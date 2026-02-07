"""
Database Manager for Network Monitor.

Provides SQLite-based storage for:
- Traffic entries
- DNS queries
- Devices
- Session statistics
- Full-text search
"""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from .models import (
    Device,
    DeviceType,
    DNSQuery,
    Protocol,
    SessionStats,
    TrafficEntry,
)


class DatabaseManager:
    """
    SQLite database manager for network monitoring data.
    
    Provides thread-safe database operations with connection pooling.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "database" / "network_monitor.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-local storage for connections
        self._local = threading.local()
        
        # Initialize database
        self._init_database()
    
    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
    
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Devices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    mac_address TEXT UNIQUE NOT NULL,
                    ip_address TEXT NOT NULL,
                    hostname TEXT,
                    device_type TEXT DEFAULT 'unknown',
                    manufacturer TEXT,
                    nickname TEXT,
                    is_monitored INTEGER DEFAULT 1,
                    has_certificate INTEGER DEFAULT 0,
                    first_seen TEXT,
                    last_seen TEXT,
                    total_requests INTEGER DEFAULT 0,
                    total_bytes INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # DNS queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dns_queries (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    device_id TEXT,
                    device_ip TEXT NOT NULL,
                    query_name TEXT NOT NULL,
                    query_type TEXT DEFAULT 'A',
                    response_ip TEXT,
                    response_ttl INTEGER,
                    blocked INTEGER DEFAULT 0,
                    block_reason TEXT,
                    category TEXT,
                    FOREIGN KEY (device_id) REFERENCES devices(id)
                )
            """)
            
            # Traffic entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    device_id TEXT,
                    device_ip TEXT NOT NULL,
                    method TEXT NOT NULL,
                    url TEXT NOT NULL,
                    host TEXT NOT NULL,
                    path TEXT,
                    protocol TEXT DEFAULT 'https',
                    request_headers TEXT DEFAULT '{}',
                    request_body TEXT,
                    request_body_type TEXT,
                    request_size INTEGER DEFAULT 0,
                    status_code INTEGER,
                    status_message TEXT,
                    response_headers TEXT DEFAULT '{}',
                    response_body TEXT,
                    response_body_type TEXT,
                    response_size INTEGER DEFAULT 0,
                    duration_ms INTEGER DEFAULT 0,
                    category TEXT,
                    sensitivity TEXT,
                    blocked INTEGER DEFAULT 0,
                    block_reason TEXT,
                    intercepted INTEGER DEFAULT 1,
                    alerts TEXT DEFAULT '[]',
                    FOREIGN KEY (device_id) REFERENCES devices(id)
                )
            """)
            
            # Session stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_requests INTEGER DEFAULT 0,
                    total_bytes_in INTEGER DEFAULT 0,
                    total_bytes_out INTEGER DEFAULT 0,
                    blocked_count INTEGER DEFAULT 0,
                    alert_count INTEGER DEFAULT 0,
                    devices_seen INTEGER DEFAULT 0,
                    top_domains TEXT DEFAULT '{}',
                    top_categories TEXT DEFAULT '{}'
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dns_timestamp ON dns_queries(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dns_device ON dns_queries(device_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dns_domain ON dns_queries(query_name)")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_device ON traffic(device_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_host ON traffic(host)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_category ON traffic(category)")
            
            # Create FTS table for full-text search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS traffic_fts USING fts5(
                    id UNINDEXED,
                    url,
                    host,
                    request_body,
                    response_body,
                    content='traffic',
                    content_rowid='rowid'
                )
            """)
            
            # Triggers to keep FTS in sync
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS traffic_ai AFTER INSERT ON traffic BEGIN
                    INSERT INTO traffic_fts(id, url, host, request_body, response_body)
                    VALUES (new.id, new.url, new.host, new.request_body, new.response_body);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS traffic_ad AFTER DELETE ON traffic BEGIN
                    INSERT INTO traffic_fts(traffic_fts, id, url, host, request_body, response_body)
                    VALUES ('delete', old.id, old.url, old.host, old.request_body, old.response_body);
                END
            """)
            
            conn.commit()
    
    # Device operations
    def add_device(self, device: Device) -> bool:
        """Add or update a device."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO devices (
                    id, mac_address, ip_address, hostname, device_type,
                    manufacturer, nickname, is_monitored, has_certificate,
                    first_seen, last_seen, total_requests, total_bytes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device.id, device.mac_address, device.ip_address, device.hostname,
                device.device_type.value, device.manufacturer, device.nickname,
                1 if device.is_monitored else 0, 1 if device.has_certificate else 0,
                device.first_seen, device.last_seen, device.total_requests,
                device.total_bytes, json.dumps(device.metadata)
            ))
            
            conn.commit()
            return True
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_device(row)
            return None
    
    def get_device_by_mac(self, mac_address: str) -> Optional[Device]:
        """Get a device by MAC address."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices WHERE mac_address = ?", (mac_address.lower(),))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_device(row)
            return None
    
    def get_device_by_ip(self, ip_address: str) -> Optional[Device]:
        """Get a device by IP address."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM devices WHERE ip_address = ? ORDER BY last_seen DESC LIMIT 1",
                (ip_address,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_device(row)
            return None
    
    def list_devices(self, monitored_only: bool = False) -> List[Device]:
        """List all devices."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if monitored_only:
                cursor.execute("SELECT * FROM devices WHERE is_monitored = 1 ORDER BY last_seen DESC")
            else:
                cursor.execute("SELECT * FROM devices ORDER BY last_seen DESC")
            
            return [self._row_to_device(row) for row in cursor.fetchall()]
    
    def update_device_stats(
        self,
        device_id: str,
        requests: int = 0,
        bytes_transferred: int = 0
    ):
        """Update device statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE devices SET
                    total_requests = total_requests + ?,
                    total_bytes = total_bytes + ?,
                    last_seen = ?
                WHERE id = ?
            """, (requests, bytes_transferred, datetime.now().isoformat(), device_id))
            conn.commit()
    
    def _row_to_device(self, row: sqlite3.Row) -> Device:
        """Convert database row to Device."""
        return Device(
            id=row["id"],
            mac_address=row["mac_address"],
            ip_address=row["ip_address"],
            hostname=row["hostname"],
            device_type=DeviceType(row["device_type"] or "unknown"),
            manufacturer=row["manufacturer"],
            nickname=row["nickname"],
            is_monitored=bool(row["is_monitored"]),
            has_certificate=bool(row["has_certificate"]),
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            total_requests=row["total_requests"] or 0,
            total_bytes=row["total_bytes"] or 0,
            metadata=json.loads(row["metadata"] or "{}")
        )
    
    # DNS operations
    def add_dns_query(self, query: DNSQuery) -> bool:
        """Add a DNS query."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO dns_queries (
                    id, timestamp, device_id, device_ip, query_name, query_type,
                    response_ip, response_ttl, blocked, block_reason, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query.id, query.timestamp, query.device_id, query.device_ip,
                query.query_name, query.query_type, query.response_ip,
                query.response_ttl, 1 if query.blocked else 0,
                query.block_reason, query.category
            ))
            
            conn.commit()
            return True
    
    def get_dns_queries(
        self,
        device_id: Optional[str] = None,
        domain: Optional[str] = None,
        since: Optional[datetime] = None,
        blocked_only: bool = False,
        limit: int = 1000
    ) -> List[DNSQuery]:
        """Get DNS queries with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM dns_queries WHERE 1=1"
            params = []
            
            if device_id:
                query += " AND device_id = ?"
                params.append(device_id)
            
            if domain:
                query += " AND query_name LIKE ?"
                params.append(f"%{domain}%")
            
            if since:
                query += " AND timestamp > ?"
                params.append(since.isoformat())
            
            if blocked_only:
                query += " AND blocked = 1"
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [self._row_to_dns_query(row) for row in cursor.fetchall()]
    
    def _row_to_dns_query(self, row: sqlite3.Row) -> DNSQuery:
        """Convert database row to DNSQuery."""
        return DNSQuery(
            id=row["id"],
            timestamp=row["timestamp"],
            device_id=row["device_id"],
            device_ip=row["device_ip"],
            query_name=row["query_name"],
            query_type=row["query_type"],
            response_ip=row["response_ip"],
            response_ttl=row["response_ttl"],
            blocked=bool(row["blocked"]),
            block_reason=row["block_reason"],
            category=row["category"]
        )
    
    # Traffic operations
    def add_traffic_entry(self, entry: TrafficEntry) -> bool:
        """Add a traffic entry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO traffic (
                    id, timestamp, device_id, device_ip, method, url, host, path,
                    protocol, request_headers, request_body, request_body_type,
                    request_size, status_code, status_message, response_headers,
                    response_body, response_body_type, response_size, duration_ms,
                    category, sensitivity, blocked, block_reason, intercepted, alerts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.timestamp, entry.device_id, entry.device_ip,
                entry.method, entry.url, entry.host, entry.path,
                entry.protocol.value, json.dumps(entry.request_headers),
                entry.request_body, entry.request_body_type, entry.request_size,
                entry.status_code, entry.status_message,
                json.dumps(entry.response_headers), entry.response_body,
                entry.response_body_type, entry.response_size, entry.duration_ms,
                entry.category, entry.sensitivity, 1 if entry.blocked else 0,
                entry.block_reason, 1 if entry.intercepted else 0,
                json.dumps(entry.alerts)
            ))
            
            conn.commit()
            return True
    
    def get_traffic_entry(self, entry_id: str) -> Optional[TrafficEntry]:
        """Get a traffic entry by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM traffic WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_traffic_entry(row)
            return None
    
    def get_traffic(
        self,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        category: Optional[str] = None,
        since: Optional[datetime] = None,
        blocked_only: bool = False,
        has_alerts: bool = False,
        limit: int = 1000
    ) -> List[TrafficEntry]:
        """Get traffic entries with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM traffic WHERE 1=1"
            params = []
            
            if device_id:
                query += " AND device_id = ?"
                params.append(device_id)
            
            if host:
                query += " AND host LIKE ?"
                params.append(f"%{host}%")
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if since:
                query += " AND timestamp > ?"
                params.append(since.isoformat())
            
            if blocked_only:
                query += " AND blocked = 1"
            
            if has_alerts:
                query += " AND alerts != '[]'"
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [self._row_to_traffic_entry(row) for row in cursor.fetchall()]
    
    def _row_to_traffic_entry(self, row: sqlite3.Row) -> TrafficEntry:
        """Convert database row to TrafficEntry."""
        return TrafficEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            device_id=row["device_id"],
            device_ip=row["device_ip"],
            method=row["method"],
            url=row["url"],
            host=row["host"],
            path=row["path"],
            protocol=Protocol(row["protocol"] or "https"),
            request_headers=json.loads(row["request_headers"] or "{}"),
            request_body=row["request_body"],
            request_body_type=row["request_body_type"],
            request_size=row["request_size"] or 0,
            status_code=row["status_code"],
            status_message=row["status_message"],
            response_headers=json.loads(row["response_headers"] or "{}"),
            response_body=row["response_body"],
            response_body_type=row["response_body_type"],
            response_size=row["response_size"] or 0,
            duration_ms=row["duration_ms"] or 0,
            category=row["category"],
            sensitivity=row["sensitivity"],
            blocked=bool(row["blocked"]),
            block_reason=row["block_reason"],
            intercepted=bool(row["intercepted"]),
            alerts=json.loads(row["alerts"] or "[]")
        )
    
    # Full-text search
    def search(
        self,
        query: str,
        limit: int = 100
    ) -> List[TrafficEntry]:
        """
        Full-text search across traffic data.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching traffic entries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Use FTS5 search
            cursor.execute("""
                SELECT traffic.* FROM traffic
                JOIN traffic_fts ON traffic.id = traffic_fts.id
                WHERE traffic_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            
            return [self._row_to_traffic_entry(row) for row in cursor.fetchall()]
    
    # Statistics
    def get_stats(
        self,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            since_clause = ""
            params = []
            if since:
                since_clause = " WHERE timestamp > ?"
                params = [since.isoformat()]
            
            # Traffic stats
            cursor.execute(f"SELECT COUNT(*) FROM traffic{since_clause}", params)
            traffic_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT SUM(request_size), SUM(response_size) FROM traffic{since_clause}", params)
            row = cursor.fetchone()
            bytes_out = row[0] or 0
            bytes_in = row[1] or 0
            
            cursor.execute(f"SELECT COUNT(*) FROM traffic WHERE blocked = 1{' AND timestamp > ?' if since else ''}", params)
            blocked_count = cursor.fetchone()[0]
            
            # DNS stats
            cursor.execute(f"SELECT COUNT(*) FROM dns_queries{since_clause}", params)
            dns_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM dns_queries WHERE blocked = 1{' AND timestamp > ?' if since else ''}", params)
            dns_blocked = cursor.fetchone()[0]
            
            # Device stats
            cursor.execute("SELECT COUNT(*) FROM devices")
            device_count = cursor.fetchone()[0]
            
            # Top domains
            cursor.execute(f"""
                SELECT host, COUNT(*) as cnt FROM traffic
                {since_clause}
                GROUP BY host
                ORDER BY cnt DESC
                LIMIT 10
            """, params)
            top_domains = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Top categories
            cursor.execute(f"""
                SELECT category, COUNT(*) as cnt FROM traffic
                WHERE category IS NOT NULL{' AND timestamp > ?' if since else ''}
                GROUP BY category
                ORDER BY cnt DESC
                LIMIT 10
            """, params)
            top_categories = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                "traffic_count": traffic_count,
                "bytes_in": bytes_in,
                "bytes_out": bytes_out,
                "blocked_count": blocked_count,
                "dns_count": dns_count,
                "dns_blocked": dns_blocked,
                "device_count": device_count,
                "top_domains": top_domains,
                "top_categories": top_categories
            }
    
    # Cleanup
    def cleanup_old_data(self, days: int = 30):
        """Delete data older than specified days."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("DELETE FROM traffic WHERE timestamp < ?", (cutoff,))
            traffic_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM dns_queries WHERE timestamp < ?", (cutoff,))
            dns_deleted = cursor.rowcount
            
            conn.commit()
            
            # Vacuum to reclaim space
            conn.execute("VACUUM")
            
            return {
                "traffic_deleted": traffic_deleted,
                "dns_deleted": dns_deleted
            }
    
    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0
    
    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for database operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management")
    parser.add_argument("--action", choices=[
        "stats", "search", "cleanup", "devices", "traffic", "dns",
        "get-traffic", "update-device", "export"
    ], default="stats", help="Action to perform")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--device", help="Device ID filter")
    parser.add_argument("--id", help="Entry ID for get operations")
    parser.add_argument("--monitored", help="Set monitored status (0 or 1)")
    parser.add_argument("--host", help="Host filter")
    parser.add_argument("--days", type=int, default=30, help="Cleanup days")
    parser.add_argument("--limit", type=int, default=100, help="Result limit")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    parser.add_argument("--output", help="Output file path for export")
    
    args = parser.parse_args()
    
    db = DatabaseManager()
    
    try:
        if args.action == "stats":
            stats = db.get_stats()
            stats["database_size_bytes"] = db.get_database_size()
            output_json({"success": True, "stats": stats})
        
        elif args.action == "search":
            if not args.query:
                output_json({"success": False, "error": "No query specified"})
                return
            
            results = db.search(args.query, limit=args.limit)
            output_json({
                "success": True,
                "count": len(results),
                "results": [r.to_dict() for r in results]
            })
        
        elif args.action == "cleanup":
            result = db.cleanup_old_data(days=args.days)
            output_json({"success": True, "cleanup": result})
        
        elif args.action == "devices":
            devices = db.list_devices()
            output_json({
                "success": True,
                "count": len(devices),
                "devices": [d.to_dict() for d in devices]
            })
        
        elif args.action == "traffic":
            entries = db.get_traffic(
                device_id=args.device,
                host=args.host,
                limit=args.limit
            )
            output_json({
                "success": True,
                "count": len(entries),
                "traffic": [e.to_dict() for e in entries]
            })
        
        elif args.action == "dns":
            queries = db.get_dns_queries(
                device_id=args.device,
                limit=args.limit
            )
            output_json({
                "success": True,
                "count": len(queries),
                "queries": [q.to_dict() for q in queries]
            })
        
        elif args.action == "get-traffic":
            if not args.id:
                output_json({"success": False, "error": "No entry ID specified"})
                return
            
            entry = db.get_traffic_entry(args.id)
            if entry:
                output_json({
                    "success": True,
                    "traffic": [entry.to_dict()]
                })
            else:
                output_json({"success": False, "error": f"Traffic entry not found: {args.id}"})
        
        elif args.action == "update-device":
            if not args.device:
                output_json({"success": False, "error": "No device ID specified"})
                return
            
            device = db.get_device(args.device)
            if not device:
                output_json({"success": False, "error": f"Device not found: {args.device}"})
                return
            
            # Update monitored status if specified
            if args.monitored is not None:
                device.is_monitored = args.monitored == "1"
            
            db.add_device(device)
            output_json({"success": True, "action": "updated", "device_id": args.device})
        
        elif args.action == "export":
            if not args.output:
                output_json({"success": False, "error": "No output path specified"})
                return
            
            # Export based on format
            stats = db.get_stats()
            devices = db.list_devices()
            traffic = db.get_traffic(limit=10000)
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "stats": stats,
                "devices": [d.to_dict() for d in devices],
                "traffic": [t.to_dict() for t in traffic]
            }
            
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if args.format == "json":
                with open(output_path, "w") as f:
                    json.dump(export_data, f, indent=2, default=str)
            elif args.format == "csv":
                import csv
                # Export traffic as CSV
                with open(output_path, "w", newline="") as f:
                    if traffic:
                        writer = csv.DictWriter(f, fieldnames=traffic[0].to_dict().keys())
                        writer.writeheader()
                        for entry in traffic:
                            writer.writerow(entry.to_dict())
            
            output_json({
                "success": True,
                "action": "exported",
                "path": str(output_path),
                "format": args.format,
                "records": len(traffic)
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })
    finally:
        db.close()


if __name__ == "__main__":
    main()
