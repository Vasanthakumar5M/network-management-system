"""
Desktop Notification System.

Provides real-time notifications for alerts:
- Windows toast notifications
- Sound alerts
- System tray integration
- Email notifications (optional)
"""

import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .keywords import AlertSeverity, AlertCategory


class NotificationType(Enum):
    """Types of notifications."""
    TOAST = "toast"  # Windows toast notification
    SOUND = "sound"  # Sound alert
    EMAIL = "email"  # Email notification
    WEBHOOK = "webhook"  # Webhook (for custom integrations)


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    enabled: bool = True
    
    # Which severities trigger notifications
    min_severity: AlertSeverity = AlertSeverity.MEDIUM
    
    # Notification types enabled
    toast_enabled: bool = True
    sound_enabled: bool = True
    email_enabled: bool = False
    webhook_enabled: bool = False
    
    # Sound settings
    sound_file: Optional[str] = None
    sound_volume: float = 1.0
    
    # Email settings
    email_address: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Webhook settings
    webhook_url: Optional[str] = None
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    
    # Rate limiting
    cooldown_seconds: int = 30  # Don't notify for same alert within this time
    max_per_hour: int = 50
    
    # Quiet hours
    quiet_start_hour: Optional[int] = None  # 22 for 10 PM
    quiet_end_hour: Optional[int] = None  # 7 for 7 AM
    
    # Category-specific settings
    category_overrides: Dict[str, dict] = field(default_factory=dict)


class Notifier:
    """
    Desktop notification system.
    
    Handles sending notifications through various channels.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the notifier.
        
        Args:
            config_file: Path to notification configuration
        """
        if config_file is None:
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / "config" / "notifications.json"
        
        self.config_file = Path(config_file)
        self.config = NotificationConfig()
        
        # Rate limiting
        self._notification_times: Dict[str, datetime] = {}
        self._hourly_count = 0
        self._hour_start: Optional[datetime] = None
        
        # Notification queue for async sending
        self._queue: List[dict] = []
        self._sending = False
        self._send_thread: Optional[threading.Thread] = None
        
        self._load_config()
    
    def _load_config(self):
        """Load notification configuration."""
        if not self.config_file.exists():
            return
        
        try:
            data = json.loads(self.config_file.read_text())
            
            self.config = NotificationConfig(
                enabled=data.get("enabled", True),
                min_severity=AlertSeverity(data.get("min_severity", "medium")),
                toast_enabled=data.get("toast_enabled", True),
                sound_enabled=data.get("sound_enabled", True),
                email_enabled=data.get("email_enabled", False),
                webhook_enabled=data.get("webhook_enabled", False),
                sound_file=data.get("sound_file"),
                sound_volume=data.get("sound_volume", 1.0),
                email_address=data.get("email_address"),
                smtp_server=data.get("smtp_server"),
                smtp_port=data.get("smtp_port", 587),
                smtp_user=data.get("smtp_user"),
                smtp_password=data.get("smtp_password"),
                webhook_url=data.get("webhook_url"),
                webhook_headers=data.get("webhook_headers", {}),
                cooldown_seconds=data.get("cooldown_seconds", 30),
                max_per_hour=data.get("max_per_hour", 50),
                quiet_start_hour=data.get("quiet_start_hour"),
                quiet_end_hour=data.get("quiet_end_hour"),
                category_overrides=data.get("category_overrides", {})
            )
        except Exception as e:
            print(json.dumps({"error": f"Failed to load notification config: {e}"}))
    
    def _save_config(self):
        """Save notification configuration."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "enabled": self.config.enabled,
            "min_severity": self.config.min_severity.value,
            "toast_enabled": self.config.toast_enabled,
            "sound_enabled": self.config.sound_enabled,
            "email_enabled": self.config.email_enabled,
            "webhook_enabled": self.config.webhook_enabled,
            "sound_file": self.config.sound_file,
            "sound_volume": self.config.sound_volume,
            "email_address": self.config.email_address,
            "smtp_server": self.config.smtp_server,
            "smtp_port": self.config.smtp_port,
            "smtp_user": self.config.smtp_user,
            # Don't save password in plain text
            "webhook_url": self.config.webhook_url,
            "webhook_headers": self.config.webhook_headers,
            "cooldown_seconds": self.config.cooldown_seconds,
            "max_per_hour": self.config.max_per_hour,
            "quiet_start_hour": self.config.quiet_start_hour,
            "quiet_end_hour": self.config.quiet_end_hour,
            "category_overrides": self.config.category_overrides
        }
        
        self.config_file.write_text(json.dumps(data, indent=2))
    
    def notify(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        category: Optional[AlertCategory] = None,
        alert_id: Optional[str] = None,
        async_send: bool = True
    ) -> bool:
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            severity: Alert severity
            category: Alert category
            alert_id: Unique alert ID for rate limiting
            async_send: Whether to send asynchronously
            
        Returns:
            True if notification was sent/queued
        """
        if not self.config.enabled:
            return False
        
        # Check severity threshold
        severity_order = [
            AlertSeverity.LOW,
            AlertSeverity.MEDIUM,
            AlertSeverity.HIGH,
            AlertSeverity.CRITICAL
        ]
        if severity_order.index(severity) < severity_order.index(self.config.min_severity):
            return False
        
        # Check quiet hours
        if self._is_quiet_hours():
            # Only notify for critical during quiet hours
            if severity != AlertSeverity.CRITICAL:
                return False
        
        # Check rate limiting
        if not self._check_rate_limit(alert_id or title):
            return False
        
        notification = {
            "title": title,
            "message": message,
            "severity": severity,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        
        if async_send:
            self._queue.append(notification)
            self._start_sender()
            return True
        else:
            return self._send_notification(notification)
    
    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours."""
        if self.config.quiet_start_hour is None or self.config.quiet_end_hour is None:
            return False
        
        current_hour = datetime.now().hour
        start = self.config.quiet_start_hour
        end = self.config.quiet_end_hour
        
        if start < end:
            # Normal range (e.g., 22-07)
            return start <= current_hour or current_hour < end
        else:
            # Overnight range
            return start <= current_hour < 24 or 0 <= current_hour < end
    
    def _check_rate_limit(self, key: str) -> bool:
        """Check rate limiting for a notification."""
        now = datetime.now()
        
        # Check per-alert cooldown
        last_time = self._notification_times.get(key)
        if last_time:
            if (now - last_time).seconds < self.config.cooldown_seconds:
                return False
        
        # Check hourly limit
        if self._hour_start is None or (now - self._hour_start) > timedelta(hours=1):
            self._hourly_count = 0
            self._hour_start = now
        
        if self._hourly_count >= self.config.max_per_hour:
            return False
        
        # Update tracking
        self._notification_times[key] = now
        self._hourly_count += 1
        
        return True
    
    def _start_sender(self):
        """Start the notification sender thread."""
        if self._sending:
            return
        
        self._sending = True
        self._send_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._send_thread.start()
    
    def _sender_loop(self):
        """Send queued notifications."""
        while self._sending and self._queue:
            notification = self._queue.pop(0)
            self._send_notification(notification)
            time.sleep(0.1)  # Small delay between notifications
        
        self._sending = False
    
    def _send_notification(self, notification: dict) -> bool:
        """Send a single notification through all enabled channels."""
        success = False
        
        title = notification["title"]
        message = notification["message"]
        severity = notification["severity"]
        
        # Toast notification
        if self.config.toast_enabled:
            if self._send_toast(title, message, severity):
                success = True
        
        # Sound
        if self.config.sound_enabled:
            self._play_sound(severity)
        
        # Email
        if self.config.email_enabled and self.config.email_address:
            self._send_email(title, message, severity)
        
        # Webhook
        if self.config.webhook_enabled and self.config.webhook_url:
            self._send_webhook(notification)
        
        return success
    
    def _send_toast(
        self,
        title: str,
        message: str,
        severity: AlertSeverity
    ) -> bool:
        """Send a Windows toast notification."""
        try:
            # Use PowerShell for Windows toast notifications
            if os.name == 'nt':
                # Escape special characters for PowerShell
                title_escaped = title.replace("'", "''").replace('"', '`"')
                message_escaped = message.replace("'", "''").replace('"', '`"')
                
                # Create toast notification using PowerShell
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

                $template = @"
                <toast>
                    <visual>
                        <binding template="ToastText02">
                            <text id="1">{title_escaped}</text>
                            <text id="2">{message_escaped}</text>
                        </binding>
                    </visual>
                    <audio src="ms-winsoundevent:Notification.Default"/>
                </toast>
"@

                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Network Monitor").Show($toast)
                '''
                
                subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                    capture_output=True,
                    timeout=5
                )
                return True
            
            else:
                # Linux/Mac - use notify-send or osascript
                if os.system("which notify-send > /dev/null 2>&1") == 0:
                    subprocess.run(["notify-send", title, message], timeout=5)
                    return True
        
        except Exception as e:
            print(json.dumps({"error": f"Toast notification failed: {e}"}))
        
        return False
    
    def _play_sound(self, severity: AlertSeverity):
        """Play alert sound."""
        try:
            if os.name == 'nt':
                import winsound
                
                if self.config.sound_file and os.path.exists(self.config.sound_file):
                    winsound.PlaySound(self.config.sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    # Use system sounds based on severity
                    if severity == AlertSeverity.CRITICAL:
                        winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    elif severity == AlertSeverity.HIGH:
                        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    else:
                        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        
        except Exception:
            pass
    
    def _send_email(
        self,
        title: str,
        message: str,
        severity: AlertSeverity
    ):
        """Send email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            if not all([
                self.config.email_address,
                self.config.smtp_server,
                self.config.smtp_user,
                self.config.smtp_password
            ]):
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_user
            msg['To'] = self.config.email_address
            msg['Subject'] = f"[{severity.value.upper()}] {title}"
            
            body = f"""
Network Monitor Alert
---------------------
Severity: {severity.value.upper()}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)
        
        except Exception as e:
            print(json.dumps({"error": f"Email notification failed: {e}"}))
    
    def _send_webhook(self, notification: dict):
        """Send webhook notification."""
        try:
            import urllib.request
            
            if not self.config.webhook_url:
                return
            
            payload = {
                "title": notification["title"],
                "message": notification["message"],
                "severity": notification["severity"].value,
                "timestamp": notification["timestamp"],
                "category": notification["category"].value if notification.get("category") else None
            }
            
            data = json.dumps(payload).encode('utf-8')
            
            headers = {
                'Content-Type': 'application/json',
                **self.config.webhook_headers
            }
            
            req = urllib.request.Request(
                self.config.webhook_url,
                data=data,
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                pass
        
        except Exception as e:
            print(json.dumps({"error": f"Webhook notification failed: {e}"}))
    
    def update_config(self, **kwargs) -> bool:
        """Update notification configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                if key == 'min_severity':
                    value = AlertSeverity(value)
                setattr(self.config, key, value)
        
        self._save_config()
        return True
    
    def test_notification(self) -> bool:
        """Send a test notification."""
        return self.notify(
            title="Test Notification",
            message="This is a test notification from Network Monitor",
            severity=AlertSeverity.LOW,
            async_send=False
        )
    
    def get_status(self) -> dict:
        """Get notification system status."""
        return {
            "enabled": self.config.enabled,
            "toast_enabled": self.config.toast_enabled,
            "sound_enabled": self.config.sound_enabled,
            "email_enabled": self.config.email_enabled,
            "webhook_enabled": self.config.webhook_enabled,
            "min_severity": self.config.min_severity.value,
            "quiet_hours": {
                "start": self.config.quiet_start_hour,
                "end": self.config.quiet_end_hour,
                "active": self._is_quiet_hours()
            },
            "hourly_count": self._hourly_count,
            "max_per_hour": self.config.max_per_hour
        }


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for notifications."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Desktop notifications")
    parser.add_argument("--action", choices=[
        "test", "status", "send", "enable", "disable", "configure"
    ], default="status", help="Action to perform")
    parser.add_argument("--title", help="Notification title")
    parser.add_argument("--message", help="Notification message")
    parser.add_argument("--severity", default="medium", help="Alert severity")
    parser.add_argument("--channel", choices=["toast", "sound", "email", "webhook"],
                       help="Channel to enable/disable")
    parser.add_argument("--value", help="Configuration value")
    
    args = parser.parse_args()
    
    notifier = Notifier()
    
    try:
        if args.action == "test":
            success = notifier.test_notification()
            output_json({"success": success, "action": "test"})
        
        elif args.action == "status":
            output_json({
                "success": True,
                "status": notifier.get_status()
            })
        
        elif args.action == "send":
            if not args.title or not args.message:
                output_json({"success": False, "error": "Title and message required"})
                return
            
            success = notifier.notify(
                title=args.title,
                message=args.message,
                severity=AlertSeverity(args.severity),
                async_send=False
            )
            output_json({"success": success, "action": "sent"})
        
        elif args.action == "enable":
            if args.channel == "toast":
                notifier.update_config(toast_enabled=True)
            elif args.channel == "sound":
                notifier.update_config(sound_enabled=True)
            elif args.channel == "email":
                notifier.update_config(email_enabled=True)
            elif args.channel == "webhook":
                notifier.update_config(webhook_enabled=True)
            else:
                notifier.update_config(enabled=True)
            
            output_json({"success": True, "action": "enabled", "channel": args.channel})
        
        elif args.action == "disable":
            if args.channel == "toast":
                notifier.update_config(toast_enabled=False)
            elif args.channel == "sound":
                notifier.update_config(sound_enabled=False)
            elif args.channel == "email":
                notifier.update_config(email_enabled=False)
            elif args.channel == "webhook":
                notifier.update_config(webhook_enabled=False)
            else:
                notifier.update_config(enabled=False)
            
            output_json({"success": True, "action": "disabled", "channel": args.channel})
        
        elif args.action == "configure":
            output_json({
                "success": True,
                "current_config": notifier.get_status(),
                "help": "Use --channel and --value to configure specific settings"
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })


if __name__ == "__main__":
    main()
