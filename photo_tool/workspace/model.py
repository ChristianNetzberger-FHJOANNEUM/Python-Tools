"""
Workspace data model and directory structure
"""

from dataclasses import dataclass
from pathlib import Path

from ..util.paths import ensure_dir


@dataclass
class Workspace:
    """
    Workspace represents a photo management project
    
    Directory structure:
        root/
            config.yaml           # Configuration
            cache/                # Cached data (thumbnails, hashes)
                thumbnails/
                hashes/
            db/                   # SQLite database
                index.sqlite
            reports/              # Generated reports
            exports/              # Exported/processed images
            logs/                 # Log files
    """
    root: Path
    
    def __post_init__(self):
        self.root = Path(self.root).resolve()
    
    @property
    def config_file(self) -> Path:
        """Path to config.yaml"""
        return self.root / "config.yaml"
    
    @property
    def cache_dir(self) -> Path:
        """Cache directory"""
        return self.root / "cache"
    
    @property
    def thumbnails_dir(self) -> Path:
        """Thumbnails cache"""
        return self.cache_dir / "thumbnails"
    
    @property
    def hashes_dir(self) -> Path:
        """Perceptual hashes cache"""
        return self.cache_dir / "hashes"
    
    @property
    def db_dir(self) -> Path:
        """Database directory"""
        return self.root / "db"
    
    @property
    def db_file(self) -> Path:
        """SQLite database file"""
        return self.db_dir / "index.sqlite"
    
    @property
    def reports_dir(self) -> Path:
        """Reports output directory"""
        return self.root / "reports"
    
    @property
    def exports_dir(self) -> Path:
        """Exports directory for processed images"""
        return self.root / "exports"
    
    @property
    def logs_dir(self) -> Path:
        """Logs directory"""
        return self.root / "logs"
    
    def ensure_structure(self) -> None:
        """Create all workspace directories"""
        ensure_dir(self.root)
        ensure_dir(self.cache_dir)
        ensure_dir(self.thumbnails_dir)
        ensure_dir(self.hashes_dir)
        ensure_dir(self.db_dir)
        ensure_dir(self.reports_dir)
        ensure_dir(self.exports_dir)
        ensure_dir(self.logs_dir)
    
    def exists(self) -> bool:
        """Check if workspace exists and is valid"""
        return (
            self.root.exists() and
            self.root.is_dir() and
            self.config_file.exists()
        )
