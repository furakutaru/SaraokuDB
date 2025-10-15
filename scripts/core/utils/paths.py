"""Utility functions for handling file paths."""
from pathlib import Path
from typing import Optional, Union

from ..config import (
    BASE_DIR, CACHE_DIR, OUTPUT_DIR, LOG_DIR
)

def get_cache_path(filename: str, subdir: Optional[str] = None) -> Path:
    """Get path to a cache file.
    
    Args:
        filename: Name of the cache file
        subdir: Optional subdirectory within the cache directory
        
    Returns:
        Path: Full path to the cache file
    """
    if subdir:
        cache_dir = CACHE_DIR / subdir
        cache_dir.mkdir(exist_ok=True, parents=True)
        return cache_dir / filename
    return CACHE_DIR / filename

def get_output_path(filename: str, subdir: Optional[str] = None) -> Path:
    """Get path to an output file.
    
    Args:
        filename: Name of the output file
        subdir: Optional subdirectory within the output directory
        
    Returns:
        Path: Full path to the output file
    """
    if subdir:
        output_dir = OUTPUT_DIR / subdir
        output_dir.mkdir(exist_ok=True, parents=True)
        return output_dir / filename
    return OUTPUT_DIR / filename

def get_log_path(filename: str) -> Path:
    """Get path to a log file.
    
    Args:
        filename: Name of the log file
        
    Returns:
        Path: Full path to the log file
    """
    LOG_DIR.mkdir(exist_ok=True, parents=True)
    return LOG_DIR / filename

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure that the directory exists.
    
    Args:
        path: Path to a directory or file
        
    Returns:
        Path: The input path as a Path object
    """
    path = Path(path)
    if path.suffix:  # It's a file
        path.parent.mkdir(exist_ok=True, parents=True)
    else:  # It's a directory
        path.mkdir(exist_ok=True, parents=True)
    return path
