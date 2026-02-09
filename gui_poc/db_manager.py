"""
Database Manager for Phase 3: SQLite Integration
================================================

Purpose: Initialize, manage, and sync SQLite databases for workspace and projects.

Architecture:
- Workspace DB: workspace_media.db (global media pool)
- Project DB: projects/{project_id}/project.db (project-specific data)

Design Principle: Hybrid JSON + SQLite
- JSON sidecars: Source of truth (portable)
- SQLite: Performance cache + timeline/project data

Author: Phase 3 Implementation
Date: 2026-02-08
"""

import sqlite3
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections and schema initialization.
    """
    
    def __init__(self, workspace_root: str):
        """
        Initialize database manager.
        
        Args:
            workspace_root: Path to workspace root directory
        """
        self.workspace_root = Path(workspace_root)
        self.db_dir = self.workspace_root / "gui_poc" / "db"
        self.schemas_dir = self.db_dir / "schemas"
        
        # Database paths
        self.workspace_db_path = self.db_dir / "workspace_media.db"
        
        # Ensure directories exist
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # WORKSPACE DATABASE
    # ========================================================================
    
    def init_workspace_db(self) -> sqlite3.Connection:
        """
        Initialize workspace database with schema.
        
        Returns:
            Database connection
        """
        logger.info("🔧 Initializing workspace database...")
        
        # Connect to database
        conn = sqlite3.connect(str(self.workspace_db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        
        # Load schema
        schema_path = self.schemas_dir / "workspace_schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        
        logger.info(f"✅ Workspace database initialized: {self.workspace_db_path}")
        
        return conn
    
    def get_workspace_db(self) -> sqlite3.Connection:
        """
        Get workspace database connection (creates if not exists).
        
        Returns:
            Database connection
        """
        if not self.workspace_db_path.exists():
            return self.init_workspace_db()
        
        conn = sqlite3.connect(str(self.workspace_db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========================================================================
    # PROJECT DATABASE
    # ========================================================================
    
    def init_project_db(self, project_id: str) -> sqlite3.Connection:
        """
        Initialize project database with schema.
        
        Args:
            project_id: Project ID
            
        Returns:
            Database connection
        """
        logger.info(f"🔧 Initializing project database for: {project_id}")
        
        # Project DB path
        project_dir = self.workspace_root / "gui_poc" / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        project_db_path = project_dir / "project.db"
        
        # Connect to database
        conn = sqlite3.connect(str(project_db_path))
        conn.row_factory = sqlite3.Row
        
        # Load schema
        schema_path = self.schemas_dir / "project_schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        
        logger.info(f"✅ Project database initialized: {project_db_path}")
        
        return conn
    
    def get_project_db(self, project_id: str) -> sqlite3.Connection:
        """
        Get project database connection (creates if not exists).
        
        Args:
            project_id: Project ID
            
        Returns:
            Database connection
        """
        project_db_path = self.workspace_root / "gui_poc" / "projects" / project_id / "project.db"
        
        if not project_db_path.exists():
            return self.init_project_db(project_id)
        
        conn = sqlite3.connect(str(project_db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========================================================================
    # DATABASE UTILITIES
    # ========================================================================
    
    def get_db_info(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """
        Get database metadata and statistics.
        
        Args:
            conn: Database connection
            
        Returns:
            Dict with database info
        """
        cursor = conn.cursor()
        
        # Get metadata
        cursor.execute("SELECT key, value FROM db_metadata")
        metadata = {row['key']: row['value'] for row in cursor.fetchall()}
        
        # Get table counts
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row['name'] for row in cursor.fetchall()]
        
        table_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            table_counts[table] = cursor.fetchone()['count']
        
        return {
            'metadata': metadata,
            'tables': tables,
            'table_counts': table_counts
        }
    
    def vacuum_database(self, conn: sqlite3.Connection):
        """
        Optimize database (VACUUM).
        
        Args:
            conn: Database connection
        """
        logger.info("🧹 Running VACUUM on database...")
        conn.execute("VACUUM")
        logger.info("✅ Database optimized")
    
    def close_all_connections(self):
        """
        Close all database connections.
        (Note: In practice, we use context managers)
        """
        pass  # Context managers handle this


class WorkspaceMediaDB:
    """
    High-level interface for workspace media database operations.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    # ========================================================================
    # MEDIA CRUD OPERATIONS
    # ========================================================================
    
    def add_media(self, conn: sqlite3.Connection, path: str, media_type: str, 
                  metadata: Dict[str, Any]) -> int:
        """
        Add media file to workspace database.
        
        Args:
            conn: Database connection
            path: File path (absolute)
            media_type: 'photo', 'video', or 'audio'
            metadata: Media metadata dict
            
        Returns:
            Media ID
        """
        cursor = conn.cursor()
        
        # Extract common fields
        path_obj = Path(path)
        filename = path_obj.name
        folder = str(path_obj.parent)
        file_size = path_obj.stat().st_size if path_obj.exists() else 0
        file_mtime = int(path_obj.stat().st_mtime) if path_obj.exists() else int(time.time())
        
        # Extract metadata fields (with defaults)
        rating = metadata.get('rating', 0)
        color = metadata.get('color')
        keywords = json.dumps(metadata.get('keywords', []))
        comment = metadata.get('comment')
        
        # Insert into media table
        cursor.execute("""
            INSERT OR REPLACE INTO media 
            (path, filename, folder, media_type, file_size, file_mtime,
             rating, color, keywords, comment, json_mtime, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            path, filename, folder, media_type, file_size, file_mtime,
            rating, color, keywords, comment, 
            int(time.time()),  # json_mtime
            int(time.time())   # updated_at
        ))
        
        media_id = cursor.lastrowid
        conn.commit()
        
        return media_id
    
    def get_media_by_path(self, conn: sqlite3.Connection, path: str) -> Optional[Dict[str, Any]]:
        """
        Get media by file path.
        
        Args:
            conn: Database connection
            path: File path
            
        Returns:
            Media dict or None
        """
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media WHERE path = ?", (path,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_media(self, conn: sqlite3.Connection, media_type: Optional[str] = None,
                      limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all media files.
        
        Args:
            conn: Database connection
            media_type: Filter by type ('photo', 'video', 'audio') or None for all
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of media dicts
        """
        cursor = conn.cursor()
        
        if media_type:
            cursor.execute("""
                SELECT * FROM media 
                WHERE media_type = ?
                ORDER BY filename
                LIMIT ? OFFSET ?
            """, (media_type, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM media 
                ORDER BY filename
                LIMIT ? OFFSET ?
            """, (limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_media_metadata(self, conn: sqlite3.Connection, media_id: int, 
                             metadata: Dict[str, Any]):
        """
        Update media metadata.
        
        Args:
            conn: Database connection
            media_id: Media ID
            metadata: New metadata dict
        """
        cursor = conn.cursor()
        
        # Build UPDATE query dynamically
        allowed_fields = {'rating', 'color', 'keywords', 'comment'}
        update_fields = []
        update_values = []
        
        for key, value in metadata.items():
            if key in allowed_fields:
                update_fields.append(f"{key} = ?")
                if key == 'keywords' and isinstance(value, list):
                    update_values.append(json.dumps(value))
                else:
                    update_values.append(value)
        
        if update_fields:
            update_fields.append("updated_at = ?")
            update_values.append(int(time.time()))
            update_values.append(media_id)
            
            query = f"UPDATE media SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
            conn.commit()
    
    def delete_media(self, conn: sqlite3.Connection, media_id: int):
        """
        Delete media from database.
        
        Args:
            conn: Database connection
            media_id: Media ID
        """
        cursor = conn.cursor()
        cursor.execute("DELETE FROM media WHERE id = ?", (media_id,))
        conn.commit()
    
    # ========================================================================
    # PHOTO-SPECIFIC OPERATIONS
    # ========================================================================
    
    def add_photo_metadata(self, conn: sqlite3.Connection, media_id: int, 
                          exif_data: Dict[str, Any], sidecar_data: Dict[str, Any]):
        """
        Add photo-specific metadata.
        
        Args:
            conn: Database connection
            media_id: Media ID
            exif_data: EXIF data dict
            sidecar_data: Sidecar data dict (blur, burst, etc.)
        """
        cursor = conn.cursor()
        
        # Extract EXIF fields
        capture_time = exif_data.get('capture_time')
        width = exif_data.get('width')
        height = exif_data.get('height')
        camera_make = exif_data.get('camera_make')
        camera_model = exif_data.get('camera_model')
        lens_model = exif_data.get('lens_model')
        iso = exif_data.get('iso')
        aperture = exif_data.get('aperture')
        shutter_speed = exif_data.get('shutter_speed')
        focal_length = exif_data.get('focal_length')
        orientation = exif_data.get('orientation')
        
        # Extract sidecar analyses (blur, burst)
        # Note: _load_sidecar already returns the 'analyses' dict, not the full phototool structure
        blur_data = sidecar_data.get('blur', {})
        burst_data = sidecar_data.get('burst', {})
        
        # Version 2: neighbors are simple string paths, burst_id is always present
        burst_neighbors = burst_data.get('neighbors', [])
        burst_id = burst_data.get('burst_id')
        
        # Fallback: generate burst_id if somehow missing (should not happen in Version 2)
        if not burst_id and burst_neighbors:
            import hashlib
            first_neighbor = burst_neighbors[0] if burst_neighbors else ''
            burst_id = hashlib.md5(first_neighbor.encode()).hexdigest()[:12]
            logger.warning(f"Missing burst_id in JSON, generated: {burst_id}")
        
        # Insert photo metadata
        cursor.execute("""
            INSERT OR REPLACE INTO photo_metadata 
            (media_id, capture_time, width, height, camera_make, camera_model, 
             lens_model, iso, aperture, shutter_speed, focal_length, orientation,
             blur_laplacian, blur_laplacian_threshold, blur_tenengrad, blur_tenengrad_threshold,
             blur_roi, blur_roi_threshold, blur_detection_date,
             is_burst_candidate, burst_id, burst_neighbors, burst_score, burst_detection_date,
             exif_synced_at, sidecar_synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?)
        """, (
            media_id, capture_time, width, height, camera_make, camera_model,
            lens_model, iso, aperture, shutter_speed, focal_length, orientation,
            # Blur (handle both 'detection_date' and 'computed_at', thresholds may be missing)
            blur_data.get('laplacian', {}).get('score'),
            blur_data.get('laplacian', {}).get('threshold', 50.0),  # Default threshold
            blur_data.get('tenengrad', {}).get('score'),
            blur_data.get('tenengrad', {}).get('threshold', 100.0),  # Default threshold
            blur_data.get('roi', {}).get('score'),
            blur_data.get('roi', {}).get('threshold', 60.0),  # Default threshold
            blur_data.get('detection_date') or blur_data.get('computed_at'),
            # Burst (using extracted/generated values)
            burst_data.get('is_burst_candidate', 0),
            burst_id,  # Generated or from JSON
            json.dumps(burst_neighbors) if burst_neighbors else '[]',
            burst_data.get('score'),
            burst_data.get('detection_date') or burst_data.get('computed_at'),
            # Sync timestamps
            int(time.time()),  # exif_synced_at
            int(time.time())   # sidecar_synced_at
        ))
        
        conn.commit()
    
    # ========================================================================
    # SYNC STATUS TRACKING
    # ========================================================================
    
    def start_sync(self, conn: sqlite3.Connection, sync_type: str) -> int:
        """
        Start a new sync operation.
        
        Args:
            conn: Database connection
            sync_type: 'full_rebuild', 'incremental', 'folder_scan', 'migration'
            
        Returns:
            Sync ID
        """
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sync_status 
            (sync_type, status, started_at)
            VALUES (?, 'running', ?)
        """, (sync_type, int(time.time())))
        
        sync_id = cursor.lastrowid
        conn.commit()
        
        return sync_id
    
    def finish_sync(self, conn: sqlite3.Connection, sync_id: int,
                   items_processed: int, items_added: int, items_updated: int,
                   items_deleted: int, items_errors: int,
                   duration_seconds: float, status: str = 'completed',
                   error_message: Optional[str] = None):
        """
        Complete a sync operation.
        
        Args:
            conn: Database connection
            sync_id: Sync ID
            items_processed: Total items processed
            items_added: Items added
            items_updated: Items updated
            items_deleted: Items deleted
            items_errors: Items with errors
            duration_seconds: Sync duration
            status: 'completed', 'failed', 'partial'
            error_message: Optional error message
        """
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sync_status 
            SET items_processed = ?, items_added = ?, items_updated = ?,
                items_deleted = ?, items_errors = ?,
                duration_seconds = ?, status = ?, error_message = ?,
                completed_at = ?
            WHERE id = ?
        """, (
            items_processed, items_added, items_updated,
            items_deleted, items_errors,
            duration_seconds, status, error_message,
            int(time.time()),
            sync_id
        ))
        
        conn.commit()


class ProjectMediaDB:
    """
    High-level interface for project database operations.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    # ========================================================================
    # PROJECT MEDIA ASSIGNMENTS
    # ========================================================================
    
    def add_project_media(self, conn: sqlite3.Connection, 
                         workspace_media_id: int, workspace_path: str, 
                         media_type: str, sequence_order: Optional[int] = None) -> int:
        """
        Add media to project.
        
        Args:
            conn: Database connection
            workspace_media_id: ID in workspace DB
            workspace_path: File path
            media_type: 'photo', 'video', 'audio'
            sequence_order: Optional sequence order
            
        Returns:
            Project media ID
        """
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO project_media
            (workspace_media_id, workspace_path, media_type, sequence_order, added_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            workspace_media_id, workspace_path, media_type, sequence_order,
            int(time.time()), int(time.time())
        ))
        
        project_media_id = cursor.lastrowid
        conn.commit()
        
        return project_media_id
    
    def get_project_media(self, conn: sqlite3.Connection, 
                         media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all media in project.
        
        Args:
            conn: Database connection
            media_type: Optional filter by type
            
        Returns:
            List of project media dicts
        """
        cursor = conn.cursor()
        
        if media_type:
            cursor.execute("""
                SELECT * FROM project_media 
                WHERE media_type = ? AND is_selected = 1
                ORDER BY sequence_order, id
            """, (media_type,))
        else:
            cursor.execute("""
                SELECT * FROM project_media 
                WHERE is_selected = 1
                ORDER BY sequence_order, id
            """)
        
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_db_manager_instance: Optional[DatabaseManager] = None


def get_db_manager(workspace_root: Optional[str] = None) -> DatabaseManager:
    """
    Get singleton DatabaseManager instance.
    
    Args:
        workspace_root: Path to workspace root (required for first call)
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager_instance
    
    if _db_manager_instance is None:
        if workspace_root is None:
            raise ValueError("workspace_root required for first initialization")
        _db_manager_instance = DatabaseManager(workspace_root)
    
    return _db_manager_instance
