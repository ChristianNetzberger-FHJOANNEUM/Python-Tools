"""
Path utilities for cross-platform compatibility
"""

import os
from pathlib import Path
from typing import List


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, create if needed"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_path(path: str | Path) -> Path:
    """Normalize path for cross-platform compatibility"""
    return Path(path).resolve()


def safe_filename(name: str) -> str:
    """
    Convert string to safe filename (remove special chars)
    
    Args:
        name: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        name = name.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    name = name.strip(' .')
    
    # Ensure not empty
    if not name:
        name = "unnamed"
    
    return name


def get_relative_path(path: Path, base: Path) -> Path:
    """Get relative path from base, or absolute if not under base"""
    try:
        return path.relative_to(base)
    except ValueError:
        return path


def find_files(
    root: Path,
    extensions: List[str],
    recursive: bool = True
) -> List[Path]:
    """
    Find all files with given extensions
    
    Args:
        root: Root directory to search
        extensions: List of extensions (e.g., ['.jpg', '.jpeg'])
        recursive: Search subdirectories
        
    Returns:
        List of matching file paths
    """
    extensions_lower = [ext.lower() for ext in extensions]
    files = []
    
    pattern = "**/*" if recursive else "*"
    
    for item in root.glob(pattern):
        if item.is_file() and item.suffix.lower() in extensions_lower:
            files.append(item)
    
    return sorted(files)
