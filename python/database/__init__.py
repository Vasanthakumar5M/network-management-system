"""
Database Module for Network Monitor.

Provides persistent storage using SQLite:
- Traffic logging
- DNS query history
- Device tracking
- Full-text search
"""

from .db_manager import DatabaseManager
from .models import (
    Device,
    DeviceType,
    DNSQuery,
    Protocol,
    SessionStats,
    TrafficDirection,
    TrafficEntry,
)
from .search import (
    SearchEngine,
    SearchQuery,
    SearchResult,
)

__all__ = [
    # Database Manager
    "DatabaseManager",
    # Models
    "Device",
    "DeviceType",
    "DNSQuery",
    "TrafficEntry",
    "TrafficDirection",
    "Protocol",
    "SessionStats",
    # Search
    "SearchEngine",
    "SearchQuery",
    "SearchResult",
]
