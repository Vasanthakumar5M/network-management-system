"""
Network utility functions for Network Monitor
"""

import socket
import subprocess
import re
from typing import Optional, List, Dict, Tuple
import psutil


def get_interfaces() -> List[Dict[str, str]]:
    """
    Get list of network interfaces with their details
    
    Returns:
        List of interface dictionaries with name, ip, mac, description
    """
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    
    for iface_name, addr_list in addrs.items():
        if iface_name in stats and stats[iface_name].isup:
            ip = ""
            mac = ""
            
            for addr in addr_list:
                if addr.family.name == 'AF_INET':
                    ip = addr.address
                elif addr.family.name == 'AF_LINK':
                    mac = addr.address
            
            # Skip loopback and interfaces without IP
            if ip and not ip.startswith('127.'):
                interfaces.append({
                    "name": iface_name,
                    "ip": ip,
                    "mac": mac,
                    "is_up": stats[iface_name].isup,
                    "speed": stats[iface_name].speed
                })
    
    return interfaces


def get_local_ip(interface: Optional[str] = None) -> Optional[str]:
    """
    Get local IP address
    
    Args:
        interface: Specific interface name (optional)
        
    Returns:
        Local IP address or None
    """
    if interface:
        addrs = psutil.net_if_addrs()
        if interface in addrs:
            for addr in addrs[interface]:
                if addr.family.name == 'AF_INET':
                    return addr.address
        return None
    
    # Auto-detect by connecting to external address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def get_mac_address(interface: Optional[str] = None) -> Optional[str]:
    """
    Get MAC address for interface
    
    Args:
        interface: Specific interface name (optional)
        
    Returns:
        MAC address or None
    """
    addrs = psutil.net_if_addrs()
    
    if interface and interface in addrs:
        for addr in addrs[interface]:
            if addr.family.name == 'AF_LINK':
                return addr.address
    
    # Return first non-empty MAC
    for iface_name, addr_list in addrs.items():
        for addr in addr_list:
            if addr.family.name == 'AF_LINK' and addr.address:
                return addr.address
    
    return None


def get_gateway_ip() -> Optional[str]:
    """
    Get default gateway IP address
    
    Returns:
        Gateway IP or None
    """
    try:
        # Windows: parse ipconfig output
        result = subprocess.run(
            ['ipconfig'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        for line in result.stdout.split('\n'):
            if 'Default Gateway' in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    
    # Fallback: try common gateway addresses
    local_ip = get_local_ip()
    if local_ip:
        parts = local_ip.split('.')
        parts[3] = '1'
        return '.'.join(parts)
    
    return None


def get_gateway_mac(gateway_ip: Optional[str] = None) -> Optional[str]:
    """
    Get gateway MAC address from ARP cache
    
    Args:
        gateway_ip: Gateway IP (auto-detected if not provided)
        
    Returns:
        Gateway MAC address or None
    """
    if not gateway_ip:
        gateway_ip = get_gateway_ip()
    
    if not gateway_ip:
        return None
    
    try:
        result = subprocess.run(
            ['arp', '-a'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        for line in result.stdout.split('\n'):
            if gateway_ip in line:
                # Match MAC address pattern
                match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
                if match:
                    return match.group(0).replace('-', ':').lower()
    except Exception:
        pass
    
    return None


def get_subnet_mask(interface: Optional[str] = None) -> Optional[str]:
    """Get subnet mask for interface"""
    addrs = psutil.net_if_addrs()
    
    if interface and interface in addrs:
        for addr in addrs[interface]:
            if addr.family.name == 'AF_INET':
                return addr.netmask
    
    # Return first valid netmask
    for iface_name, addr_list in addrs.items():
        for addr in addr_list:
            if addr.family.name == 'AF_INET' and addr.netmask:
                if not addr.address.startswith('127.'):
                    return addr.netmask
    
    return None


def get_network_range(interface: Optional[str] = None) -> str:
    """
    Get network range in CIDR notation
    
    Returns:
        Network range like "192.168.1.0/24"
    """
    ip = get_local_ip(interface)
    if not ip:
        return "192.168.1.0/24"
    
    # Simple /24 assumption for home networks
    parts = ip.split('.')
    parts[3] = '0'
    return '.'.join(parts) + '/24'


def is_admin() -> bool:
    """Check if running with administrator privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def ping(host: str, timeout: int = 1) -> bool:
    """Check if host is reachable"""
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', str(timeout * 1000), host],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return result.returncode == 0
    except Exception:
        return False


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    import json
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for network utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Network utilities")
    parser.add_argument("--action", choices=[
        "get-ip", "list-interfaces", "get-gateway", "get-mac", "get-range", "is-admin"
    ], default="list-interfaces", help="Action to perform")
    parser.add_argument("--interface", help="Network interface name")
    
    args = parser.parse_args()
    
    try:
        if args.action == "get-ip":
            ip = get_local_ip(args.interface)
            output_json({
                "success": True,
                "ip": ip,
                "interface": args.interface
            })
        
        elif args.action == "list-interfaces":
            interfaces = get_interfaces()
            # Mark default interface
            default_ip = get_local_ip()
            for iface in interfaces:
                iface["is_default"] = iface.get("ip") == default_ip
            
            output_json({
                "success": True,
                "interfaces": interfaces,
                "count": len(interfaces)
            })
        
        elif args.action == "get-gateway":
            gateway_ip = get_gateway_ip()
            gateway_mac = get_gateway_mac(gateway_ip)
            output_json({
                "success": True,
                "gateway_ip": gateway_ip,
                "gateway_mac": gateway_mac
            })
        
        elif args.action == "get-mac":
            mac = get_mac_address(args.interface)
            output_json({
                "success": True,
                "mac": mac,
                "interface": args.interface
            })
        
        elif args.action == "get-range":
            net_range = get_network_range(args.interface)
            output_json({
                "success": True,
                "range": net_range
            })
        
        elif args.action == "is-admin":
            admin = is_admin()
            output_json({
                "success": True,
                "is_admin": admin
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })


if __name__ == "__main__":
    main()
