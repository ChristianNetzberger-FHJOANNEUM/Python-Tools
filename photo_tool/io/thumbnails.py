"""
Thumbnail generation and caching for photos and videos
"""

import hashlib
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image

from ..util.logging import get_logger


logger = get_logger("thumbnails")


# Video extensions
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.wmv', '.flv', '.webm'}


def generate_thumbnail(
    media_path: Path,
    cache_dir: Path,
    size: Tuple[int, int] = (256, 256),
    force_regenerate: bool = False
) -> Path:
    """
    Generate and cache thumbnail for image or video
    
    For videos, extracts the first frame.
    
    Args:
        media_path: Source image/video path
        cache_dir: Directory to store thumbnails
        size: Thumbnail size (width, height)
        force_regenerate: Regenerate even if cached
        
    Returns:
        Path to thumbnail file
    """
    # Check if it's a video
    if media_path.suffix.lower() in VIDEO_EXTENSIONS:
        return _generate_video_thumbnail(media_path, cache_dir, size, force_regenerate)
    else:
        return _generate_image_thumbnail(media_path, cache_dir, size, force_regenerate)


def _generate_image_thumbnail(
    image_path: Path,
    cache_dir: Path,
    size: Tuple[int, int],
    force_regenerate: bool
) -> Path:
    """Generate thumbnail for image file"""
    # Generate cache filename from source path hash
    path_hash = hashlib.md5(str(image_path).encode()).hexdigest()
    thumb_name = f"{path_hash}_{size[0]}x{size[1]}.jpg"
    thumb_path = cache_dir / thumb_name
    
    # Return cached if exists
    if thumb_path.exists() and not force_regenerate:
        return thumb_path
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
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
            img.save(thumb_path, "JPEG", quality=85, optimize=True)
        
        logger.debug(f"Generated thumbnail: {thumb_path}")
        return thumb_path
    
    except Exception as e:
        logger.error(f"Error generating thumbnail for {image_path}: {e}")
        raise


def _generate_video_thumbnail(
    video_path: Path,
    cache_dir: Path,
    size: Tuple[int, int],
    force_regenerate: bool
) -> Path:
    """
    Generate thumbnail for video file by extracting first frame
    
    Args:
        video_path: Source video path
        cache_dir: Directory to store thumbnails
        size: Thumbnail size (width, height)
        force_regenerate: Regenerate even if cached
        
    Returns:
        Path to thumbnail file
    """
    # Generate cache filename
    path_hash = hashlib.md5(str(video_path).encode()).hexdigest()
    thumb_name = f"{path_hash}_{size[0]}x{size[1]}_video.jpg"
    thumb_path = cache_dir / thumb_name
    
    # Return cached if exists
    if thumb_path.exists() and not force_regenerate:
        return thumb_path
    
    try:
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Try to seek to a frame that's not black (first 5 seconds)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            # Try frame at 1 second
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps))
        
        # Read frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            # Try first frame if seeking failed
            cap = cv2.VideoCapture(str(video_path))
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                raise ValueError(f"Could not read frame from video: {video_path}")
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        img = Image.fromarray(frame_rgb)
        
        # Create thumbnail
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save to cache
        cache_dir.mkdir(parents=True, exist_ok=True)
        img.save(thumb_path, "JPEG", quality=85, optimize=True)
        
        logger.debug(f"Generated video thumbnail: {thumb_path}")
        return thumb_path
    
    except Exception as e:
        logger.error(f"Error generating video thumbnail for {video_path}: {e}")
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
