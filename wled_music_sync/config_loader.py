"""Module for managing WLED controller configuration."""
from typing import Dict, List
import os
import yaml
import logging
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)

@dataclass
class ControllerConfig:
    """Configuration for a WLED controller."""
    urls: List[str]
    description: str
    type: str

def load_controller_config(config_path: str = None) -> Dict[str, ControllerConfig]:
    """
    Load controller configuration from YAML file.
    
    Args:
        config_path: Path to the controllers.yml file. If None, will look in default locations.
        
    Returns:
        Dictionary mapping controller IDs to their configurations.
    """
    if config_path is None:
        # Look in common locations
        potential_paths = [
            "config/controllers.yml",
            "controllers.yml",
            "../config/controllers.yml",
        ]
        for path in potential_paths:
            if os.path.exists(path):
                config_path = path
                break
        else:
            raise FileNotFoundError("Could not find controllers.yml in any standard location")

    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            LOGGER.error(f"Error parsing controllers.yml: {e}")
            raise

    if not config or 'controllers' not in config:
        raise ValueError("Invalid controllers.yml: missing 'controllers' section")

    controller_configs: Dict[str, ControllerConfig] = {}
    
    for controller_id, details in config['controllers'].items():
        if not isinstance(details, dict):
            LOGGER.warning(f"Skipping invalid controller config for {controller_id}")
            continue
            
        # Validate required fields
        if 'urls' not in details:
            LOGGER.warning(f"Controller {controller_id} missing 'urls' field")
            continue
            
        # Create controller config
        controller_configs[controller_id] = ControllerConfig(
            urls=details['urls'] if isinstance(details['urls'], list) else [details['urls']],
            description=details.get('description', ''),
            type=details.get('type', 'WLED')
        )
        
    return controller_configs
