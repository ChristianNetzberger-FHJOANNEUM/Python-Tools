"""
Extended metadata management (color labels, keywords, etc.)
Extends the basic rating system with additional metadata
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..util.logging import get_logger

logger = get_logger("metadata")


def get_metadata_file(photo_path: Path) -> Path:
    """Get path to metadata JSON file for photo"""
    return photo_path.parent / f".{photo_path.stem}.metadata.json"


def get_metadata(photo_path: Path) -> Dict[str, Any]:
    """
    Get all metadata for a photo
    
    Returns:
        Dict with rating, color, keywords, gps, comment, etc.
    """
    meta_file = get_metadata_file(photo_path)
    
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read metadata for {photo_path}: {e}")
    
    # Return default metadata
    return {
        'rating': 0,
        'color': None,
        'keywords': [],
        'comment': None,
        'gps': None,
        'updated': None
    }


def set_metadata(photo_path: Path, metadata: Dict[str, Any]) -> None:
    """
    Set metadata for a photo
    
    Args:
        photo_path: Path to photo
        metadata: Dict with any of: rating, color, keywords, comment, gps
    """
    meta_file = get_metadata_file(photo_path)
    
    # Load existing metadata
    existing = get_metadata(photo_path)
    
    # Update with new values
    existing.update(metadata)
    existing['updated'] = datetime.now().isoformat()
    
    # Save to file
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)
    
    logger.debug(f"Updated metadata for {photo_path}")


def set_color_label(photo_path: Path, color: Optional[str]) -> None:
    """
    Set color label for a photo (Lightroom-style)
    
    Args:
        photo_path: Path to photo
        color: One of: 'red', 'yellow', 'green', 'blue', 'purple', or None
    """
    valid_colors = {'red', 'yellow', 'green', 'blue', 'purple', None}
    
    if color not in valid_colors:
        raise ValueError(f"Color must be one of {valid_colors}")
    
    set_metadata(photo_path, {'color': color})
    logger.debug(f"Set color label '{color}' for {photo_path}")


def get_color_label(photo_path: Path) -> Optional[str]:
    """
    Get color label for a photo
    
    Returns:
        Color string or None
    """
    metadata = get_metadata(photo_path)
    return metadata.get('color')


def set_keywords(photo_path: Path, keywords: List[str]) -> None:
    """
    Set keywords/tags for a photo
    
    Args:
        photo_path: Path to photo
        keywords: List of keyword strings
    """
    # Deduplicate and clean
    keywords = list(set([k.strip().lower() for k in keywords if k.strip()]))
    
    set_metadata(photo_path, {'keywords': keywords})
    logger.debug(f"Set {len(keywords)} keywords for {photo_path}")


def add_keyword(photo_path: Path, keyword: str) -> None:
    """
    Add a single keyword to a photo
    
    Args:
        photo_path: Path to photo
        keyword: Keyword to add
    """
    metadata = get_metadata(photo_path)
    keywords = metadata.get('keywords', [])
    
    keyword = keyword.strip().lower()
    if keyword and keyword not in keywords:
        keywords.append(keyword)
        set_keywords(photo_path, keywords)


def remove_keyword(photo_path: Path, keyword: str) -> None:
    """
    Remove a keyword from a photo
    
    Args:
        photo_path: Path to photo
        keyword: Keyword to remove
    """
    metadata = get_metadata(photo_path)
    keywords = metadata.get('keywords', [])
    
    keyword = keyword.strip().lower()
    if keyword in keywords:
        keywords.remove(keyword)
        set_keywords(photo_path, keywords)


def get_all_keywords(photo_paths: List[Path]) -> Dict[str, int]:
    """
    Get all unique keywords across multiple photos with counts
    
    Args:
        photo_paths: List of photo paths
        
    Returns:
        Dict of {keyword: count}
    """
    keyword_counts = {}
    
    for photo_path in photo_paths:
        metadata = get_metadata(photo_path)
        keywords = metadata.get('keywords', [])
        
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
    
    return keyword_counts


def migrate_from_rating_file(photo_path: Path) -> None:
    """
    Migrate old .rating.json file to new .metadata.json format
    
    Args:
        photo_path: Path to photo
    """
    rating_file = photo_path.parent / f".{photo_path.stem}.rating.json"
    
    if rating_file.exists():
        try:
            with open(rating_file, 'r', encoding='utf-8') as f:
                rating_data = json.load(f)
            
            # Convert to new format
            metadata = {
                'rating': rating_data.get('rating', 0),
                'comment': rating_data.get('comment'),
                'color': None,
                'keywords': [],
                'gps': None,
                'updated': rating_data.get('updated')
            }
            
            # Write new metadata file
            meta_file = get_metadata_file(photo_path)
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Optionally delete old file
            # rating_file.unlink()
            
            logger.info(f"Migrated rating file for {photo_path}")
        
        except Exception as e:
            logger.warning(f"Could not migrate rating file for {photo_path}: {e}")
