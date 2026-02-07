"""
Windows IP Forwarding Control
Enables/disables IP forwarding so your PC can act as a router
"""

import subprocess
import winreg
import json
from typing import Tuple


def enable_ip_forwarding(interface: str = None) -> Tuple[bool, str]:
    """
    Enable IP forwarding on Windows
    
    This allows your PC to forward packets between network interfaces,
    effectively acting as a router.
    
    Args:
        interface: Specific interface (optional)
        
    Returns:
        Tuple of (success, message)
    """
    success = True
    messages = []
    
    try:
        # Method 1: Registry (permanent, survives reboot)
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "IPEnableRouter", 0, winreg.REG_DWORD, 1)
        messages.append("Registry: IPEnableRouter set to 1")
    except Exception as e:
        messages.append(f"Registry error: {e}")
        success = False
    
    try:
        # Method 2: netsh (immediate effect)
        if interface:
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'set', 'interface', interface, 'forwarding=enabled'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                messages.append(f"netsh: Forwarding enabled on {interface}")
            else:
                messages.append(f"netsh error: {result.stderr}")
        else:
            # Enable on all interfaces
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'set', 'interface', 'interface=all', 'forwarding=enabled'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                messages.append("netsh: Forwarding enabled on all interfaces")
    except Exception as e:
        messages.append(f"netsh error: {e}")
    
    try:
        # Method 3: PowerShell (alternative)
        ps_cmd = 'Set-NetIPInterface -Forwarding Enabled -PolicyStore ActiveStore'
        result = subprocess.run(
            ['powershell', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            messages.append("PowerShell: Forwarding enabled")
    except Exception:
        pass
    
    return success, "; ".join(messages)


def disable_ip_forwarding(interface: str = None) -> Tuple[bool, str]:
    """
    Disable IP forwarding on Windows
    
    Args:
        interface: Specific interface (optional)
        
    Returns:
        Tuple of (success, message)
    """
    success = True
    messages = []
    
    try:
        # Registry
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "IPEnableRouter", 0, winreg.REG_DWORD, 0)
        messages.append("Registry: IPEnableRouter set to 0")
    except Exception as e:
        messages.append(f"Registry error: {e}")
        success = False
    
    try:
        # netsh
        if interface:
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'set', 'interface', interface, 'forwarding=disabled'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                messages.append(f"netsh: Forwarding disabled on {interface}")
        else:
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'set', 'interface', 'interface=all', 'forwarding=disabled'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                messages.append("netsh: Forwarding disabled on all interfaces")
    except Exception as e:
        messages.append(f"netsh error: {e}")
    
    try:
        # PowerShell
        ps_cmd = 'Set-NetIPInterface -Forwarding Disabled -PolicyStore ActiveStore'
        result = subprocess.run(
            ['powershell', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            messages.append("PowerShell: Forwarding disabled")
    except Exception:
        pass
    
    return success, "; ".join(messages)


def is_ip_forwarding_enabled() -> bool:
    """Check if IP forwarding is currently enabled"""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "IPEnableRouter")
            return value == 1
    except Exception:
        return False


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IP Forwarding Control")
    parser.add_argument("--enable", "-e", action="store_true", help="Enable IP forwarding")
    parser.add_argument("--disable", "-d", action="store_true", help="Disable IP forwarding")
    parser.add_argument("--status", "-s", action="store_true", help="Check current status")
    parser.add_argument("--interface", "-i", help="Specific interface")
    
    args = parser.parse_args()
    
    if args.status:
        enabled = is_ip_forwarding_enabled()
        print(json.dumps({"ip_forwarding_enabled": enabled}))
    elif args.enable:
        success, msg = enable_ip_forwarding(args.interface)
        print(json.dumps({"success": success, "message": msg}))
    elif args.disable:
        success, msg = disable_ip_forwarding(args.interface)
        print(json.dumps({"success": success, "message": msg}))
    else:
        parser.print_help()
