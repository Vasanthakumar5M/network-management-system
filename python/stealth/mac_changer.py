"""
MAC Address Changer for Windows
Changes the MAC address of a network interface to disguise the device
"""

import subprocess
import winreg
import re
import time
import json
import sys
from typing import Optional, Dict, Tuple
from pathlib import Path

from .device_profiles import DeviceProfile, DeviceProfiles, get_random_profile


class MACChanger:
    """
    Windows MAC Address Changer
    Uses registry modification and netsh to change MAC address
    """
    
    def __init__(self, interface: str):
        """
        Initialize MAC changer for specific interface
        
        Args:
            interface: Network interface name (e.g., "Wi-Fi", "Ethernet")
        """
        self.interface = interface
        self.original_mac: Optional[str] = None
        self.current_mac: Optional[str] = None
        self._adapter_key: Optional[str] = None
    
    def _get_adapter_registry_key(self) -> Optional[str]:
        """Find the registry key for the network adapter"""
        if self._adapter_key:
            return self._adapter_key
        
        try:
            # Search in network adapter configurations
            reg_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey_path = f"{reg_path}\\{subkey_name}"
                        
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                            try:
                                driver_desc = winreg.QueryValueEx(subkey, "DriverDesc")[0]
                                net_cfg_id = winreg.QueryValueEx(subkey, "NetCfgInstanceId")[0]
                                
                                # Check if this matches our interface
                                if self.interface.lower() in driver_desc.lower():
                                    self._adapter_key = subkey_path
                                    return subkey_path
                            except WindowsError:
                                pass
                        i += 1
                    except WindowsError:
                        break
        except Exception as e:
            print(f"Error finding adapter registry key: {e}")
        
        return None
    
    def get_current_mac(self) -> Optional[str]:
        """Get current MAC address of the interface"""
        try:
            result = subprocess.run(
                ['getmac', '/v', '/fo', 'csv'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            for line in result.stdout.split('\n'):
                if self.interface in line:
                    # Extract MAC from CSV
                    parts = line.split(',')
                    for part in parts:
                        mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}', part)
                        if mac_match:
                            return mac_match.group(0).replace('-', ':').upper()
        except Exception:
            pass
        
        # Alternative method using ipconfig
        try:
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            in_interface = False
            for line in result.stdout.split('\n'):
                if self.interface in line:
                    in_interface = True
                elif in_interface and 'Physical Address' in line:
                    mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}', line)
                    if mac_match:
                        return mac_match.group(0).replace('-', ':').upper()
                elif in_interface and line.strip() == '':
                    in_interface = False
        except Exception:
            pass
        
        return None
    
    def _disable_interface(self) -> bool:
        """Disable the network interface"""
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'set', 'interface', self.interface, 'disable'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(1)
            return result.returncode == 0
        except Exception:
            return False
    
    def _enable_interface(self) -> bool:
        """Enable the network interface"""
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'set', 'interface', self.interface, 'enable'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(2)  # Wait for interface to come up
            return result.returncode == 0
        except Exception:
            return False
    
    def _set_mac_registry(self, mac: str) -> bool:
        """Set MAC address in Windows registry"""
        adapter_key = self._get_adapter_registry_key()
        if not adapter_key:
            print("Could not find adapter registry key")
            return False
        
        # Remove colons/dashes from MAC
        mac_clean = mac.replace(':', '').replace('-', '')
        
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, 
                adapter_key, 
                0, 
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, "NetworkAddress", 0, winreg.REG_SZ, mac_clean)
            return True
        except Exception as e:
            print(f"Error setting MAC in registry: {e}")
            return False
    
    def _remove_mac_registry(self) -> bool:
        """Remove custom MAC address from registry (restore original)"""
        adapter_key = self._get_adapter_registry_key()
        if not adapter_key:
            return False
        
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, 
                adapter_key, 
                0, 
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, "NetworkAddress")
            return True
        except WindowsError:
            # Value might not exist
            return True
        except Exception:
            return False
    
    def change_mac(self, new_mac: str) -> Tuple[bool, str]:
        """
        Change the MAC address
        
        Args:
            new_mac: New MAC address (format: XX:XX:XX:XX:XX:XX)
            
        Returns:
            Tuple of (success, message)
        """
        # Store original MAC
        if not self.original_mac:
            self.original_mac = self.get_current_mac()
        
        # Validate MAC format
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', new_mac):
            return False, "Invalid MAC address format"
        
        # Disable interface
        print(f"Disabling interface {self.interface}...")
        if not self._disable_interface():
            return False, "Failed to disable interface"
        
        # Set new MAC in registry
        print(f"Setting new MAC: {new_mac}")
        if not self._set_mac_registry(new_mac):
            self._enable_interface()
            return False, "Failed to set MAC in registry"
        
        # Re-enable interface
        print(f"Re-enabling interface {self.interface}...")
        if not self._enable_interface():
            return False, "Failed to re-enable interface"
        
        # Verify change
        time.sleep(2)
        current = self.get_current_mac()
        new_mac_normalized = new_mac.upper().replace('-', ':')
        
        if current and current.upper() == new_mac_normalized:
            self.current_mac = current
            return True, f"MAC changed successfully to {current}"
        else:
            return False, f"MAC change may have failed. Current MAC: {current}"
    
    def restore_mac(self) -> Tuple[bool, str]:
        """Restore the original MAC address"""
        if not self.original_mac:
            return False, "Original MAC not stored"
        
        # Disable interface
        self._disable_interface()
        
        # Remove custom MAC from registry
        self._remove_mac_registry()
        
        # Re-enable interface
        self._enable_interface()
        
        time.sleep(2)
        current = self.get_current_mac()
        
        return True, f"MAC restored. Current MAC: {current}"
    
    def apply_profile(self, profile: DeviceProfile) -> Tuple[bool, str]:
        """
        Apply a device profile (MAC + hostname)
        
        Args:
            profile: Device profile to apply
            
        Returns:
            Tuple of (success, message)
        """
        new_mac = profile.generate_mac()
        success, msg = self.change_mac(new_mac)
        
        if success:
            # Also change hostname
            from .hostname_changer import change_hostname
            change_hostname(profile.hostname)
            return True, f"Applied profile '{profile.name}' with MAC {new_mac}"
        
        return success, msg


def change_mac(interface: str, new_mac: str) -> Tuple[bool, str]:
    """Quick function to change MAC address"""
    changer = MACChanger(interface)
    return changer.change_mac(new_mac)


def restore_mac(interface: str) -> Tuple[bool, str]:
    """Quick function to restore original MAC"""
    changer = MACChanger(interface)
    return changer.restore_mac()


def apply_random_profile(interface: str) -> Tuple[bool, str]:
    """Apply a random device profile to the interface"""
    changer = MACChanger(interface)
    profile = get_random_profile()
    return changer.apply_profile(profile)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MAC Address Changer")
    parser.add_argument("--interface", "-i", required=True, help="Network interface name")
    parser.add_argument("--mac", "-m", help="New MAC address")
    parser.add_argument("--profile", "-p", help="Device profile ID to apply")
    parser.add_argument("--random", "-r", action="store_true", help="Apply random profile")
    parser.add_argument("--restore", action="store_true", help="Restore original MAC")
    parser.add_argument("--show", "-s", action="store_true", help="Show current MAC")
    parser.add_argument("--list-profiles", "-l", action="store_true", help="List available profiles")
    
    args = parser.parse_args()
    
    if args.list_profiles:
        profiles = DeviceProfiles()
        print(json.dumps([p.to_dict() for p in profiles.get_all()], indent=2))
        sys.exit(0)
    
    changer = MACChanger(args.interface)
    
    if args.show:
        mac = changer.get_current_mac()
        print(json.dumps({"interface": args.interface, "mac": mac}))
    
    elif args.restore:
        success, msg = changer.restore_mac()
        print(json.dumps({"success": success, "message": msg}))
    
    elif args.random:
        success, msg = apply_random_profile(args.interface)
        print(json.dumps({"success": success, "message": msg}))
    
    elif args.profile:
        profiles = DeviceProfiles()
        profile = profiles.get_by_id(args.profile)
        if profile:
            success, msg = changer.apply_profile(profile)
            print(json.dumps({"success": success, "message": msg, "profile": profile.to_dict()}))
        else:
            print(json.dumps({"success": False, "message": f"Profile '{args.profile}' not found"}))
    
    elif args.mac:
        success, msg = changer.change_mac(args.mac)
        print(json.dumps({"success": success, "message": msg}))
    
    else:
        parser.print_help()
