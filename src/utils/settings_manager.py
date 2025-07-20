"""Settings manager for the DJ Library Organizer application."""

import os
import json
import logging
from pathlib import Path
import sys
import importlib

logger = logging.getLogger(__name__)

class SettingsManager:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            # Only initialize once
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.app_data_dir = os.path.join(os.environ.get('APPDATA', '.'), 'PulzWaveDJLibraryOrganizer')
        self.settings_file = os.path.join(self.app_data_dir, 'settings.json')
        self.settings = self._get_default_settings()
        self._initialized = True
    
    def _get_default_settings(self):
        """Get default settings from config.py."""
        # Dynamically import config.py from the parent directory
        config = importlib.import_module('config')
        return {
            "CUSTOM_ID3_TAG": getattr(config, 'DEFAULT_CUSTOM_ID3_TAG', ""),
            "POPM_EMAIL": getattr(config, 'DEFAULT_POPM_EMAIL', ""),
            "GENRE_LIST": getattr(config, 'DEFAULT_GENRE_LIST', [""]),
            "NUM_THREADS": getattr(config, 'DEFAULT_NUM_THREADS', 4),
            "ENGINE_DB_PATH": getattr(config, 'DEFAULT_ENGINE_DB_PATH', ""),
            "DJ_POOL_FOLDER_NAME": getattr(config, 'DEFAULT_DJ_POOL_FOLDER_NAME', ""),
            "API_URL": getattr(config, 'DEFAULT_API_URL', ""),
            "API_ENABLED": getattr(config, 'DEFAULT_API_ENABLED', False)
        }
    
    def load_settings(self):
        """Load settings from file."""
        try:
            # Ensure directory exists
            os.makedirs(self.app_data_dir, exist_ok=True)
            
            # Check if settings file exists
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Update settings with loaded values, keeping defaults for any missing keys
                    self.settings.update(loaded_settings)
                logger.info(f"Settings loaded from {self.settings_file}")
                return True
            else:
                logger.info("Settings file not found, using defaults")
                return False
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return False
    
    def save_settings(self):
        """Save settings to file."""
        try:
            # Ensure directory exists
            os.makedirs(self.app_data_dir, exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            
            logger.info(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
    
    def get_all(self):
        """Get all settings."""
        return self.settings
    
    def settings_exist(self):
        """Check if settings file exists."""
        return os.path.exists(self.settings_file)