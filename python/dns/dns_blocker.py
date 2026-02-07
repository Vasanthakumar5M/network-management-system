"""
DNS Blocker
Blocks DNS queries for specified domains by responding with NXDOMAIN or redirect
"""

import json
import threading
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from scapy.all import (
    sniff, send, IP, UDP, DNS, DNSQR, DNSRR, Ether,
    conf, get_if_addr
)


@dataclass
class BlockedQuery:
    """Record of a blocked DNS query"""
    timestamp: str
    device_ip: str
    domain: str
    action: str  # 'nxdomain', 'redirect', 'drop'


class DNSBlocker:
    """
    DNS Query Blocker
    Intercepts and blocks DNS queries for specified domains
    """
    
    def __init__(
        self,
        interface: str,
        blocked_domains: Optional[List[str]] = None,
        redirect_ip: str = "0.0.0.0",
        block_mode: str = "nxdomain"  # 'nxdomain', 'redirect', 'drop'
    ):
        """
        Initialize DNS blocker
        
        Args:
            interface: Network interface
            blocked_domains: List of domains to block
            redirect_ip: IP to redirect to (if mode is 'redirect')
            block_mode: How to block - 'nxdomain', 'redirect', or 'drop'
        """
        self.interface = interface
        self.blocked_domains: Set[str] = set(d.lower() for d in (blocked_domains or []))
        self.redirect_ip = redirect_ip
        self.block_mode = block_mode
        self.running = False
        self.blocked_count = 0
        self.blocked_log: List[BlockedQuery] = []
        self.local_ip = get_if_addr(interface)
        
        conf.verb = 0
    
    def is_blocked(self, domain: str) -> bool:
        """Check if domain should be blocked"""
        domain = domain.lower().rstrip('.')
        
        # Exact match
        if domain in self.blocked_domains:
            return True
        
        # Subdomain match
        for blocked in self.blocked_domains:
            if domain.endswith('.' + blocked):
                return True
            if blocked.startswith('*.') and domain.endswith(blocked[1:]):
                return True
        
        return False
    
    def _create_nxdomain_response(self, packet) -> Optional[bytes]:
        """Create NXDOMAIN response for blocked domain"""
        try:
            response = (
                IP(dst=packet[IP].src, src=packet[IP].dst) /
                UDP(dport=packet[UDP].sport, sport=53) /
                DNS(
                    id=packet[DNS].id,
                    qr=1,  # Response
                    aa=1,  # Authoritative
                    rcode=3,  # NXDOMAIN
                    qd=packet[DNS].qd
                )
            )
            return response
        except Exception:
            return None
    
    def _create_redirect_response(self, packet) -> Optional[bytes]:
        """Create redirect response for blocked domain"""
        try:
            response = (
                IP(dst=packet[IP].src, src=packet[IP].dst) /
                UDP(dport=packet[UDP].sport, sport=53) /
                DNS(
                    id=packet[DNS].id,
                    qr=1,
                    aa=1,
                    rcode=0,
                    qd=packet[DNS].qd,
                    an=DNSRR(
                        rrname=packet[DNS].qd.qname,
                        type='A',
                        ttl=300,
                        rdata=self.redirect_ip
                    )
                )
            )
            return response
        except Exception:
            return None
    
    def _process_packet(self, packet):
        """Process DNS packet and block if necessary"""
        try:
            if not packet.haslayer(DNS):
                return
            
            dns = packet[DNS]
            
            # Only process queries (not responses)
            if dns.qr != 0 or not dns.qd:
                return
            
            # Get query domain
            domain = dns.qd.qname.decode() if isinstance(dns.qd.qname, bytes) else str(dns.qd.qname)
            domain = domain.rstrip('.')
            
            # Check if blocked
            if not self.is_blocked(domain):
                return
            
            # Log blocked query
            self.blocked_count += 1
            blocked_query = BlockedQuery(
                timestamp=datetime.now().isoformat(),
                device_ip=packet[IP].src,
                domain=domain,
                action=self.block_mode
            )
            self.blocked_log.append(blocked_query)
            
            # Output blocked query
            print(json.dumps({
                "type": "blocked",
                "timestamp": blocked_query.timestamp,
                "device_ip": blocked_query.device_ip,
                "domain": blocked_query.domain,
                "action": blocked_query.action
            }), flush=True)
            
            # Send response based on mode
            if self.block_mode == "nxdomain":
                response = self._create_nxdomain_response(packet)
                if response:
                    send(response, iface=self.interface, verbose=False)
                    
            elif self.block_mode == "redirect":
                response = self._create_redirect_response(packet)
                if response:
                    send(response, iface=self.interface, verbose=False)
            
            # 'drop' mode - just don't forward (handled by ARP gateway)
            
        except Exception as e:
            print(json.dumps({"error": str(e), "type": "blocker_error"}), flush=True)
    
    def start(self):
        """Start DNS blocker"""
        self.running = True
        
        def capture_loop():
            sniff(
                iface=self.interface,
                filter="udp port 53",
                prn=self._process_packet,
                store=False,
                stop_filter=lambda x: not self.running
            )
        
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()
        
        print(json.dumps({
            "status": "started",
            "type": "dns_blocker",
            "interface": self.interface,
            "blocked_domains": len(self.blocked_domains),
            "mode": self.block_mode
        }), flush=True)
    
    def stop(self):
        """Stop DNS blocker"""
        self.running = False
        print(json.dumps({
            "status": "stopped",
            "blocked_count": self.blocked_count
        }), flush=True)
    
    def add_domain(self, domain: str):
        """Add domain to blocklist"""
        self.blocked_domains.add(domain.lower())
        print(json.dumps({
            "action": "domain_added",
            "domain": domain
        }), flush=True)
    
    def remove_domain(self, domain: str):
        """Remove domain from blocklist"""
        self.blocked_domains.discard(domain.lower())
        print(json.dumps({
            "action": "domain_removed", 
            "domain": domain
        }), flush=True)
    
    def get_blocked_log(self) -> List[Dict]:
        """Get log of blocked queries"""
        return [
            {
                "timestamp": b.timestamp,
                "device_ip": b.device_ip,
                "domain": b.domain,
                "action": b.action
            }
            for b in self.blocked_log
        ]


# CLI interface
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="DNS Blocker")
    parser.add_argument("--interface", "-i", required=True, help="Network interface")
    parser.add_argument("--domains", "-d", nargs="*", default=[], help="Domains to block")
    parser.add_argument("--mode", "-m", choices=["nxdomain", "redirect", "drop"], default="nxdomain")
    parser.add_argument("--redirect-ip", "-r", default="0.0.0.0", help="Redirect IP (for redirect mode)")
    
    args = parser.parse_args()
    
    blocker = DNSBlocker(
        interface=args.interface,
        blocked_domains=args.domains,
        redirect_ip=args.redirect_ip,
        block_mode=args.mode
    )
    
    try:
        blocker.start()
        
        while blocker.running:
            try:
                line = sys.stdin.readline().strip()
                if line:
                    cmd = json.loads(line)
                    if cmd.get("action") == "stop":
                        break
                    elif cmd.get("action") == "add":
                        blocker.add_domain(cmd["domain"])
                    elif cmd.get("action") == "remove":
                        blocker.remove_domain(cmd["domain"])
            except (json.JSONDecodeError, EOFError):
                pass
                
    except KeyboardInterrupt:
        pass
    finally:
        blocker.stop()
