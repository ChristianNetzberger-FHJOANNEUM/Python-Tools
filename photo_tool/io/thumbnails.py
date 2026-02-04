"""
Thumbnail generation and caching
"""

import hashlib
from pathlib import Path
from typing import Tuple

from PIL import Image

from ..util.logging import get_logger


logger = get_logger("thumbnails")


def generate_thumbnail(
    image_path: Path,
    cache_dir: Path,
    size: Tuple[int, int] = (256, 256),
    force_regenerate: bool = False
) -> Path:
    """
    Generate and cache thumbnail for image
    
    Args:
        image_path: Source image path
        cache_dir: Directory to store thumbnails
        size: Thumbnail size (width, height)
        force_regenerate: Regenerate even if cached
        
    Returns:
        Path to thumbnail file
    """
    # Generate cache filename from source path hash
    path_hash = hashlib.md5(str(image_path).encode()).hexdigest()
    thumb_name = f"{path_hash}_{size[0]}x{size[1]}.jpg"
    thumb_path = cache_dir / thumb_name
    
    # Return cached if exists
    if thumb_path.exists() and not force_regenerate:
        return thumb_path
    
    try:
        # Generate thumbnail
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (e.g., PNG with alpha)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply EXIF orientation
            try:
                exif = img.getexif()
                if exif:
                    orientation = exif.get(0x0112)  # Orientation tag
                    if orientation:
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
            except:
                pass
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save to cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            img.save(thumb_path, "JPEG", quality=85, optimize=True)
        
        logger.debug(f"Generated thumbnail: {thumb_path}")
        return thumb_path
    
    except Exception as e:
        logger.error(f"Error generating thumbnail for {image_path}: {e}")
        raise


def clear_thumbnail_cache(cache_dir: Path) -> int:
    """
    Clear all cached thumbnails
    
    Returns:
        Number of files deleted
    """
    count = 0
    for thumb in cache_dir.glob("*.jpg"):
        thumb.unlink()
        count += 1
    
    logger.info(f"Cleared {count} thumbnails from cache")
    return count
