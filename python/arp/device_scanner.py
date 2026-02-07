"""
Network Device Scanner
Discovers all devices on the local network
"""

import json
import socket
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from scapy.all import ARP, Ether, srp, conf
import psutil


@dataclass
class NetworkDevice:
    """Represents a device on the network"""
    ip: str
    mac: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    is_gateway: bool = False
    is_self: bool = False
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DeviceScanner:
    """Scans the local network for devices using ARP"""
    
    def __init__(self, interface: str):
        self.interface = interface
        self.devices: Dict[str, NetworkDevice] = {}
        self.local_ip = self._get_local_ip()
        self.local_mac = self._get_local_mac()
        self.gateway_ip = self._get_gateway_ip()
        
        conf.verb = 0
    
    def _get_local_ip(self) -> Optional[str]:
        """Get local IP for interface"""
        addrs = psutil.net_if_addrs()
        if self.interface in addrs:
            for addr in addrs[self.interface]:
                if addr.family.name == 'AF_INET':
                    return addr.address
        return None
    
    def _get_local_mac(self) -> Optional[str]:
        """Get local MAC for interface"""
        addrs = psutil.net_if_addrs()
        if self.interface in addrs:
            for addr in addrs[self.interface]:
                if addr.family.name == 'AF_LINK':
                    return addr.address.upper()
        return None
    
    def _get_gateway_ip(self) -> Optional[str]:
        """Get default gateway IP"""
        try:
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
    
    def _get_hostname(self, ip: str) -> Optional[str]:
        """Try to resolve hostname for IP"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except Exception:
            return None
    
    def _get_vendor(self, mac: str) -> Optional[str]:
        """Get vendor name from MAC address OUI"""
        # Common vendor prefixes (abbreviated list)
        oui_map = {
            "00:1A:2B": "HP",
            "00:1E:A6": "Samsung",
            "F4:F5:D8": "Google",
            "FC:A1:83": "Amazon",
            "40:CB:C0": "Apple",
            "00:17:88": "Philips",
            "34:3E:A4": "Ring",
            "84:EA:ED": "Roku",
            "B8:27:EB": "Raspberry Pi",
            "DC:A6:32": "Raspberry Pi",
            "00:50:56": "VMware",
            "08:00:27": "VirtualBox",
            "00:0C:29": "VMware",
            "AC:DE:48": "Intel",
            "3C:22:FB": "Apple",
            "F0:18:98": "Apple",
            "A4:83:E7": "Apple",
        }
        
        mac_prefix = mac[:8].upper()
        return oui_map.get(mac_prefix)
    
    def scan(self, timeout: int = 3) -> List[NetworkDevice]:
        """
        Scan network for devices
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            List of discovered devices
        """
        if not self.local_ip:
            return []
        
        # Calculate network range (assume /24)
        parts = self.local_ip.split('.')
        parts[3] = '0'
        network = '.'.join(parts) + '/24'
        
        # Create ARP request
        arp = ARP(pdst=network)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        
        # Send and receive
        try:
            result = srp(packet, timeout=timeout, iface=self.interface, verbose=False)[0]
        except Exception as e:
            print(json.dumps({"error": str(e), "type": "scan_error"}), flush=True)
            return []
        
        now = datetime.now().isoformat()
        discovered = []
        
        for sent, received in result:
            ip = received.psrc
            mac = received.hwsrc.upper()
            
            # Check if we've seen this device before
            if ip in self.devices:
                device = self.devices[ip]
                device.last_seen = now
            else:
                device = NetworkDevice(
                    ip=ip,
                    mac=mac,
                    hostname=self._get_hostname(ip),
                    vendor=self._get_vendor(mac),
                    is_gateway=(ip == self.gateway_ip),
                    is_self=(ip == self.local_ip),
                    first_seen=now,
                    last_seen=now
                )
                self.devices[ip] = device
            
            discovered.append(device)
        
        # Sort: gateway first, self second, then by IP
        discovered.sort(key=lambda d: (
            not d.is_gateway,
            not d.is_self,
            [int(x) for x in d.ip.split('.')]
        ))
        
        return discovered
    
    def get_all_devices(self) -> List[NetworkDevice]:
        """Get all known devices"""
        return list(self.devices.values())
    
    def get_device(self, ip: str) -> Optional[NetworkDevice]:
        """Get device by IP"""
        return self.devices.get(ip)
    
    def continuous_scan(self, interval: int = 30, callback=None):
        """
        Continuously scan network
        
        Args:
            interval: Seconds between scans
            callback: Function to call with results
        """
        import time
        
        def scan_loop():
            while True:
                devices = self.scan()
                if callback:
                    callback(devices)
                else:
                    print(json.dumps({
                        "type": "scan_result",
                        "devices": [d.to_dict() for d in devices],
                        "timestamp": datetime.now().isoformat()
                    }), flush=True)
                time.sleep(interval)
        
        thread = threading.Thread(target=scan_loop, daemon=True)
        thread.start()
        return thread


def scan_network(interface: str, timeout: int = 3) -> List[Dict]:
    """
    Quick function to scan network
    
    Args:
        interface: Network interface
        timeout: Scan timeout
        
    Returns:
        List of device dictionaries
    """
    scanner = DeviceScanner(interface)
    devices = scanner.scan(timeout)
    return [d.to_dict() for d in devices]


# CLI interface
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Network Device Scanner")
    parser.add_argument("--interface", "-i", required=True, help="Network interface")
    parser.add_argument("--timeout", "-t", type=int, default=3, help="Scan timeout")
    parser.add_argument("--continuous", "-c", action="store_true", help="Continuous scanning")
    parser.add_argument("--interval", type=int, default=30, help="Scan interval (seconds)")
    
    args = parser.parse_args()
    
    scanner = DeviceScanner(args.interface)
    
    if args.continuous:
        scanner.continuous_scan(args.interval)
        
        # Keep main thread alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        devices = scanner.scan(args.timeout)
        print(json.dumps({
            "devices": [d.to_dict() for d in devices],
            "count": len(devices)
        }))
