"""
Media Manager - Manages all media folders across all storage locations
Handles pre-scanning, indexing, and categorization of media folders
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from ..util.logging import get_logger

logger = get_logger("media_manager")


class FolderCategory(Enum):
    """Media folder categories"""
    INTERNAL = "internal"      # Internal HDD/SSD
    USB = "usb"               # USB/External drives
    NETWORK = "network"       # Network shares (NAS, SMB)
    CLOUD = "cloud"           # Cloud storage (mounted)
    OTHER = "other"


@dataclass
class MediaFolder:
    """Represents a media folder with scan metadata"""
    path: str
    name: str
    category: str
    
    # Scan status
    is_scanned: bool = False
    scan_date: Optional[str] = None
    scan_coverage: Optional[Dict[str, float]] = None  # % coverage per analyzer
    
    # Statistics
    total_photos: int = 0
    total_videos: int = 0
    total_audio: int = 0
    total_size_bytes: int = 0
    
    # Volume info (for USB drive detection)
    volume_label: Optional[str] = None
    volume_serial: Optional[str] = None
    
    # Additional metadata
    added_at: Optional[str] = None
    last_accessed: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaFolder':
        """Create from dictionary"""
        return cls(**data)


class MediaManager:
    """
    Top-level media folder manager
    Manages all available media folders across all storage locations
    """
    
    def __init__(self):
        # Store in user's home directory
        self.config_dir = Path.home() / ".photo_tool" / "media"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "media_folders.json"
        
        # Load existing folders
        self._load()
    
    def _load(self):
        """Load media folders from config"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.folders = [MediaFolder.from_dict(f) for f in data.get('folders', [])]
                    logger.info(f"Loaded {len(self.folders)} media folders")
            except Exception as e:
                logger.error(f"Failed to load media folders: {e}")
                self.folders = []
        else:
            self.folders = []
    
    def _save(self):
        """Save media folders to config"""
        try:
            data = {
                'version': '1.0',
                'updated': datetime.now().isoformat(),
                'folders': [f.to_dict() for f in self.folders]
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.folders)} media folders")
        except Exception as e:
            logger.error(f"Failed to save media folders: {e}")
            raise
    
    def list_folders(self) -> List[Dict[str, Any]]:
        """Get all media folders"""
        return [f.to_dict() for f in self.folders]
    
    def get_folder(self, path: str) -> Optional[MediaFolder]:
        """Get media folder by path"""
        path_normalized = str(Path(path).resolve())
        for folder in self.folders:
            if str(Path(folder.path).resolve()) == path_normalized:
                return folder
        return None
    
    def add_folder(
        self,
        path: Path,
        name: Optional[str] = None,
        category: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Add a media folder"""
        try:
            path = Path(path).resolve()
            
            # Check if already exists
            if self.get_folder(str(path)):
                logger.warning(f"Media folder already exists: {path}")
                return False
            
            # Auto-detect category if not provided
            if not category:
                category = self._detect_category(path)
            
            # Get volume info for USB detection
            volume_label, volume_serial = self._get_volume_info(path)
            
            # Create folder entry
            folder = MediaFolder(
                path=str(path),
                name=name or path.name,
                category=category,
                volume_label=volume_label,
                volume_serial=volume_serial,
                added_at=datetime.now().isoformat(),
                scan_coverage={}
            )
            
            self.folders.append(folder)
            self._save()
            
            logger.info(f"Added media folder: {path} ({category})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add media folder: {e}")
            return False
    
    def remove_folder(self, path: str) -> bool:
        """Remove a media folder"""
        try:
            folder = self.get_folder(path)
            if not folder:
                return False
            
            self.folders = [f for f in self.folders if f.path != folder.path]
            self._save()
            
            logger.info(f"Removed media folder: {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to remove media folder: {e}")
            return False
    
    def update_scan_status(
        self,
        path: str,
        is_scanned: bool,
        scan_coverage: Dict[str, float],
        stats: Optional[Dict[str, int]] = None
    ) -> bool:
        """Update scan status for a folder"""
        try:
            folder = self.get_folder(path)
            if not folder:
                return False
            
            folder.is_scanned = is_scanned
            folder.scan_date = datetime.now().isoformat()
            folder.scan_coverage = scan_coverage
            
            if stats:
                folder.total_photos = stats.get('photos', 0)
                folder.total_videos = stats.get('videos', 0)
                folder.total_audio = stats.get('audio', 0)
            
            self._save()
            return True
        
        except Exception as e:
            logger.error(f"Failed to update scan status: {e}")
            return False
    
    def _detect_category(self, path: Path) -> str:
        """Auto-detect folder category based on path"""
        try:
            path_str = str(path).upper()
            
            # Check for network paths
            if path_str.startswith(r'\\') or path_str.startswith('//'):
                return FolderCategory.NETWORK.value
            
            # Check for cloud sync folders
            cloud_indicators = ['DROPBOX', 'ONEDRIVE', 'GOOGLE DRIVE', 'ICLOUD']
            if any(indicator in path_str for indicator in cloud_indicators):
                return FolderCategory.CLOUD.value
            
            # Check drive type (Windows) with win32api if available
            if path.drive:
                try:
                    import win32api
                    drive_type = win32api.GetDriveType(path.drive + '\\')
                    # DRIVE_REMOVABLE = 2, DRIVE_FIXED = 3
                    if drive_type == 2:
                        return FolderCategory.USB.value
                    elif drive_type == 3:
                        return FolderCategory.INTERNAL.value
                except ImportError:
                    pass
            
            return FolderCategory.OTHER.value
        
        except:
            # Fallback if win32api not available
            if len(str(path)) > 3 and str(path)[0].isalpha() and str(path)[1] == ':':
                # Assume C: = internal, others = USB
                drive_letter = str(path)[0].upper()
                if drive_letter == 'C':
                    return FolderCategory.INTERNAL.value
                else:
                    return FolderCategory.USB.value
            
            return FolderCategory.OTHER.value
    
    def _get_volume_info(self, path: Path) -> tuple[Optional[str], Optional[str]]:
        """Get volume label and serial number (for USB drive tracking)"""
        try:
            if not path.drive:
                return None, None
            
            try:
                import win32api
                volume_info = win32api.GetVolumeInformation(path.drive + '\\')
                # Returns: (volume_name, volume_serial, ...)
                return volume_info[0], str(volume_info[1])
            except ImportError:
                # Fallback without win32api
                return None, None
        
        except:
            return None, None
    
    def find_folder_by_volume(self, volume_serial: str) -> Optional[MediaFolder]:
        """Find media folder by volume serial (for USB drive re-detection)"""
        for folder in self.folders:
            if folder.volume_serial == volume_serial:
                return folder
        return None
    
    def get_folders_by_category(self, category: str) -> List[MediaFolder]:
        """Get all folders in a category"""
        return [f for f in self.folders if f.category == category]
    
    def get_available_folders(self) -> List[MediaFolder]:
        """Get folders that are currently accessible"""
        available = []
        for folder in self.folders:
            if Path(folder.path).exists():
                available.append(folder)
        return available
    
    def get_unavailable_folders(self) -> List[MediaFolder]:
        """Get folders that are not currently accessible (e.g., USB unplugged)"""
        unavailable = []
        for folder in self.folders:
            if not Path(folder.path).exists():
                unavailable.append(folder)
        return unavailable
