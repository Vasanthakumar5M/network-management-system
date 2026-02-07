"""
Transparent Proxy for HTTPS Interception.

Uses mitmproxy to intercept, decrypt, and analyze HTTPS traffic.
Supports:
- Transparent proxy mode (for ARP-spoofed traffic)
- Content filtering and blocking
- Real-time traffic streaming to Tauri frontend
- Certificate management
"""

import asyncio
import json
import os
import queue
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

# mitmproxy imports (will be available when running)
try:
    from mitmproxy import ctx, http, options
    from mitmproxy.addons import default_addons
    from mitmproxy.master import Master
    from mitmproxy.proxy import config as proxy_config
    from mitmproxy.tools.dump import DumpMaster
    MITMPROXY_AVAILABLE = True
except ImportError:
    MITMPROXY_AVAILABLE = False

from .traffic_parser import ParsedFlow, TrafficParser, TrafficCategory


@dataclass
class ProxyConfig:
    """Configuration for the transparent proxy."""
    listen_host: str = "0.0.0.0"
    listen_port: int = 8080
    transparent_mode: bool = True
    ssl_insecure: bool = True  # Accept invalid upstream certs
    ca_cert_path: Optional[str] = None  # Custom CA cert
    ca_key_path: Optional[str] = None  # Custom CA key
    block_list: Set[str] = field(default_factory=set)
    category_blocks: Set[TrafficCategory] = field(default_factory=set)
    keyword_alerts: List[str] = field(default_factory=list)
    max_body_size: int = 10 * 1024 * 1024  # 10MB
    stream_large_bodies: int = 5 * 1024 * 1024  # Stream bodies > 5MB
    anticache: bool = True
    anticomp: bool = True  # Disable compression for easier analysis


@dataclass 
class FlowEvent:
    """Event representing a traffic flow for IPC."""
    event_type: str  # "request", "response", "error", "blocked"
    flow_id: str
    timestamp: str
    data: Dict[str, Any]


class TrafficInterceptor:
    """
    mitmproxy addon for intercepting and analyzing traffic.
    
    This addon is loaded into mitmproxy and receives callbacks
    for each HTTP request/response.
    """
    
    def __init__(
        self,
        config: ProxyConfig,
        event_callback: Callable[[FlowEvent], None],
        parser: Optional[TrafficParser] = None
    ):
        """
        Initialize the traffic interceptor.
        
        Args:
            config: Proxy configuration
            event_callback: Callback for traffic events
            parser: Optional TrafficParser instance
        """
        self.config = config
        self.event_callback = event_callback
        self.parser = parser or TrafficParser()
        self.active_flows: Dict[str, Dict[str, Any]] = {}
    
    def load(self, loader):
        """Called when addon is loaded."""
        pass
    
    def configure(self, updated):
        """Called when configuration changes."""
        pass
    
    def request(self, flow: http.HTTPFlow):
        """
        Called when a request is received.
        
        This is where we can block, modify, or analyze requests.
        """
        flow_id = flow.id
        host = flow.request.host
        url = flow.request.pretty_url
        
        # Check block list
        if self._should_block(flow):
            self._block_flow(flow, "Domain blocked by policy")
            return
        
        # Check category blocks
        category = self.parser._categorize_domain(host)
        if category in self.config.category_blocks:
            self._block_flow(flow, f"Category blocked: {category.value}")
            return
        
        # Track flow
        self.active_flows[flow_id] = {
            "start_time": time.time(),
            "host": host,
            "url": url
        }
        
        # Parse and emit request event
        try:
            parsed = self.parser.parse_mitmproxy_flow(flow)
            self._emit_event(FlowEvent(
                event_type="request",
                flow_id=flow_id,
                timestamp=datetime.utcnow().isoformat(),
                data=self.parser.to_dict(parsed)
            ))
        except Exception as e:
            self._emit_event(FlowEvent(
                event_type="error",
                flow_id=flow_id,
                timestamp=datetime.utcnow().isoformat(),
                data={"error": str(e), "phase": "request"}
            ))
    
    def response(self, flow: http.HTTPFlow):
        """
        Called when a response is received.
        
        This is where we analyze response content and detect alerts.
        """
        flow_id = flow.id
        
        # Remove from active flows
        flow_info = self.active_flows.pop(flow_id, {})
        
        # Calculate duration
        duration_ms = 0
        if "start_time" in flow_info:
            duration_ms = int((time.time() - flow_info["start_time"]) * 1000)
        
        # Parse and emit response event
        try:
            parsed = self.parser.parse_mitmproxy_flow(flow)
            parsed.duration_ms = duration_ms
            
            # Check for keyword alerts
            alerts = self._check_keyword_alerts(flow)
            if alerts:
                parsed.alerts.extend(alerts)
            
            self._emit_event(FlowEvent(
                event_type="response",
                flow_id=flow_id,
                timestamp=datetime.utcnow().isoformat(),
                data=self.parser.to_dict(parsed)
            ))
            
            # Emit alert events separately for real-time notifications
            for alert in parsed.alerts:
                self._emit_event(FlowEvent(
                    event_type="alert",
                    flow_id=flow_id,
                    timestamp=datetime.utcnow().isoformat(),
                    data={
                        "alert_type": alert,
                        "host": flow.request.host,
                        "url": flow.request.pretty_url
                    }
                ))
        
        except Exception as e:
            self._emit_event(FlowEvent(
                event_type="error",
                flow_id=flow_id,
                timestamp=datetime.utcnow().isoformat(),
                data={"error": str(e), "phase": "response"}
            ))
    
    def error(self, flow: http.HTTPFlow):
        """Called when an error occurs."""
        self._emit_event(FlowEvent(
            event_type="error",
            flow_id=flow.id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "error": str(flow.error) if flow.error else "Unknown error",
                "host": flow.request.host if flow.request else "unknown"
            }
        ))
    
    def _should_block(self, flow: http.HTTPFlow) -> bool:
        """Check if flow should be blocked."""
        host = flow.request.host.lower()
        url = flow.request.pretty_url.lower()
        
        for blocked in self.config.block_list:
            blocked = blocked.lower()
            if blocked in host or blocked in url:
                return True
        
        return False
    
    def _block_flow(self, flow: http.HTTPFlow, reason: str):
        """Block a flow with a custom response."""
        # Kill the flow
        flow.kill()
        
        # Emit blocked event
        self._emit_event(FlowEvent(
            event_type="blocked",
            flow_id=flow.id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "reason": reason,
                "host": flow.request.host,
                "url": flow.request.pretty_url
            }
        ))
    
    def _check_keyword_alerts(self, flow: http.HTTPFlow) -> List[str]:
        """Check for keyword matches in request/response."""
        alerts = []
        
        if not self.config.keyword_alerts:
            return alerts
        
        # Check URL
        url = flow.request.pretty_url.lower()
        for keyword in self.config.keyword_alerts:
            keyword = keyword.lower()
            if keyword in url:
                alerts.append(f"KEYWORD_URL:{keyword}")
        
        # Check request body
        if flow.request.content:
            try:
                content = flow.request.content.decode('utf-8', errors='ignore').lower()
                for keyword in self.config.keyword_alerts:
                    keyword = keyword.lower()
                    if keyword in content:
                        alerts.append(f"KEYWORD_REQUEST:{keyword}")
            except Exception:
                pass
        
        # Check response body
        if flow.response and flow.response.content:
            try:
                content = flow.response.content.decode('utf-8', errors='ignore').lower()
                for keyword in self.config.keyword_alerts:
                    keyword = keyword.lower()
                    if keyword in content:
                        alerts.append(f"KEYWORD_RESPONSE:{keyword}")
            except Exception:
                pass
        
        return alerts
    
    def _emit_event(self, event: FlowEvent):
        """Emit event through callback."""
        if self.event_callback:
            self.event_callback(event)


class TransparentProxy:
    """
    Manages the mitmproxy transparent proxy.
    
    Provides methods to start, stop, and configure the proxy,
    with IPC support for Tauri integration.
    """
    
    def __init__(self, config: Optional[ProxyConfig] = None):
        """
        Initialize the transparent proxy.
        
        Args:
            config: Proxy configuration
        """
        self.config = config or ProxyConfig()
        self.master: Optional[Master] = None
        self.event_queue: queue.Queue = queue.Queue()
        self.running = False
        self._proxy_thread: Optional[threading.Thread] = None
    
    def _event_handler(self, event: FlowEvent):
        """Handle events from the interceptor."""
        self.event_queue.put(event)
        
        # Also output to stdout for Tauri IPC
        output_json({
            "type": "flow_event",
            "event_type": event.event_type,
            "flow_id": event.flow_id,
            "timestamp": event.timestamp,
            "data": event.data
        })
    
    async def _run_proxy(self):
        """Run the mitmproxy master."""
        if not MITMPROXY_AVAILABLE:
            raise RuntimeError("mitmproxy is not installed")
        
        # Build mitmproxy options
        opts = options.Options(
            listen_host=self.config.listen_host,
            listen_port=self.config.listen_port,
            mode=["transparent"] if self.config.transparent_mode else ["regular"],
            ssl_insecure=self.config.ssl_insecure,
            anticache=self.config.anticache,
            anticomp=self.config.anticomp,
        )
        
        # Set custom CA if provided
        if self.config.ca_cert_path and self.config.ca_key_path:
            # mitmproxy expects combined PEM file
            combined_path = Path(self.config.ca_cert_path).with_suffix('.pem')
            if combined_path.exists():
                opts.certs = [str(combined_path)]
        
        # Create master
        self.master = DumpMaster(opts)
        
        # Add our interceptor addon
        interceptor = TrafficInterceptor(
            config=self.config,
            event_callback=self._event_handler
        )
        self.master.addons.add(interceptor)
        
        # Run
        self.running = True
        try:
            await self.master.run()
        finally:
            self.running = False
    
    def start(self):
        """Start the proxy in a background thread."""
        if self.running:
            return
        
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_proxy())
            except Exception as e:
                output_json({
                    "type": "error",
                    "error": str(e),
                    "context": "proxy_startup"
                })
            finally:
                loop.close()
        
        self._proxy_thread = threading.Thread(target=run_in_thread, daemon=True)
        self._proxy_thread.start()
        
        # Wait for startup
        time.sleep(1)
        
        output_json({
            "type": "status",
            "status": "started",
            "host": self.config.listen_host,
            "port": self.config.listen_port,
            "mode": "transparent" if self.config.transparent_mode else "regular"
        })
    
    def stop(self):
        """Stop the proxy."""
        if self.master:
            self.master.shutdown()
        self.running = False
        
        output_json({
            "type": "status",
            "status": "stopped"
        })
    
    def add_to_blocklist(self, domain: str):
        """Add domain to block list."""
        self.config.block_list.add(domain.lower())
        output_json({
            "type": "config_update",
            "action": "add_block",
            "domain": domain
        })
    
    def remove_from_blocklist(self, domain: str):
        """Remove domain from block list."""
        self.config.block_list.discard(domain.lower())
        output_json({
            "type": "config_update",
            "action": "remove_block",
            "domain": domain
        })
    
    def block_category(self, category: str):
        """Block a traffic category."""
        try:
            cat = TrafficCategory(category)
            self.config.category_blocks.add(cat)
            output_json({
                "type": "config_update",
                "action": "block_category",
                "category": category
            })
        except ValueError:
            output_json({
                "type": "error",
                "error": f"Unknown category: {category}"
            })
    
    def unblock_category(self, category: str):
        """Unblock a traffic category."""
        try:
            cat = TrafficCategory(category)
            self.config.category_blocks.discard(cat)
            output_json({
                "type": "config_update",
                "action": "unblock_category",
                "category": category
            })
        except ValueError:
            pass
    
    def add_keyword_alert(self, keyword: str):
        """Add keyword for alert detection."""
        if keyword not in self.config.keyword_alerts:
            self.config.keyword_alerts.append(keyword.lower())
        output_json({
            "type": "config_update",
            "action": "add_keyword",
            "keyword": keyword
        })
    
    def remove_keyword_alert(self, keyword: str):
        """Remove keyword from alert detection."""
        keyword = keyword.lower()
        if keyword in self.config.keyword_alerts:
            self.config.keyword_alerts.remove(keyword)
        output_json({
            "type": "config_update",
            "action": "remove_keyword",
            "keyword": keyword
        })
    
    def get_events(self, timeout: float = 0.1) -> List[FlowEvent]:
        """
        Get pending events from the queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            List of FlowEvent objects
        """
        events = []
        try:
            while True:
                event = self.event_queue.get(timeout=timeout)
                events.append(event)
        except queue.Empty:
            pass
        return events


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def setup_windows_redirect(listen_port: int = 8080) -> bool:
    """
    Set up Windows traffic redirection using netsh.
    
    This redirects traffic to the transparent proxy.
    Requires Administrator privileges.
    
    Returns:
        True if successful
    """
    import subprocess
    
    try:
        # Enable IP forwarding
        subprocess.run(
            ["netsh", "interface", "ipv4", "set", "global", "forwarding=enabled"],
            check=True,
            capture_output=True
        )
        
        # Add port proxy rule for HTTP
        subprocess.run([
            "netsh", "interface", "portproxy", "add", "v4tov4",
            f"listenport=80", f"listenaddress=0.0.0.0",
            f"connectport={listen_port}", "connectaddress=127.0.0.1"
        ], check=True, capture_output=True)
        
        # Add port proxy rule for HTTPS
        subprocess.run([
            "netsh", "interface", "portproxy", "add", "v4tov4",
            f"listenport=443", f"listenaddress=0.0.0.0",
            f"connectport={listen_port}", "connectaddress=127.0.0.1"
        ], check=True, capture_output=True)
        
        return True
    
    except subprocess.CalledProcessError as e:
        output_json({
            "type": "error",
            "error": f"Failed to set up redirect: {e.stderr.decode()}"
        })
        return False


def cleanup_windows_redirect():
    """Clean up Windows traffic redirection rules."""
    import subprocess
    
    try:
        # Remove port proxy rules
        subprocess.run([
            "netsh", "interface", "portproxy", "delete", "v4tov4",
            "listenport=80", "listenaddress=0.0.0.0"
        ], capture_output=True)
        
        subprocess.run([
            "netsh", "interface", "portproxy", "delete", "v4tov4",
            "listenport=443", "listenaddress=0.0.0.0"
        ], capture_output=True)
        
        output_json({
            "type": "status",
            "status": "redirect_cleaned"
        })
    except Exception as e:
        output_json({
            "type": "error",
            "error": f"Failed to clean up redirect: {str(e)}"
        })


def main():
    """CLI entry point for the transparent proxy."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Transparent HTTPS proxy")
    parser.add_argument("--action", choices=["start", "stop", "status", "setup-redirect", "cleanup-redirect"],
                       default="start", help="Action to perform")
    parser.add_argument("--port", type=int, default=8080, help="Proxy listen port")
    parser.add_argument("--host", default="0.0.0.0", help="Proxy listen host")
    parser.add_argument("--transparent", action="store_true", default=True,
                       help="Run in transparent mode")
    parser.add_argument("--ca-cert", help="Path to CA certificate")
    parser.add_argument("--ca-key", help="Path to CA key")
    parser.add_argument("--block", action="append", default=[],
                       help="Domains to block")
    parser.add_argument("--block-category", action="append", default=[],
                       help="Categories to block")
    parser.add_argument("--keyword", action="append", default=[],
                       help="Keywords to alert on")
    
    args = parser.parse_args()
    
    if args.action == "setup-redirect":
        success = setup_windows_redirect(args.port)
        output_json({
            "success": success,
            "action": "setup_redirect"
        })
        return
    
    if args.action == "cleanup-redirect":
        cleanup_windows_redirect()
        return
    
    if args.action == "status":
        output_json({
            "mitmproxy_available": MITMPROXY_AVAILABLE,
            "default_port": 8080
        })
        return
    
    if not MITMPROXY_AVAILABLE:
        output_json({
            "success": False,
            "error": "mitmproxy is not installed. Run: pip install mitmproxy"
        })
        sys.exit(1)
    
    # Build config
    config = ProxyConfig(
        listen_host=args.host,
        listen_port=args.port,
        transparent_mode=args.transparent,
        ca_cert_path=args.ca_cert,
        ca_key_path=args.ca_key,
        block_list=set(args.block),
        keyword_alerts=args.keyword
    )
    
    # Add category blocks
    for cat in args.block_category:
        try:
            config.category_blocks.add(TrafficCategory(cat))
        except ValueError:
            output_json({
                "type": "warning",
                "message": f"Unknown category: {cat}"
            })
    
    # Create and start proxy
    proxy = TransparentProxy(config)
    
    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        output_json({"type": "status", "status": "shutting_down"})
        proxy.stop()
        cleanup_windows_redirect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.action == "start":
        proxy.start()
        
        # Keep running and read commands from stdin
        try:
            while proxy.running:
                try:
                    line = input()
                    if not line:
                        continue
                    
                    cmd = json.loads(line)
                    action = cmd.get("action")
                    
                    if action == "stop":
                        proxy.stop()
                        break
                    elif action == "add_block":
                        proxy.add_to_blocklist(cmd.get("domain", ""))
                    elif action == "remove_block":
                        proxy.remove_from_blocklist(cmd.get("domain", ""))
                    elif action == "block_category":
                        proxy.block_category(cmd.get("category", ""))
                    elif action == "unblock_category":
                        proxy.unblock_category(cmd.get("category", ""))
                    elif action == "add_keyword":
                        proxy.add_keyword_alert(cmd.get("keyword", ""))
                    elif action == "remove_keyword":
                        proxy.remove_keyword_alert(cmd.get("keyword", ""))
                    elif action == "status":
                        output_json({
                            "type": "status",
                            "running": proxy.running,
                            "block_list": list(proxy.config.block_list),
                            "blocked_categories": [c.value for c in proxy.config.category_blocks],
                            "keyword_alerts": proxy.config.keyword_alerts
                        })
                
                except json.JSONDecodeError:
                    pass
                except EOFError:
                    break
        
        except KeyboardInterrupt:
            pass
        
        finally:
            proxy.stop()


if __name__ == "__main__":
    main()
