"""
DNS Parser Module

Parses DNS packets and extracts query/response information.
Supports various DNS record types (A, AAAA, CNAME, MX, TXT, etc.)
"""

import struct
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Optional


class DNSRecordType(IntEnum):
    """DNS record types."""
    A = 1
    NS = 2
    CNAME = 5
    SOA = 6
    PTR = 12
    MX = 15
    TXT = 16
    AAAA = 28
    SRV = 33
    ANY = 255
    
    @classmethod
    def to_string(cls, value: int) -> str:
        """Convert record type to string."""
        try:
            return cls(value).name
        except ValueError:
            return f"TYPE{value}"


class DNSResponseCode(IntEnum):
    """DNS response codes."""
    NOERROR = 0
    FORMERR = 1
    SERVFAIL = 2
    NXDOMAIN = 3
    NOTIMP = 4
    REFUSED = 5
    
    @classmethod
    def to_string(cls, value: int) -> str:
        """Convert response code to string."""
        try:
            return cls(value).name
        except ValueError:
            return f"RCODE{value}"


@dataclass
class DNSQuestion:
    """Represents a DNS question."""
    name: str
    qtype: int
    qclass: int
    
    @property
    def type_str(self) -> str:
        return DNSRecordType.to_string(self.qtype)


@dataclass
class DNSRecord:
    """Represents a DNS resource record."""
    name: str
    rtype: int
    rclass: int
    ttl: int
    rdata: str
    
    @property
    def type_str(self) -> str:
        return DNSRecordType.to_string(self.rtype)


@dataclass
class DNSPacket:
    """Represents a parsed DNS packet."""
    transaction_id: int
    is_response: bool
    opcode: int
    authoritative: bool
    truncated: bool
    recursion_desired: bool
    recursion_available: bool
    response_code: int
    questions: list[DNSQuestion]
    answers: list[DNSRecord]
    authority: list[DNSRecord]
    additional: list[DNSRecord]
    timestamp: datetime
    source_ip: Optional[str] = None
    source_mac: Optional[str] = None
    dest_ip: Optional[str] = None
    
    @property
    def response_code_str(self) -> str:
        return DNSResponseCode.to_string(self.response_code)
    
    @property
    def query_domain(self) -> Optional[str]:
        """Get the primary queried domain."""
        if self.questions:
            return self.questions[0].name
        return None
    
    @property
    def query_type(self) -> Optional[str]:
        """Get the primary query type."""
        if self.questions:
            return self.questions[0].type_str
        return None
    
    @property
    def resolved_ips(self) -> list[str]:
        """Get resolved IP addresses from A/AAAA records."""
        ips = []
        for answer in self.answers:
            if answer.rtype in (DNSRecordType.A, DNSRecordType.AAAA):
                ips.append(answer.rdata)
        return ips
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "transaction_id": self.transaction_id,
            "is_response": self.is_response,
            "opcode": self.opcode,
            "authoritative": self.authoritative,
            "truncated": self.truncated,
            "recursion_desired": self.recursion_desired,
            "recursion_available": self.recursion_available,
            "response_code": self.response_code,
            "response_code_str": self.response_code_str,
            "questions": [
                {"name": q.name, "type": q.type_str, "class": q.qclass}
                for q in self.questions
            ],
            "answers": [
                {"name": r.name, "type": r.type_str, "ttl": r.ttl, "data": r.rdata}
                for r in self.answers
            ],
            "authority_count": len(self.authority),
            "additional_count": len(self.additional),
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "source_mac": self.source_mac,
            "dest_ip": self.dest_ip,
            "query_domain": self.query_domain,
            "query_type": self.query_type,
            "resolved_ips": self.resolved_ips
        }


class DNSParser:
    """Parses raw DNS packets."""
    
    def __init__(self):
        """Initialize the DNS parser."""
        pass
    
    def parse(
        self,
        data: bytes,
        source_ip: Optional[str] = None,
        source_mac: Optional[str] = None,
        dest_ip: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> Optional[DNSPacket]:
        """Parse a raw DNS packet.
        
        Args:
            data: Raw DNS packet bytes (UDP payload)
            source_ip: Source IP address
            source_mac: Source MAC address
            dest_ip: Destination IP address
            timestamp: Packet timestamp
            
        Returns:
            Parsed DNSPacket or None if parsing fails
        """
        if len(data) < 12:
            return None
            
        try:
            # Parse header
            transaction_id, flags, qcount, ancount, nscount, arcount = struct.unpack(
                "!HHHHHH", data[:12]
            )
            
            # Parse flags
            is_response = bool(flags & 0x8000)
            opcode = (flags >> 11) & 0x0F
            authoritative = bool(flags & 0x0400)
            truncated = bool(flags & 0x0200)
            recursion_desired = bool(flags & 0x0100)
            recursion_available = bool(flags & 0x0080)
            response_code = flags & 0x000F
            
            offset = 12
            
            # Parse questions
            questions = []
            for _ in range(qcount):
                name, offset = self._parse_name(data, offset)
                if offset + 4 > len(data):
                    break
                qtype, qclass = struct.unpack("!HH", data[offset:offset + 4])
                offset += 4
                questions.append(DNSQuestion(name, qtype, qclass))
                
            # Parse answers
            answers = []
            for _ in range(ancount):
                record, offset = self._parse_record(data, offset)
                if record:
                    answers.append(record)
                    
            # Parse authority
            authority = []
            for _ in range(nscount):
                record, offset = self._parse_record(data, offset)
                if record:
                    authority.append(record)
                    
            # Parse additional
            additional = []
            for _ in range(arcount):
                record, offset = self._parse_record(data, offset)
                if record:
                    additional.append(record)
                    
            return DNSPacket(
                transaction_id=transaction_id,
                is_response=is_response,
                opcode=opcode,
                authoritative=authoritative,
                truncated=truncated,
                recursion_desired=recursion_desired,
                recursion_available=recursion_available,
                response_code=response_code,
                questions=questions,
                answers=answers,
                authority=authority,
                additional=additional,
                timestamp=timestamp or datetime.now(),
                source_ip=source_ip,
                source_mac=source_mac,
                dest_ip=dest_ip
            )
            
        except Exception:
            return None
    
    def _parse_name(self, data: bytes, offset: int) -> tuple[str, int]:
        """Parse a DNS domain name with compression support.
        
        Args:
            data: Packet data
            offset: Starting offset
            
        Returns:
            Tuple of (domain_name, new_offset)
        """
        labels = []
        original_offset = offset
        jumped = False
        
        while offset < len(data):
            length = data[offset]
            
            if length == 0:
                offset += 1
                break
                
            # Check for compression pointer
            if (length & 0xC0) == 0xC0:
                if offset + 1 >= len(data):
                    break
                pointer = ((length & 0x3F) << 8) | data[offset + 1]
                if not jumped:
                    original_offset = offset + 2
                jumped = True
                offset = pointer
                continue
                
            # Regular label
            offset += 1
            if offset + length > len(data):
                break
            labels.append(data[offset:offset + length].decode("utf-8", errors="ignore"))
            offset += length
            
        if jumped:
            offset = original_offset
            
        return ".".join(labels), offset
    
    def _parse_record(self, data: bytes, offset: int) -> tuple[Optional[DNSRecord], int]:
        """Parse a DNS resource record.
        
        Args:
            data: Packet data
            offset: Starting offset
            
        Returns:
            Tuple of (DNSRecord or None, new_offset)
        """
        if offset >= len(data):
            return None, offset
            
        try:
            name, offset = self._parse_name(data, offset)
            
            if offset + 10 > len(data):
                return None, offset
                
            rtype, rclass, ttl, rdlength = struct.unpack(
                "!HHIH", data[offset:offset + 10]
            )
            offset += 10
            
            if offset + rdlength > len(data):
                return None, offset
                
            rdata = self._parse_rdata(data, offset, rtype, rdlength)
            offset += rdlength
            
            return DNSRecord(name, rtype, rclass, ttl, rdata), offset
            
        except Exception:
            return None, offset
    
    def _parse_rdata(self, data: bytes, offset: int, rtype: int, rdlength: int) -> str:
        """Parse record data based on type.
        
        Args:
            data: Packet data
            offset: RDATA offset
            rtype: Record type
            rdlength: RDATA length
            
        Returns:
            Parsed RDATA as string
        """
        try:
            if rtype == DNSRecordType.A and rdlength == 4:
                # IPv4 address
                return ".".join(str(b) for b in data[offset:offset + 4])
                
            elif rtype == DNSRecordType.AAAA and rdlength == 16:
                # IPv6 address
                parts = struct.unpack("!8H", data[offset:offset + 16])
                return ":".join(f"{p:x}" for p in parts)
                
            elif rtype in (DNSRecordType.CNAME, DNSRecordType.NS, DNSRecordType.PTR):
                # Domain name
                name, _ = self._parse_name(data, offset)
                return name
                
            elif rtype == DNSRecordType.MX:
                # Mail exchange
                if rdlength >= 2:
                    preference = struct.unpack("!H", data[offset:offset + 2])[0]
                    name, _ = self._parse_name(data, offset + 2)
                    return f"{preference} {name}"
                return ""
                
            elif rtype == DNSRecordType.TXT:
                # Text record
                texts = []
                pos = offset
                end = offset + rdlength
                while pos < end:
                    txt_len = data[pos]
                    pos += 1
                    if pos + txt_len <= end:
                        texts.append(
                            data[pos:pos + txt_len].decode("utf-8", errors="ignore")
                        )
                        pos += txt_len
                return " ".join(texts)
                
            elif rtype == DNSRecordType.SOA:
                # SOA record
                mname, pos = self._parse_name(data, offset)
                rname, pos = self._parse_name(data, pos)
                if pos + 20 <= offset + rdlength:
                    serial, refresh, retry, expire, minimum = struct.unpack(
                        "!IIIII", data[pos:pos + 20]
                    )
                    return f"{mname} {rname} {serial}"
                return f"{mname} {rname}"
                
            else:
                # Unknown type - return hex
                return data[offset:offset + rdlength].hex()
                
        except Exception:
            return data[offset:offset + rdlength].hex()


def parse_dns_from_scapy(packet) -> Optional[dict]:
    """Parse DNS from a Scapy packet.
    
    Args:
        packet: Scapy packet with DNS layer
        
    Returns:
        Dictionary with parsed DNS data
    """
    try:
        from scapy.all import DNS, DNSQR, DNSRR, IP, Ether
        
        if not packet.haslayer(DNS):
            return None
            
        dns = packet[DNS]
        
        # Extract source info
        source_ip = packet[IP].src if packet.haslayer(IP) else None
        dest_ip = packet[IP].dst if packet.haslayer(IP) else None
        source_mac = packet[Ether].src if packet.haslayer(Ether) else None
        
        # Parse questions
        questions = []
        if dns.qdcount and dns.qd:
            for i in range(dns.qdcount):
                try:
                    qr = dns.qd[i] if hasattr(dns.qd, "__getitem__") else dns.qd
                    questions.append({
                        "name": qr.qname.decode() if isinstance(qr.qname, bytes) else str(qr.qname),
                        "type": DNSRecordType.to_string(qr.qtype),
                        "class": qr.qclass
                    })
                except (IndexError, AttributeError):
                    break
                    
        # Parse answers
        answers = []
        resolved_ips = []
        if dns.ancount and dns.an:
            for i in range(dns.ancount):
                try:
                    rr = dns.an[i] if hasattr(dns.an, "__getitem__") else dns.an
                    rdata = str(rr.rdata) if hasattr(rr, "rdata") else ""
                    
                    if rr.type in (1, 28):  # A or AAAA
                        resolved_ips.append(rdata)
                        
                    answers.append({
                        "name": rr.rrname.decode() if isinstance(rr.rrname, bytes) else str(rr.rrname),
                        "type": DNSRecordType.to_string(rr.type),
                        "ttl": rr.ttl,
                        "data": rdata
                    })
                except (IndexError, AttributeError):
                    break
        
        # Get primary query
        query_domain = None
        query_type = None
        if questions:
            query_domain = questions[0]["name"].rstrip(".")
            query_type = questions[0]["type"]
            
        return {
            "timestamp": datetime.now().isoformat(),
            "transaction_id": dns.id,
            "is_response": bool(dns.qr),
            "opcode": dns.opcode,
            "response_code": dns.rcode,
            "response_code_str": DNSResponseCode.to_string(dns.rcode),
            "questions": questions,
            "answers": answers,
            "source_ip": source_ip,
            "source_mac": source_mac,
            "dest_ip": dest_ip,
            "query_domain": query_domain,
            "query_type": query_type,
            "resolved_ips": resolved_ips,
            "is_blocked": False
        }
        
    except Exception as e:
        return None


# Convenience function
def parse_dns(data: bytes, **kwargs) -> Optional[DNSPacket]:
    """Parse DNS packet data.
    
    Args:
        data: Raw DNS packet bytes
        **kwargs: Additional metadata (source_ip, source_mac, etc.)
        
    Returns:
        Parsed DNSPacket or None
    """
    parser = DNSParser()
    return parser.parse(data, **kwargs)
