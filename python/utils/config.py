"""
Configuration management for Network Monitor
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def get_config_path() -> Path:
    """Get the configuration directory path"""
    # Check for environment variable override
    if os.environ.get("NETWORK_MONITOR_CONFIG"):
        return Path(os.environ["NETWORK_MONITOR_CONFIG"])
    
    # Default to ./config relative to project root
    return Path(__file__).parent.parent.parent / "config"


def load_config(filename: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file
    
    Args:
        filename: Name of config file (e.g., 'settings.json')
        
    Returns:
        Configuration dictionary
    """
    config_path = get_config_path() / filename
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config {filename}: {e}")
        return {}


def save_config(filename: str, config: Dict[str, Any]) -> bool:
    """
    Save configuration to JSON file
    
    Args:
        filename: Name of config file
        config: Configuration dictionary
        
    Returns:
        True if successful
    """
    config_path = get_config_path() / filename
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving config {filename}: {e}")
        return False


def get_setting(key: str, default: Any = None) -> Any:
    """Get a specific setting from settings.json"""
    settings = load_config("settings.json")
    
    # Support nested keys with dot notation
    keys = key.split('.')
    value = settings
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def set_setting(key: str, value: Any) -> bool:
    """Set a specific setting in settings.json"""
    settings = load_config("settings.json")
    
    keys = key.split('.')
    current = settings
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    return save_config("settings.json", settings)
