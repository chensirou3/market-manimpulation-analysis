"""
Path management utilities for the manipulation detection toolkit.

This module provides functions to reliably locate project directories
regardless of where scripts are executed from.
"""

from pathlib import Path
from typing import Optional
import yaml


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    This function locates the project root by searching for the presence
    of key files (config.yaml, requirements.txt) in parent directories.
    
    Returns:
        Path: Absolute path to the project root directory.
        
    Raises:
        RuntimeError: If project root cannot be determined.
        
    Examples:
        >>> root = get_project_root()
        >>> print(root)
        /path/to/market
    """
    # Start from the current file's directory
    current = Path(__file__).resolve()
    
    # Traverse up to find project root (contains requirements.txt)
    for parent in [current] + list(current.parents):
        if (parent / "requirements.txt").exists():
            return parent
        if (parent / "src" / "config" / "config.yaml").exists():
            return parent
    
    # Fallback: assume we're in src/utils, go up two levels
    fallback = current.parent.parent.parent
    if fallback.exists():
        return fallback
    
    raise RuntimeError(
        "Could not determine project root. "
        "Make sure you're running from within the project directory."
    )


def get_config_path() -> Path:
    """
    Get the path to the main configuration file.
    
    Returns:
        Path: Absolute path to config.yaml.
        
    Examples:
        >>> config_path = get_config_path()
        >>> print(config_path)
        /path/to/market/src/config/config.yaml
    """
    return get_project_root() / "src" / "config" / "config.yaml"


def load_config() -> dict:
    """
    Load the configuration from config.yaml.
    
    Returns:
        dict: Configuration dictionary.
        
    Raises:
        FileNotFoundError: If config.yaml doesn't exist.
        yaml.YAMLError: If config.yaml is malformed.
        
    Examples:
        >>> config = load_config()
        >>> print(config['data']['data_dir'])
        ./data
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_data_dir(create_if_missing: bool = True) -> Path:
    """
    Get the data directory path from configuration.
    
    Args:
        create_if_missing: If True, create the directory if it doesn't exist.
        
    Returns:
        Path: Absolute path to the data directory.
        
    Examples:
        >>> data_dir = get_data_dir()
        >>> print(data_dir)
        /path/to/market/data
    """
    config = load_config()
    data_dir_str = config.get('data', {}).get('data_dir', './data')
    
    # Convert to absolute path
    if data_dir_str.startswith('.'):
        data_dir = get_project_root() / data_dir_str.lstrip('./')
    else:
        data_dir = Path(data_dir_str)
    
    # Create if requested
    if create_if_missing and not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir


def get_output_dir(subdir: Optional[str] = None, create_if_missing: bool = True) -> Path:
    """
    Get an output directory within the data directory.
    
    Args:
        subdir: Optional subdirectory name (e.g., 'processed', 'results').
        create_if_missing: If True, create the directory if it doesn't exist.
        
    Returns:
        Path: Absolute path to the output directory.
        
    Examples:
        >>> output_dir = get_output_dir('processed')
        >>> print(output_dir)
        /path/to/market/data/processed
    """
    data_dir = get_data_dir(create_if_missing=create_if_missing)
    
    if subdir:
        output_dir = data_dir / subdir
        if create_if_missing and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    return data_dir


if __name__ == "__main__":
    # Demo usage
    print("Project Root:", get_project_root())
    print("Config Path:", get_config_path())
    print("Data Directory:", get_data_dir())
    print("Output Directory (processed):", get_output_dir('processed'))
    
    # Load and display config
    config = load_config()
    print("\nConfiguration loaded successfully!")
    print(f"Bar timeframe: {config['bars']['timeframe']}")
    print(f"Simulation days: {config['simulation']['n_days']}")

