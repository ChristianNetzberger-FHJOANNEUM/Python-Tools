"""
Configuration loading and saving
"""

from pathlib import Path
from typing import Optional

import yaml

from .schema import PhotoToolConfig
from ..util.logging import get_logger


logger = get_logger("config")


def load_config(config_path: Optional[Path] = None) -> PhotoToolConfig:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config.yaml (optional)
        
    Returns:
        Validated configuration object
    """
    # Default config
    defaults_path = Path(__file__).parent / "defaults.yaml"
    
    with open(defaults_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    # Override with user config if provided
    if config_path and config_path.exists():
        logger.info(f"Loading config from {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f)
            
        # Deep merge
        config_dict = _merge_dicts(config_dict, user_config)
    elif config_path:
        logger.warning(f"Config file not found: {config_path}, using defaults")
    
    # Validate and return
    try:
        return PhotoToolConfig(**config_dict)
    except Exception as e:
        logger.error(f"Invalid configuration: {e}")
        raise


def save_config(config: PhotoToolConfig, config_path: Path) -> None:
    """
    Save configuration to YAML file
    
    Args:
        config: Configuration object
        config_path: Output path
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    config_dict = config.model_dump(mode='python')
    
    # Convert Path objects to strings for YAML
    config_dict = _paths_to_strings(config_dict)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Configuration saved to {config_path}")


def _merge_dicts(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def _paths_to_strings(obj):
    """Convert Path objects to strings recursively"""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _paths_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_paths_to_strings(item) for item in obj]
    else:
        return obj
