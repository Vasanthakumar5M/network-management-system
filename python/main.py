#!/usr/bin/env python3
"""
Network Monitor - Main Entry Point

This is the main entry point for the Network Monitor Python backend.
It coordinates all the monitoring subsystems and communicates with the
Tauri frontend via JSON over stdout.

Usage:
    python main.py [--config CONFIG_PATH] [--mode MODE]

Modes:
    full        - Run all monitoring systems (default)
    dns-only    - Only DNS capture
    proxy-only  - Only HTTPS proxy
    arp-only    - Only ARP gateway
"""

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from python.utils.logger import setup_logger
from python.utils.config import ConfigManager
from python.utils.network_utils import get_default_interface, get_gateway_ip
from python.stealth.device_profiles import DeviceProfileManager
from python.stealth.mac_changer import MACChanger
from python.stealth.hostname_changer import HostnameChanger
from python.dns.dns_capture import DNSCapture
from python.dns.dns_blocker import DNSBlocker
from python.arp.arp_gateway import ARPGateway
from python.arp.device_scanner import DeviceScanner
from python.arp.ip_forwarding import IPForwarding
from python.https.transparent_proxy import TransparentProxy
from python.https.cert_generator import CertificateGenerator
from python.blocking.blocker import UnifiedBlocker
from python.alerts.alert_engine import AlertEngine
from python.alerts.notifier import Notifier
from python.database.db_manager import DatabaseManager


class NetworkMonitor:
    """Main Network Monitor orchestrator."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Network Monitor.
        
        Args:
            config_path: Optional path to configuration directory
        """
        self.logger = setup_logger("network_monitor")
        self.config_path = config_path or str(PROJECT_ROOT / "config")
        
        # Load configuration
        self.config = ConfigManager(self.config_path)
        
        # Initialize components (lazy loading)
        self._db: Optional[DatabaseManager] = None
        self._profile_manager: Optional[DeviceProfileManager] = None
        self._mac_changer: Optional[MACChanger] = None
        self._hostname_changer: Optional[HostnameChanger] = None
        self._dns_capture: Optional[DNSCapture] = None
        self._dns_blocker: Optional[DNSBlocker] = None
        self._arp_gateway: Optional[ARPGateway] = None
        self._device_scanner: Optional[DeviceScanner] = None
        self._ip_forwarding: Optional[IPForwarding] = None
        self._https_proxy: Optional[TransparentProxy] = None
        self._blocker: Optional[UnifiedBlocker] = None
        self._alert_engine: Optional[AlertEngine] = None
        self._notifier: Optional[Notifier] = None
        
        # State
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        
        # Network info
        self.interface: Optional[str] = None
        self.gateway_ip: Optional[str] = None
        self.local_ip: Optional[str] = None
        
    @property
    def db(self) -> DatabaseManager:
        """Lazy load database manager."""
        if self._db is None:
            db_path = self.config.get("database.path", "./database/network_monitor.db")
            self._db = DatabaseManager(db_path)
        return self._db
    
    @property
    def blocker(self) -> UnifiedBlocker:
        """Lazy load blocker."""
        if self._blocker is None:
            self._blocker = UnifiedBlocker(self.db)
        return self._blocker
    
    @property
    def alert_engine(self) -> AlertEngine:
        """Lazy load alert engine."""
        if self._alert_engine is None:
            self._alert_engine = AlertEngine(self.db)
        return self._alert_engine
    
    @property
    def notifier(self) -> Notifier:
        """Lazy load notifier."""
        if self._notifier is None:
            self._notifier = Notifier()
        return self._notifier

    def emit(self, event_type: str, data: dict) -> None:
        """Emit an event to the Tauri frontend via stdout JSON.
        
        Args:
            event_type: Type of event (traffic, alert, device, status, error)
            data: Event data dictionary
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        print(json.dumps(event), flush=True)

    def emit_status(self, message: str, level: str = "info") -> None:
        """Emit a status update."""
        self.emit("status", {"message": message, "level": level})

    def emit_error(self, error: str, component: str = "main") -> None:
        """Emit an error."""
        self.emit("error", {"error": error, "component": component})
        self.logger.error(f"[{component}] {error}")

    def setup_network(self) -> bool:
        """Detect and configure network settings.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get network interface
            interface_config = self.config.get("network.interface", "auto")
            if interface_config == "auto":
                self.interface = get_default_interface()
            else:
                self.interface = interface_config
                
            if not self.interface:
                self.emit_error("Could not detect network interface")
                return False
                
            # Get gateway IP
            gateway_config = self.config.get("network.gateway_ip", "auto")
            if gateway_config == "auto":
                self.gateway_ip = get_gateway_ip()
            else:
                self.gateway_ip = gateway_config
                
            if not self.gateway_ip:
                self.emit_error("Could not detect gateway IP")
                return False
                
            self.emit_status(f"Network: {self.interface}, Gateway: {self.gateway_ip}")
            return True
            
        except Exception as e:
            self.emit_error(f"Network setup failed: {e}")
            return False

    def setup_stealth(self) -> bool:
        """Configure stealth mode (MAC and hostname spoofing).
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config.get("stealth.enabled", True):
            self.emit_status("Stealth mode disabled", "warning")
            return True
            
        try:
            # Load device profiles
            self._profile_manager = DeviceProfileManager()
            
            # Get current profile
            profile_id = self.config.get("stealth.device_profile", "hp_printer")
            profile = self._profile_manager.get_profile(profile_id)
            
            if not profile:
                self.emit_error(f"Device profile not found: {profile_id}")
                return False
                
            # Change MAC address
            if self.config.get("stealth.change_mac", True):
                self._mac_changer = MACChanger()
                new_mac = self._profile_manager.generate_mac(profile_id)
                if self._mac_changer.change_mac(self.interface, new_mac):
                    self.emit_status(f"MAC changed to: {new_mac}")
                else:
                    self.emit_error("Failed to change MAC address")
                    
            # Change hostname
            if self.config.get("stealth.change_hostname", True):
                self._hostname_changer = HostnameChanger()
                hostname = profile.get("hostname", "Device")
                if self._hostname_changer.change_hostname(hostname):
                    self.emit_status(f"Hostname changed to: {hostname}")
                else:
                    self.emit_error("Failed to change hostname")
                    
            return True
            
        except Exception as e:
            self.emit_error(f"Stealth setup failed: {e}")
            return False

    def start_dns_capture(self) -> bool:
        """Start DNS capture system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._dns_blocker = DNSBlocker(self.blocker)
            self._dns_capture = DNSCapture(
                interface=self.interface,
                callback=self._on_dns_packet,
                blocker=self._dns_blocker
            )
            
            thread = threading.Thread(
                target=self._dns_capture.start,
                name="DNSCapture",
                daemon=True
            )
            thread.start()
            self._threads.append(thread)
            
            self.emit_status("DNS capture started")
            return True
            
        except Exception as e:
            self.emit_error(f"DNS capture failed: {e}", "dns")
            return False

    def start_arp_gateway(self) -> bool:
        """Start ARP spoofing gateway.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Enable IP forwarding
            self._ip_forwarding = IPForwarding()
            self._ip_forwarding.enable()
            
            # Scan for devices
            self._device_scanner = DeviceScanner(self.interface)
            devices = self._device_scanner.scan()
            self.emit_status(f"Found {len(devices)} devices on network")
            
            # Start ARP gateway
            self._arp_gateway = ARPGateway(
                interface=self.interface,
                gateway_ip=self.gateway_ip,
                targets=None,  # Target all devices
                callback=self._on_device_update
            )
            
            thread = threading.Thread(
                target=self._arp_gateway.start,
                name="ARPGateway",
                daemon=True
            )
            thread.start()
            self._threads.append(thread)
            
            self.emit_status("ARP gateway started")
            return True
            
        except Exception as e:
            self.emit_error(f"ARP gateway failed: {e}", "arp")
            return False

    def start_https_proxy(self) -> bool:
        """Start HTTPS interception proxy.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            port = self.config.get("proxy.listen_port", 8080)
            cert_path = PROJECT_ROOT / "certs"
            
            # Ensure certificate exists
            if not (cert_path / "ca-cert.pem").exists():
                self.emit_status("Generating CA certificate...")
                generator = CertificateGenerator()
                generator.generate(
                    output_dir=str(cert_path),
                    profile="google_trust"
                )
                
            self._https_proxy = TransparentProxy(
                port=port,
                cert_dir=str(cert_path),
                callback=self._on_http_flow
            )
            
            thread = threading.Thread(
                target=self._https_proxy.start,
                name="HTTPSProxy",
                daemon=True
            )
            thread.start()
            self._threads.append(thread)
            
            self.emit_status(f"HTTPS proxy started on port {port}")
            return True
            
        except Exception as e:
            self.emit_error(f"HTTPS proxy failed: {e}", "https")
            return False

    def _on_dns_packet(self, packet_data: dict) -> None:
        """Handle captured DNS packet.
        
        Args:
            packet_data: Parsed DNS packet data
        """
        try:
            # Store in database
            self.db.insert_dns_query(packet_data)
            
            # Check for alerts
            alert = self.alert_engine.check_dns(packet_data)
            if alert:
                self.notifier.notify(alert)
                self.emit("alert", alert)
                
            # Emit to frontend
            self.emit("dns", packet_data)
            
        except Exception as e:
            self.logger.error(f"DNS packet handling error: {e}")

    def _on_http_flow(self, flow_data: dict) -> None:
        """Handle captured HTTP/HTTPS flow.
        
        Args:
            flow_data: Parsed HTTP flow data
        """
        try:
            # Check blocking
            if self.blocker.should_block(flow_data):
                flow_data["is_blocked"] = True
                flow_data["block_reason"] = self.blocker.get_block_reason(flow_data)
                
            # Store in database
            self.db.insert_traffic(flow_data)
            
            # Check for alerts
            alert = self.alert_engine.check_traffic(flow_data)
            if alert:
                flow_data["has_alert"] = True
                self.notifier.notify(alert)
                self.emit("alert", alert)
                
            # Emit to frontend
            self.emit("traffic", flow_data)
            
        except Exception as e:
            self.logger.error(f"HTTP flow handling error: {e}")

    def _on_device_update(self, device_data: dict) -> None:
        """Handle device discovery/update.
        
        Args:
            device_data: Device information
        """
        try:
            # Store/update in database
            self.db.upsert_device(device_data)
            
            # Check if new device
            if device_data.get("is_new"):
                alert = {
                    "type": "new_device",
                    "severity": "low",
                    "title": "New device connected",
                    "description": f"Device {device_data.get('hostname', device_data.get('ip'))} joined the network",
                    "device": device_data
                }
                self.notifier.notify(alert)
                self.emit("alert", alert)
                
            # Emit to frontend
            self.emit("device", device_data)
            
        except Exception as e:
            self.logger.error(f"Device update handling error: {e}")

    def start(self, mode: str = "full") -> bool:
        """Start the Network Monitor.
        
        Args:
            mode: Operating mode (full, dns-only, proxy-only, arp-only)
            
        Returns:
            True if started successfully
        """
        self.logger.info(f"Starting Network Monitor in {mode} mode")
        self.emit_status(f"Starting Network Monitor ({mode} mode)")
        
        # Setup network
        if not self.setup_network():
            return False
            
        # Setup stealth
        if mode in ("full", "arp-only"):
            self.setup_stealth()
            
        # Start components based on mode
        success = True
        
        if mode in ("full", "dns-only"):
            success = success and self.start_dns_capture()
            
        if mode in ("full", "arp-only"):
            success = success and self.start_arp_gateway()
            
        if mode in ("full", "proxy-only"):
            success = success and self.start_https_proxy()
            
        if success:
            self.is_running = True
            self.start_time = datetime.now()
            self.emit_status("Network Monitor started successfully")
            self.emit("started", {
                "mode": mode,
                "interface": self.interface,
                "gateway": self.gateway_ip
            })
        else:
            self.emit_error("Failed to start some components")
            
        return success

    def stop(self) -> None:
        """Stop the Network Monitor and cleanup."""
        self.logger.info("Stopping Network Monitor")
        self.emit_status("Stopping Network Monitor...")
        
        self._stop_event.set()
        
        # Stop components
        if self._dns_capture:
            self._dns_capture.stop()
            
        if self._arp_gateway:
            self._arp_gateway.stop()
            
        if self._https_proxy:
            self._https_proxy.stop()
            
        # Disable IP forwarding
        if self._ip_forwarding:
            self._ip_forwarding.disable()
            
        # Wait for threads
        for thread in self._threads:
            thread.join(timeout=5)
            
        # Close database
        if self._db:
            self._db.close()
            
        self.is_running = False
        self.emit_status("Network Monitor stopped")
        self.emit("stopped", {})

    def run(self, mode: str = "full") -> None:
        """Run the Network Monitor until interrupted.
        
        Args:
            mode: Operating mode
        """
        # Setup signal handlers
        def signal_handler(sig, frame):
            self.logger.info(f"Received signal {sig}")
            self.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start monitoring
        if not self.start(mode):
            sys.exit(1)
            
        # Keep running
        try:
            while self.is_running and not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Network Monitor - Stealth Network Monitoring System"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration directory",
        default=None
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["full", "dns-only", "proxy-only", "arp-only"],
        default="full",
        help="Operating mode"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Create and run monitor
    monitor = NetworkMonitor(config_path=args.config)
    monitor.run(mode=args.mode)


if __name__ == "__main__":
    main()
