"""
Simple SQLite database for photo indexing
(Future: For now, we'll work with in-memory data structures)
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..util.logging import get_logger


logger = get_logger("db")


@dataclass
class PhotoRecord:
    """Photo metadata record"""
    id: Optional[int] = None
    path: str = ""
    filename: str = ""
    size_bytes: int = 0
    modified_time: Optional[datetime] = None
    captured_time: Optional[datetime] = None
    width: int = 0
    height: int = 0
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    focal_length: Optional[float] = None
    aperture: Optional[float] = None
    iso: Optional[int] = None
    shutter_speed: Optional[str] = None
    phash: Optional[str] = None
    blur_score: Optional[float] = None
    indexed_time: Optional[datetime] = None


class PhotoDatabase:
    """Simple SQLite wrapper for photo metadata"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    size_bytes INTEGER,
                    modified_time TIMESTAMP,
                    captured_time TIMESTAMP,
                    width INTEGER,
                    height INTEGER,
                    camera_model TEXT,
                    lens_model TEXT,
                    focal_length REAL,
                    aperture REAL,
                    iso INTEGER,
                    shutter_speed TEXT,
                    phash TEXT,
                    blur_score REAL,
                    indexed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_captured_time ON photos(captured_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON photos(path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phash ON photos(phash)")
            
            conn.commit()
        
        logger.debug(f"Database initialized: {self.db_path}")
    
    def insert_photo(self, photo: PhotoRecord) -> int:
        """Insert or update photo record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO photos 
                (path, filename, size_bytes, modified_time, captured_time,
                 width, height, camera_model, lens_model, focal_length,
                 aperture, iso, shutter_speed, phash, blur_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                photo.path, photo.filename, photo.size_bytes,
                photo.modified_time, photo.captured_time,
                photo.width, photo.height, photo.camera_model,
                photo.lens_model, photo.focal_length, photo.aperture,
                photo.iso, photo.shutter_speed, photo.phash, photo.blur_score
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_photos(self, order_by: str = "captured_time") -> List[PhotoRecord]:
        """Get all photos, optionally sorted"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"SELECT * FROM photos ORDER BY {order_by}")
            return [self._row_to_record(row) for row in cursor.fetchall()]
    
    def get_photos_in_timerange(
        self,
        start: datetime,
        end: datetime
    ) -> List[PhotoRecord]:
        """Get photos captured in time range"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM photos WHERE captured_time BETWEEN ? AND ? ORDER BY captured_time",
                (start, end)
            )
            return [self._row_to_record(row) for row in cursor.fetchall()]
    
    @staticmethod
    def _row_to_record(row) -> PhotoRecord:
        """Convert database row to PhotoRecord"""
        return PhotoRecord(
            id=row['id'],
            path=row['path'],
            filename=row['filename'],
            size_bytes=row['size_bytes'],
            modified_time=datetime.fromisoformat(row['modified_time']) if row['modified_time'] else None,
            captured_time=datetime.fromisoformat(row['captured_time']) if row['captured_time'] else None,
            width=row['width'],
            height=row['height'],
            camera_model=row['camera_model'],
            lens_model=row['lens_model'],
            focal_length=row['focal_length'],
            aperture=row['aperture'],
            iso=row['iso'],
            shutter_speed=row['shutter_speed'],
            phash=row['phash'],
            blur_score=row['blur_score'],
            indexed_time=datetime.fromisoformat(row['indexed_time']) if row['indexed_time'] else None
        )
