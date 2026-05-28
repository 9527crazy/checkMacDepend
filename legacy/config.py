"""
Configuration management for Package Monitor
"""
import os
import json
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "scan_interval_hours": 24,
    "storage_dir": os.path.expanduser("~/.pkg-monitor"),
    "records_file": "records.json",
    "reports_dir": "reports",
    "auto_scan_on_startup": True,
    "show_notifications": True,
    "enabled_managers": [
        "homebrew",
        "pip",
        "npm",
        "cargo",
        "gem",
        "go"
    ]
}


class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = os.path.expanduser("~/.pkg-monitor/config.json")
        else:
            self.config_path = config_path
        
        self.config = DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        
        # Ensure storage directory exists
        os.makedirs(self.config["storage_dir"], exist_ok=True)
        os.makedirs(os.path.join(self.config["storage_dir"], self.config["reports_dir"]), exist_ok=True)
    
    def save(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key, default=None):
        """Get config value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set config value"""
        self.config[key] = value
    
    @property
    def records_path(self):
        """Get full path to records file"""
        return os.path.join(self.config["storage_dir"], self.config["records_file"])
    
    @property
    def reports_path(self):
        """Get full path to reports directory"""
        return os.path.join(self.config["storage_dir"], self.config["reports_dir"])
