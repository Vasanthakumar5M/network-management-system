"""
Hostname Changer for Windows
Changes the computer's hostname to match the spoofed device profile
"""

import subprocess
import socket
import winreg
from typing import Optional, Tuple


def get_hostname() -> str:
    """Get current computer hostname"""
    return socket.gethostname()


def change_hostname(new_hostname: str) -> Tuple[bool, str]:
    """
    Change the computer's hostname
    
    Note: Full hostname change requires restart.
    This changes the NetBIOS name which takes effect on network immediately.
    
    Args:
        new_hostname: New hostname (max 15 characters for NetBIOS)
        
    Returns:
        Tuple of (success, message)
    """
    # NetBIOS name limit
    if len(new_hostname) > 15:
        new_hostname = new_hostname[:15]
    
    try:
        # Method 1: Using WMIC (older but widely compatible)
        result = subprocess.run(
            ['wmic', 'computersystem', 'where', 'name="%COMPUTERNAME%"', 
             'call', 'rename', f'name="{new_hostname}"'],
            capture_output=True,
            text=True,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            return True, f"Hostname change initiated to '{new_hostname}'. May require restart for full effect."
        
    except Exception as e:
        pass
    
    try:
        # Method 2: Using PowerShell (modern)
        ps_command = f'Rename-Computer -NewName "{new_hostname}" -Force -ErrorAction SilentlyContinue'
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            return True, f"Hostname changed to '{new_hostname}'. Restart required for full effect."
            
    except Exception as e:
        pass
    
    try:
        # Method 3: Registry modification (takes effect after restart)
        key_path = r"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "ComputerName", 0, winreg.REG_SZ, new_hostname)
        
        # Also set ActiveComputerName
        active_key_path = r"SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, active_key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "ComputerName", 0, winreg.REG_SZ, new_hostname)
        
        return True, f"Hostname set to '{new_hostname}' in registry. Restart required."
        
    except Exception as e:
        return False, f"Failed to change hostname: {e}"


def get_netbios_name() -> Optional[str]:
    """Get the NetBIOS name of the computer"""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            return winreg.QueryValueEx(key, "ComputerName")[0]
    except Exception:
        return socket.gethostname()


# CLI interface
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Hostname Changer")
    parser.add_argument("--set", "-s", help="New hostname to set")
    parser.add_argument("--show", action="store_true", help="Show current hostname")
    
    args = parser.parse_args()
    
    if args.show:
        print(json.dumps({
            "hostname": get_hostname(),
            "netbios": get_netbios_name()
        }))
    elif args.set:
        success, msg = change_hostname(args.set)
        print(json.dumps({"success": success, "message": msg}))
    else:
        parser.print_help()
