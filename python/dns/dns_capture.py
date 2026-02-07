"""
DNS Packet Capture
Captures all DNS queries from devices on the network
Works without any installation on target devices
"""

import json
import sys
import threading
from datetime import datetime
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass, asdict

from scapy.all import sniff, DNS, DNSQR, DNSRR, IP, UDP, Ether, conf


@dataclass
class DNSQuery:
    """Represents a captured DNS query"""
    id: int
    timestamp: str
    device_ip: str
    device_mac: str
    query_name: str
    query_type: str
    response_ip: Optional[str] = None
    is_response: bool = False
    ttl: Optional[int] = None
    blocked: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class DNSCapture:
    """
    DNS Query Capture Engine
    Captures all DNS queries passing through the network
    """
    
    # DNS query type mapping
    QUERY_TYPES = {
        1: "A",
        2: "NS",
        5: "CNAME",
        6: "SOA",
        12: "PTR",
        15: "MX",
        16: "TXT",
        28: "AAAA",
        33: "SRV",
        255: "ANY"
    }
    
    def __init__(
        self,
        interface: str,
        callback: Optional[Callable[[DNSQuery], None]] = None,
        blocklist: Optional[List[str]] = None
    ):
        """
        Initialize DNS capture
        
        Args:
            interface: Network interface to capture on
            callback: Function to call for each DNS query
            blocklist: List of domains to mark as blocked
        """
        self.interface = interface
        self.callback = callback or self._default_callback
        self.blocklist = set(blocklist or [])
        self.running = False
        self.query_count = 0
        self.capture_thread: Optional[threading.Thread] = None
        
        # Disable Scapy verbosity
        conf.verb = 0
    
    def _default_callback(self, query: DNSQuery):
        """Default callback - print to stdout as JSON"""
        print(query.to_json(), flush=True)
    
    def _get_query_type(self, qtype: int) -> str:
        """Convert query type number to string"""
        return self.QUERY_TYPES.get(qtype, f"TYPE{qtype}")
    
    def _is_blocked(self, domain: str) -> bool:
        """Check if domain matches blocklist"""
        domain_lower = domain.lower().rstrip('.')
        
        for blocked in self.blocklist:
            blocked_lower = blocked.lower()
            if domain_lower == blocked_lower:
                return True
            if domain_lower.endswith('.' + blocked_lower):
                return True
            if '*' in blocked_lower:
                # Simple wildcard matching
                pattern = blocked_lower.replace('*', '')
                if pattern in domain_lower:
                    return True
        
        return False
    
    def _process_packet(self, packet):
        """Process a captured DNS packet"""
        try:
            if not packet.haslayer(DNS):
                return
            
            dns = packet[DNS]
            
            # Get source info
            device_ip = packet[IP].src if packet.haslayer(IP) else "unknown"
            device_mac = packet[Ether].src if packet.haslayer(Ether) else "unknown"
            
            # DNS Query (QR=0)
            if dns.qr == 0 and dns.qd:
                self.query_count += 1
                
                query_name = dns.qd.qname.decode() if isinstance(dns.qd.qname, bytes) else str(dns.qd.qname)
                query_name = query_name.rstrip('.')
                
                query = DNSQuery(
                    id=self.query_count,
                    timestamp=datetime.now().isoformat(),
                    device_ip=device_ip,
                    device_mac=device_mac.upper(),
                    query_name=query_name,
                    query_type=self._get_query_type(dns.qd.qtype),
                    is_response=False,
                    blocked=self._is_blocked(query_name)
                )
                
                self.callback(query)
            
            # DNS Response (QR=1)
            elif dns.qr == 1 and dns.an:
                self.query_count += 1
                
                query_name = dns.qd.qname.decode() if dns.qd and isinstance(dns.qd.qname, bytes) else "unknown"
                query_name = query_name.rstrip('.')
                
                # Get response IP if A record
                response_ip = None
                ttl = None
                
                for i in range(dns.ancount):
                    try:
                        rr = dns.an[i]
                        if rr.type == 1:  # A record
                            response_ip = rr.rdata
                            ttl = rr.ttl
                            break
                    except Exception:
                        pass
                
                query = DNSQuery(
                    id=self.query_count,
                    timestamp=datetime.now().isoformat(),
                    device_ip=device_ip,
                    device_mac=device_mac.upper(),
                    query_name=query_name,
                    query_type=self._get_query_type(dns.qd.qtype) if dns.qd else "RESPONSE",
                    response_ip=str(response_ip) if response_ip else None,
                    is_response=True,
                    ttl=ttl,
                    blocked=self._is_blocked(query_name)
                )
                
                self.callback(query)
                
        except Exception as e:
            # Log error but continue capturing
            error_msg = json.dumps({"error": str(e), "type": "dns_parse_error"})
            print(error_msg, file=sys.stderr, flush=True)
    
    def start(self):
        """Start capturing DNS queries"""
        self.running = True
        
        def capture_loop():
            try:
                sniff(
                    iface=self.interface,
                    filter="udp port 53",
                    prn=self._process_packet,
                    store=False,
                    stop_filter=lambda x: not self.running
                )
            except Exception as e:
                error_msg = json.dumps({"error": str(e), "type": "capture_error"})
                print(error_msg, file=sys.stderr, flush=True)
        
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Send start message
        start_msg = json.dumps({
            "status": "started",
            "interface": self.interface,
            "type": "dns_capture"
        })
        print(start_msg, flush=True)
    
    def stop(self):
        """Stop capturing"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        stop_msg = json.dumps({
            "status": "stopped",
            "total_queries": self.query_count
        })
        print(stop_msg, flush=True)
    
    def add_to_blocklist(self, domain: str):
        """Add domain to blocklist"""
        self.blocklist.add(domain.lower())
    
    def remove_from_blocklist(self, domain: str):
        """Remove domain from blocklist"""
        self.blocklist.discard(domain.lower())
    
    def set_blocklist(self, domains: List[str]):
        """Set entire blocklist"""
        self.blocklist = set(d.lower() for d in domains)


def start_dns_capture(
    interface: str,
    callback: Optional[Callable[[DNSQuery], None]] = None,
    blocklist: Optional[List[str]] = None
) -> DNSCapture:
    """
    Quick function to start DNS capture
    
    Args:
        interface: Network interface
        callback: Callback function for queries
        blocklist: Blocked domains
        
    Returns:
        DNSCapture instance
    """
    capture = DNSCapture(interface, callback, blocklist)
    capture.start()
    return capture


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DNS Capture")
    parser.add_argument("--interface", "-i", required=True, help="Network interface")
    parser.add_argument("--blocklist", "-b", nargs="*", default=[], help="Blocked domains")
    
    args = parser.parse_args()
    
    capture = DNSCapture(args.interface, blocklist=args.blocklist)
    
    try:
        capture.start()
        
        # Keep main thread alive and handle stdin commands
        while capture.running:
            try:
                line = sys.stdin.readline().strip()
                if line:
                    cmd = json.loads(line)
                    if cmd.get("action") == "stop":
                        break
                    elif cmd.get("action") == "block":
                        capture.add_to_blocklist(cmd["domain"])
                    elif cmd.get("action") == "unblock":
                        capture.remove_from_blocklist(cmd["domain"])
            except json.JSONDecodeError:
                pass
            except EOFError:
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        capture.stop()
