"""Stealth modules for Network Monitor"""

from .mac_changer import MACChanger, change_mac, restore_mac
from .device_profiles import DeviceProfiles, get_random_profile
from .hostname_changer import change_hostname, get_hostname
