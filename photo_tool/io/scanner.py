"""
File scanner for finding photos
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm

from ..util.paths import find_files
from ..util.logging import get_logger


logger = get_logger("scanner")


@dataclass
class PhotoFile:
    """Basic file information"""
    path: Path
    filename: str
    size_bytes: int
    modified_time: datetime
    extension: str
    
    @classmethod
    def from_path(cls, path: Path) -> "PhotoFile":
        """Create PhotoFile from path"""
        stat = path.stat()
        return cls(
            path=path,
            filename=path.name,
            size_bytes=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            extension=path.suffix.lower()
        )


def scan_directory(
    root: Path,
    extensions: List[str],
    recursive: bool = True,
    show_progress: bool = True
) -> List[PhotoFile]:
    """
    Scan directory for image files
    
    Args:
        root: Root directory to scan
        extensions: File extensions to include
        recursive: Scan subdirectories
        show_progress: Show progress bar
        
    Returns:
        List of PhotoFile objects
    """
    logger.info(f"Scanning directory: {root}")
    logger.info(f"Extensions: {', '.join(extensions)}")
    
    # Find all matching files
    file_paths = find_files(root, extensions, recursive)
    
    logger.info(f"Found {len(file_paths)} files")
    
    # Create PhotoFile objects
    photos = []
    iterator = tqdm(file_paths, desc="Reading file info") if show_progress else file_paths
    
    for path in iterator:
        try:
            photo = PhotoFile.from_path(path)
            photos.append(photo)
        except Exception as e:
            logger.warning(f"Error reading {path}: {e}")
    
    logger.info(f"Successfully indexed {len(photos)} photos")
    
    return photos


def scan_multiple_directories(
    roots: List[Path],
    extensions: List[str],
    recursive: bool = True,
    show_progress: bool = True
) -> List[PhotoFile]:
    """
    Scan multiple directories
    
    Args:
        roots: List of root directories
        extensions: File extensions
        recursive: Scan subdirectories
        show_progress: Show progress bar
        
    Returns:
        Combined list of PhotoFile objects
    """
    all_photos = []
    
    for root in roots:
        if not root.exists():
            logger.warning(f"Directory not found: {root}")
            continue
        
        photos = scan_directory(root, extensions, recursive, show_progress)
        all_photos.extend(photos)
    
    # Remove duplicates by path
    seen = set()
    unique_photos = []
    for photo in all_photos:
        if photo.path not in seen:
            seen.add(photo.path)
            unique_photos.append(photo)
    
    if len(all_photos) != len(unique_photos):
        logger.info(f"Removed {len(all_photos) - len(unique_photos)} duplicate entries")
    
    return unique_photos
