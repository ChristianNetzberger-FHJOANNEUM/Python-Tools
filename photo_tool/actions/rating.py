"""
Photo rating system (XMP sidecars)
"""

import json
from pathlib import Path
from typing import Optional

from ..util.logging import get_logger


logger = get_logger("rating")


def get_rating_file(photo_path: Path) -> Path:
    """Get path to rating JSON file for photo"""
    return photo_path.parent / f".{photo_path.stem}.rating.json"


def set_rating(photo_path: Path, rating: int, comment: Optional[str] = None) -> None:
    """
    Set rating for a photo (0-5 stars)
    
    Stores in JSON sidecar file
    
    Args:
        photo_path: Path to photo
        rating: Rating value (0-5)
        comment: Optional comment
    """
    if not 0 <= rating <= 5:
        raise ValueError("Rating must be between 0 and 5")
    
    rating_file = get_rating_file(photo_path)
    
    data = {
        'photo': photo_path.name,
        'rating': rating,
        'comment': comment,
        'updated': str(Path(photo_path).stat().st_mtime)
    }
    
    with open(rating_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.debug(f"Set rating {rating} for {photo_path}")


def get_rating(photo_path: Path) -> Optional[int]:
    """
    Get rating for a photo
    
    Returns:
        Rating (0-5) or None if not rated
    """
    rating_file = get_rating_file(photo_path)
    
    if not rating_file.exists():
        return None
    
    try:
        with open(rating_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('rating')
    except Exception as e:
        logger.warning(f"Could not read rating for {photo_path}: {e}")
        return None


def get_rating_with_comment(photo_path: Path) -> tuple[Optional[int], Optional[str]]:
    """
    Get rating and comment
    
    Returns:
        (rating, comment) tuple
    """
    rating_file = get_rating_file(photo_path)
    
    if not rating_file.exists():
        return (None, None)
    
    try:
        with open(rating_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return (data.get('rating'), data.get('comment'))
    except Exception as e:
        logger.warning(f"Could not read rating for {photo_path}: {e}")
        return (None, None)
