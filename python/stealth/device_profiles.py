"""
Device profiles for MAC address spoofing
Each profile makes your PC appear as a different device type
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class DeviceProfile:
    """Represents a fake device identity"""
    id: str
    name: str
    mac_prefix: str
    hostname: str
    description: str
    
    def generate_mac(self) -> str:
        """Generate a full MAC address with this profile's prefix"""
        prefix_parts = self.mac_prefix.split(':')
        # Generate random suffix
        suffix = [format(random.randint(0, 255), '02x') for _ in range(6 - len(prefix_parts))]
        return ':'.join(prefix_parts + suffix).upper()
    
    def to_dict(self) -> Dict:
        return asdict(self)


# Built-in device profiles
DEFAULT_PROFILES = [
    DeviceProfile(
        id="hp_printer",
        name="HP Printer",
        mac_prefix="00:1A:2B",
        hostname="HP-LaserJet-Pro",
        description="Appears as HP LaserJet printer"
    ),
    DeviceProfile(
        id="samsung_tv",
        name="Samsung Smart TV",
        mac_prefix="00:1E:A6",
        hostname="Samsung-TV",
        description="Appears as Samsung television"
    ),
    DeviceProfile(
        id="google_nest",
        name="Google Nest Hub",
        mac_prefix="F4:F5:D8",
        hostname="Google-Home-Mini",
        description="Appears as Google smart speaker"
    ),
    DeviceProfile(
        id="amazon_echo",
        name="Amazon Echo",
        mac_prefix="FC:A1:83",
        hostname="Echo-Dot-3rd-Gen",
        description="Appears as Amazon Alexa device"
    ),
    DeviceProfile(
        id="apple_tv",
        name="Apple TV",
        mac_prefix="40:CB:C0",
        hostname="Apple-TV",
        description="Appears as Apple TV streaming device"
    ),
    DeviceProfile(
        id="philips_hue",
        name="Philips Hue Bridge",
        mac_prefix="00:17:88",
        hostname="Philips-hue",
        description="Appears as smart light bridge"
    ),
    DeviceProfile(
        id="ring_doorbell",
        name="Ring Doorbell",
        mac_prefix="34:3E:A4",
        hostname="Ring-Video-Doorbell",
        description="Appears as Ring security camera"
    ),
    DeviceProfile(
        id="roku",
        name="Roku Ultra",
        mac_prefix="84:EA:ED",
        hostname="Roku-Ultra",
        description="Appears as Roku streaming device"
    ),
    DeviceProfile(
        id="nest_thermostat",
        name="Nest Thermostat",
        mac_prefix="64:16:66",
        hostname="Nest-Learning-Thermostat",
        description="Appears as Nest smart thermostat"
    ),
    DeviceProfile(
        id="sonos_speaker",
        name="Sonos Speaker",
        mac_prefix="00:0E:58",
        hostname="Sonos-One",
        description="Appears as Sonos smart speaker"
    ),
]


class DeviceProfiles:
    """Manage device profiles for MAC spoofing"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.profiles: List[DeviceProfile] = list(DEFAULT_PROFILES)
        self.config_path = config_path or Path(__file__).parent.parent.parent / "config" / "device_profiles.json"
        self.current_profile: Optional[DeviceProfile] = None
        self._load_custom_profiles()
    
    def _load_custom_profiles(self):
        """Load custom profiles from config file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    
                # Add custom profiles
                for p in data.get('custom_profiles', []):
                    self.profiles.append(DeviceProfile(**p))
                
                # Set current profile if saved
                current_id = data.get('current_profile')
                if current_id:
                    self.current_profile = self.get_by_id(current_id)
                    
            except (json.JSONDecodeError, IOError):
                pass
    
    def save_config(self):
        """Save current configuration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "profiles": [p.to_dict() for p in DEFAULT_PROFILES],
            "custom_profiles": [
                p.to_dict() for p in self.profiles 
                if p not in DEFAULT_PROFILES
            ],
            "current_profile": self.current_profile.id if self.current_profile else None,
            "auto_rotate": False,
            "rotate_interval_hours": 24
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_all(self) -> List[DeviceProfile]:
        """Get all available profiles"""
        return self.profiles
    
    def get_by_id(self, profile_id: str) -> Optional[DeviceProfile]:
        """Get profile by ID"""
        for p in self.profiles:
            if p.id == profile_id:
                return p
        return None
    
    def get_random(self) -> DeviceProfile:
        """Get a random profile"""
        return random.choice(self.profiles)
    
    def add_custom(self, profile: DeviceProfile):
        """Add a custom profile"""
        self.profiles.append(profile)
        self.save_config()
    
    def set_current(self, profile: DeviceProfile):
        """Set the current active profile"""
        self.current_profile = profile
        self.save_config()


def get_random_profile() -> DeviceProfile:
    """Quick function to get a random device profile"""
    return DeviceProfiles().get_random()


def get_profile_by_id(profile_id: str) -> Optional[DeviceProfile]:
    """Get a specific profile by ID"""
    return DeviceProfiles().get_by_id(profile_id)
