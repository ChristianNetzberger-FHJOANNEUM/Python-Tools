"""
Sidecar file management for storing photo analysis results
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from photo_tool.util.logging import get_logger

logger = get_logger("sidecar")


class SidecarManager:
    """
    Manages .phototool.json sidecar files
    Stores all analysis results next to the photo
    """
    
    SIDECAR_SUFFIX = ".phototool.json"
    VERSION = "1.0"
    
    def __init__(self, photo_path: Path):
        self.photo_path = Path(photo_path)
        self.sidecar_path = Path(str(photo_path) + self.SIDECAR_SUFFIX)
        self._data = None
    
    @property
    def exists(self) -> bool:
        """Check if sidecar exists"""
        return self.sidecar_path.exists()
    
    def load(self) -> Dict[str, Any]:
        """Load sidecar data"""
        if not self.exists:
            self._data = self._create_empty()
            return self._data
        
        try:
            with open(self.sidecar_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure it's a valid dictionary
                if not isinstance(data, dict):
                    logger.warning(f"Invalid sidecar data for {self.photo_path}, recreating")
                    self._data = self._create_empty()
                else:
                    self._data = data
            return self._data
        
        except Exception as e:
            logger.error(f"Failed to load sidecar for {self.photo_path}: {e}")
            self._data = self._create_empty()
            return self._data
    
    def save(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """Save sidecar data"""
        if data:
            self._data = data
        
        # Ensure _data exists and is valid
        if not self._data or not isinstance(self._data, dict):
            logger.warning(f"No valid data to save for {self.photo_path}")
            return False
        
        try:
            # Ensure scan_info exists
            if 'scan_info' not in self._data or not isinstance(self._data['scan_info'], dict):
                self._data['scan_info'] = {
                    'scanned_at': datetime.now().isoformat(),
                    'scanner_version': '1.0.0',
                    'updated_at': datetime.now().isoformat()
                }
            
            # Update metadata
            self._data['scan_info']['updated_at'] = datetime.now().isoformat()
            
            with open(self.sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save sidecar for {self.photo_path}: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Get value from sidecar using dot notation (e.g., 'blur.laplacian.score')"""
        if not self._data:
            self.load()
        
        keys = key.split('.')
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value in sidecar using dot notation"""
        if not self._data:
            self.load()
        
        keys = key.split('.')
        data = self._data
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        # Set value
        data[keys[-1]] = value
    
    def update_analysis(self, analyzer_name: str, results: Dict[str, Any]) -> None:
        """Update analysis results"""
        if not self._data:
            self.load()
        
        if 'analyses' not in self._data:
            self._data['analyses'] = {}
        
        self._data['analyses'][analyzer_name] = {
            **results,
            'computed_at': datetime.now().isoformat()
        }
    
    def is_stale(self) -> bool:
        """Check if sidecar is outdated (photo modified after scan)"""
        if not self.exists:
            return True
        
        try:
            photo_mtime = self.photo_path.stat().st_mtime
            scan_date = self.get('scan_info.scanned_at')
            
            if not scan_date:
                return True
            
            scan_dt = datetime.fromisoformat(scan_date)
            scan_timestamp = scan_dt.timestamp()
            
            return photo_mtime > scan_timestamp
        
        except:
            return True
    
    def _create_empty(self) -> Dict[str, Any]:
        """Create empty sidecar structure"""
        return {
            'version': self.VERSION,
            'photo': {
                'path': str(self.photo_path),
                'name': self.photo_path.name,
                'size_bytes': self.photo_path.stat().st_size if self.photo_path.exists() else 0,
                'modified_at': datetime.fromtimestamp(self.photo_path.stat().st_mtime).isoformat() if self.photo_path.exists() else None
            },
            'scan_info': {
                'scanned_at': datetime.now().isoformat(),
                'scanner_version': '1.0.0',
                'updated_at': datetime.now().isoformat()
            },
            'analyses': {}
        }
    
    @classmethod
    def get_sidecar_path(cls, photo_path: Path) -> Path:
        """Get sidecar path for a photo"""
        return Path(str(photo_path) + cls.SIDECAR_SUFFIX)
    
    @classmethod
    def has_sidecar(cls, photo_path: Path) -> bool:
        """Check if photo has a sidecar"""
        return cls.get_sidecar_path(photo_path).exists()
