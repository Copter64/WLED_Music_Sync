"""Module for managing application paths and media locations."""
import os
from typing import Dict, List, Optional
import yaml
import logging

LOGGER = logging.getLogger(__name__)

class PathConfig:
    """Manages application paths and media locations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize path configuration.
        
        Args:
            config_path: Path to paths.yml file. If None, will look in default locations.
        """
        self.config = self._load_config(config_path)
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from YAML file."""
        if config_path is None:
            potential_paths = [
                "config/paths.yml",
                "paths.yml",
                "../config/paths.yml",
            ]
            for path in potential_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            else:
                LOGGER.warning("No paths.yml found, using defaults")
                return self._default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            LOGGER.error(f"Error loading paths.yml: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "paths": {
                "media": {
                    "songs": "KPopDH",
                    "presets": "presets"
                },
                "config": {
                    "controllers": "config/controllers.yml",
                    "timings": "timings.yml"
                },
                "settings": {
                    "supported_formats": [".mp3", ".wav", ".ogg"]
                }
            }
        }
    
    def get_songs_path(self, collection: Optional[str] = None) -> str:
        """
        Get the absolute path to the songs directory.
        
        Args:
            collection: Optional collection name from paths.collections
            
        Returns:
            Absolute path to the songs directory
        """
        if collection and "collections" in self.config["paths"]:
            path = self.config["paths"]["collections"].get(collection)
            if path:
                return os.path.join(self.base_path, path)
        
        return os.path.join(self.base_path, 
                          self.config["paths"]["media"]["songs"])
    
    def get_presets_path(self) -> str:
        """Get the absolute path to the presets directory."""
        return os.path.join(self.base_path, 
                          self.config["paths"]["media"]["presets"])
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio file formats."""
        return self.config["paths"]["settings"]["supported_formats"]
    
    def get_config_path(self, name: str) -> str:
        """
        Get the absolute path to a config file.
        
        Args:
            name: Name of the config file (e.g., 'controllers', 'timings')
            
        Returns:
            Absolute path to the config file
        """
        path = self.config["paths"]["config"].get(name)
        if not path:
            raise ValueError(f"Unknown config path: {name}")
        return os.path.join(self.base_path, path)

# Create a global instance for easy access
path_config = PathConfig()
