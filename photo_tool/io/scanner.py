"""
File scanner for finding photos and videos
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal

from tqdm import tqdm

from ..util.paths import find_files
from ..util.logging import get_logger


logger = get_logger("scanner")


# Media type detection
PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.wmv', '.flv', '.webm', '.mts', '.m2ts'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.wma', '.aiff', '.alac'}


@dataclass
class MediaFile:
    """Basic file information for photos, videos, and audio"""
    path: Path
    filename: str
    size_bytes: int
    modified_time: datetime
    extension: str
    media_type: Literal["photo", "video", "audio", "unknown"]
    
    @classmethod
    def from_path(cls, path: Path) -> "MediaFile":
        """Create MediaFile from path"""
        stat = path.stat()
        ext = path.suffix.lower()
        
        # Determine media type
        if ext in PHOTO_EXTENSIONS:
            media_type = "photo"
        elif ext in VIDEO_EXTENSIONS:
            media_type = "video"
        elif ext in AUDIO_EXTENSIONS:
            media_type = "audio"
        else:
            media_type = "unknown"
        
        return cls(
            path=path,
            filename=path.name,
            size_bytes=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            extension=ext,
            media_type=media_type
        )
    
    @property
    def is_photo(self) -> bool:
        """Check if this is a photo"""
        return self.media_type == "photo"
    
    @property
    def is_video(self) -> bool:
        """Check if this is a video"""
        return self.media_type == "video"
    
    @property
    def is_audio(self) -> bool:
        """Check if this is an audio file"""
        return self.media_type == "audio"


# Backwards compatibility alias
PhotoFile = MediaFile


def scan_directory(
    root: Path,
    extensions: List[str],
    recursive: bool = True,
    show_progress: bool = True
) -> List[MediaFile]:
    """
    Scan directory for media files (photos and videos)
    
    Args:
        root: Root directory to scan
        extensions: File extensions to include
        recursive: Scan subdirectories
        show_progress: Show progress bar
        
    Returns:
        List of MediaFile objects
    """
    logger.info(f"Scanning directory: {root}")
    logger.info(f"Extensions: {', '.join(extensions)}")
    
    # Find all matching files
    file_paths = find_files(root, extensions, recursive)
    
    logger.info(f"Found {len(file_paths)} files")
    
    # Create MediaFile objects
    media_files = []
    iterator = tqdm(file_paths, desc="Reading file info") if show_progress else file_paths
    
    for path in iterator:
        try:
            media_file = MediaFile.from_path(path)
            media_files.append(media_file)
        except Exception as e:
            logger.warning(f"Error reading {path}: {e}")
    
    # Count by type
    photos = sum(1 for m in media_files if m.is_photo)
    videos = sum(1 for m in media_files if m.is_video)
    audio = sum(1 for m in media_files if m.is_audio)
    
    logger.info(f"Successfully indexed {len(media_files)} files ({photos} photos, {videos} videos, {audio} audio)")
    
    return media_files


def scan_multiple_directories(
    roots: List[Path],
    extensions: List[str],
    recursive: bool = True,
    show_progress: bool = True
) -> List[MediaFile]:
    """
    Scan multiple directories
    
    Args:
        roots: List of root directories
        extensions: File extensions
        recursive: Scan subdirectories
        show_progress: Show progress bar
        
    Returns:
        Combined list of MediaFile objects
    """
    all_media = []
    
    for root in roots:
        if not root.exists():
            logger.warning(f"Directory not found: {root}")
            continue
        
        media = scan_directory(root, extensions, recursive, show_progress)
        all_media.extend(media)
    
    # Remove duplicates by path
    seen = set()
    unique_media = []
    for media in all_media:
        if media.path not in seen:
            seen.add(media.path)
            unique_media.append(media)
    
    if len(all_media) != len(unique_media):
        logger.info(f"Removed {len(all_media) - len(unique_media)} duplicate entries")
    
    return unique_media


def filter_by_type(
    media_files: List[MediaFile],
    media_type: Literal["photo", "video", "audio", "all"] = "all"
) -> List[MediaFile]:
    """
    Filter media files by type
    
    Args:
        media_files: List of media files
        media_type: Type to filter ('photo', 'video', 'audio', 'all')
        
    Returns:
        Filtered list
    """
    if media_type == "all":
        return media_files
    elif media_type == "photo":
        return [m for m in media_files if m.is_photo]
    elif media_type == "video":
        return [m for m in media_files if m.is_video]
    elif media_type == "audio":
        return [m for m in media_files if m.is_audio]
    else:
        raise ValueError(f"Unknown media type: {media_type}")
