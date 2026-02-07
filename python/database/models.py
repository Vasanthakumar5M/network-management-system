"""
Data Models for Network Monitor.

Defines the data structures for storing:
- Traffic entries
- DNS queries
- Devices
- Alerts
- Configuration
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DeviceType(Enum):
    """Types of network devices."""
    UNKNOWN = "unknown"
    PHONE = "phone"
    TABLET = "tablet"
    COMPUTER = "computer"
    SMART_TV = "smart_tv"
    GAMING_CONSOLE = "gaming_console"
    IOT = "iot"
    ROUTER = "router"


class TrafficDirection(Enum):
    """Direction of network traffic."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Protocol(Enum):
    """Network protocols."""
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    TCP = "tcp"
    UDP = "udp"
    OTHER = "other"


@dataclass
class Device:
    """A device on the network."""
    id: str
    mac_address: str
    ip_address: str
    hostname: Optional[str] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    manufacturer: Optional[str] = None
    nickname: Optional[str] = None  # User-defined name
    
    # Monitoring settings
    is_monitored: bool = True
    has_certificate: bool = False
    
    # Stats
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    total_requests: int = 0
    total_bytes: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "device_type": self.device_type.value,
            "manufacturer": self.manufacturer,
            "nickname": self.nickname,
            "is_monitored": self.is_monitored,
            "has_certificate": self.has_certificate,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "total_requests": self.total_requests,
            "total_bytes": self.total_bytes,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            mac_address=data["mac_address"],
            ip_address=data["ip_address"],
            hostname=data.get("hostname"),
            device_type=DeviceType(data.get("device_type", "unknown")),
            manufacturer=data.get("manufacturer"),
            nickname=data.get("nickname"),
            is_monitored=data.get("is_monitored", True),
            has_certificate=data.get("has_certificate", False),
            first_seen=data.get("first_seen"),
            last_seen=data.get("last_seen"),
            total_requests=data.get("total_requests", 0),
            total_bytes=data.get("total_bytes", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class DNSQuery:
    """A DNS query from a device."""
    id: str
    timestamp: str
    device_id: str
    device_ip: str
    
    # Query details
    query_name: str  # Domain queried
    query_type: str  # A, AAAA, CNAME, etc.
    
    # Response
    response_ip: Optional[str] = None
    response_ttl: Optional[int] = None
    
    # Status
    blocked: bool = False
    block_reason: Optional[str] = None
    
    # Classification
    category: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "device_ip": self.device_ip,
            "query_name": self.query_name,
            "query_type": self.query_type,
            "response_ip": self.response_ip,
            "response_ttl": self.response_ttl,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "category": self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DNSQuery":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            device_id=data["device_id"],
            device_ip=data["device_ip"],
            query_name=data["query_name"],
            query_type=data["query_type"],
            response_ip=data.get("response_ip"),
            response_ttl=data.get("response_ttl"),
            blocked=data.get("blocked", False),
            block_reason=data.get("block_reason"),
            category=data.get("category")
        )


@dataclass
class TrafficEntry:
    """A single HTTP/HTTPS traffic entry."""
    id: str
    timestamp: str
    device_id: str
    device_ip: str
    
    # Request details
    method: str
    url: str
    host: str
    path: str
    protocol: Protocol = Protocol.HTTPS
    
    # Request body
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[str] = None
    request_body_type: Optional[str] = None
    request_size: int = 0
    
    # Response details
    status_code: Optional[int] = None
    status_message: Optional[str] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[str] = None
    response_body_type: Optional[str] = None
    response_size: int = 0
    
    # Timing
    duration_ms: int = 0
    
    # Classification
    category: Optional[str] = None
    sensitivity: Optional[str] = None
    
    # Status
    blocked: bool = False
    block_reason: Optional[str] = None
    intercepted: bool = True
    
    # Alerts
    alerts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "device_ip": self.device_ip,
            "method": self.method,
            "url": self.url,
            "host": self.host,
            "path": self.path,
            "protocol": self.protocol.value,
            "request_headers": self.request_headers,
            "request_body": self.request_body,
            "request_body_type": self.request_body_type,
            "request_size": self.request_size,
            "status_code": self.status_code,
            "status_message": self.status_message,
            "response_headers": self.response_headers,
            "response_body": self.response_body,
            "response_body_type": self.response_body_type,
            "response_size": self.response_size,
            "duration_ms": self.duration_ms,
            "category": self.category,
            "sensitivity": self.sensitivity,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "intercepted": self.intercepted,
            "alerts": self.alerts
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TrafficEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            device_id=data["device_id"],
            device_ip=data["device_ip"],
            method=data["method"],
            url=data["url"],
            host=data["host"],
            path=data["path"],
            protocol=Protocol(data.get("protocol", "https")),
            request_headers=data.get("request_headers", {}),
            request_body=data.get("request_body"),
            request_body_type=data.get("request_body_type"),
            request_size=data.get("request_size", 0),
            status_code=data.get("status_code"),
            status_message=data.get("status_message"),
            response_headers=data.get("response_headers", {}),
            response_body=data.get("response_body"),
            response_body_type=data.get("response_body_type"),
            response_size=data.get("response_size", 0),
            duration_ms=data.get("duration_ms", 0),
            category=data.get("category"),
            sensitivity=data.get("sensitivity"),
            blocked=data.get("blocked", False),
            block_reason=data.get("block_reason"),
            intercepted=data.get("intercepted", True),
            alerts=data.get("alerts", [])
        )


@dataclass
class SessionStats:
    """Statistics for a monitoring session."""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    
    # Counts
    total_requests: int = 0
    total_bytes_in: int = 0
    total_bytes_out: int = 0
    blocked_count: int = 0
    alert_count: int = 0
    
    # Device counts
    devices_seen: int = 0
    
    # Top sites
    top_domains: Dict[str, int] = field(default_factory=dict)
    top_categories: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_requests": self.total_requests,
            "total_bytes_in": self.total_bytes_in,
            "total_bytes_out": self.total_bytes_out,
            "blocked_count": self.blocked_count,
            "alert_count": self.alert_count,
            "devices_seen": self.devices_seen,
            "top_domains": self.top_domains,
            "top_categories": self.top_categories
        }
