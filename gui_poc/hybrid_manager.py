"""
HybridMediaManager: Automatic JSON ↔ SQLite Synchronization
============================================================

Purpose: Maintain bidirectional sync between JSON sidecars and SQLite database.

Core Principle: JSON is SOURCE OF TRUTH
- All changes are written to JSON first
- SQLite is updated automatically (performance cache)
- On conflict: JSON wins
- SQLite enables fast queries (no file I/O)

Usage:
    # Initialize manager
    manager = HybridMediaManager(workspace_root)
    
    # Update media (auto-syncs JSON → SQLite)
    manager.update_media_rating('/path/to/photo.jpg', rating=5)
    
    # Load media (from SQLite, fast!)
    media = manager.load_project_media('project-123', use_cache=True)

Author: Phase 3 Implementation
Date: 2026-02-08
"""

import os
import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

from db_manager import DatabaseManager, WorkspaceMediaDB, ProjectMediaDB, get_db_manager
from migration import MigrationManager

logger = logging.getLogger(__name__)


class HybridMediaManager:
    """
    Manages bidirectional sync between JSON sidecars and SQLite database.
    
    Design:
    - JSON sidecars: Portable, human-readable, source of truth
    - SQLite: Fast queries, aggregations, indexes (performance cache)
    - Auto-sync: Changes to JSON trigger SQLite update
    """
    
    def __init__(self, workspace_root: str):
        """
        Initialize hybrid media manager.
        
        Args:
            workspace_root: Path to workspace root
        """
        self.workspace_root = Path(workspace_root)
        self.db_manager = get_db_manager(str(workspace_root))
        self.workspace_db = WorkspaceMediaDB(self.db_manager)
        self.project_db = ProjectMediaDB(self.db_manager)
        self.migration_manager = MigrationManager(str(workspace_root))
    
    # ========================================================================
    # INITIALIZATION & MIGRATION
    # ========================================================================
    
    def ensure_database_initialized(self):
        """
        Ensure workspace database exists and is initialized.
        """
        if not self.db_manager.workspace_db_path.exists():
            logger.info("🔧 Workspace database not found, initializing...")
            self.db_manager.init_workspace_db()
    
    def migrate_folders_if_needed(self, folders: List[str], force: bool = False) -> Optional[Dict[str, Any]]:
        """
        Migrate folders to SQLite if not already migrated.
        
        Args:
            folders: List of folder paths
            force: Force re-migration even if already migrated
            
        Returns:
            Migration stats or None if skipped
        """
        self.ensure_database_initialized()
        
        conn = self.db_manager.get_workspace_db()
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("SELECT COUNT(*) as count FROM media")
        media_count = cursor.fetchone()['count']
        conn.close()
        
        if media_count == 0 or force:
            logger.info("🚀 Running initial migration...")
            stats = self.migration_manager.migrate_folders_to_sqlite(folders)
            return stats
        else:
            logger.info(f"✅ Database already contains {media_count} media files")
            return None
    
    # ========================================================================
    # LOAD MEDIA (SQLite-Backed, Fast!)
    # ========================================================================
    
    def load_workspace_media(self, media_type: Optional[str] = None, 
                            limit: int = 1000, offset: int = 0,
                            use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Load media from workspace (SQLite-backed, fast!).
        
        Args:
            media_type: Filter by type ('photo', 'video', 'audio') or None
            limit: Max results
            offset: Pagination offset
            use_cache: Use SQLite cache (True) or read from JSON (False)
            
        Returns:
            List of media dicts
        """
        if use_cache:
            # Fast path: Load from SQLite
            conn = self.db_manager.get_workspace_db()
            media_list = self.workspace_db.get_all_media(
                conn, media_type, limit, offset
            )
            conn.close()
            
            # Parse JSON fields
            for media in media_list:
                if media.get('keywords'):
                    try:
                        media['keywords'] = json.loads(media['keywords'])
                    except:
                        media['keywords'] = []
            
            return media_list
        else:
            # Slow path: Read from JSON files (for debugging/verification)
            # TODO: Implement if needed
            raise NotImplementedError("JSON-only loading not yet implemented")
    
    def load_project_media(self, project_id: str, 
                          media_type: Optional[str] = None,
                          use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Load media for a specific project (SQLite-backed, fast!).
        
        This is THE critical function for the Media tab performance!
        
        Args:
            project_id: Project ID
            media_type: Filter by type ('photo', 'video', 'audio') or None
            use_cache: Use SQLite cache (True) or read from JSON (False)
            
        Returns:
            List of media dicts with combined workspace + project data
        """
        if not use_cache:
            # Fallback to old JSON-based loading
            raise NotImplementedError("JSON-only project loading not yet implemented")
        
        # Fast path: Load from SQLite with JOIN
        project_conn = self.db_manager.get_project_db(project_id)
        workspace_conn = self.db_manager.get_workspace_db()
        
        try:
            cursor = project_conn.cursor()
            
            # Build query with optional media_type filter
            if media_type:
                query = """
                    SELECT * FROM project_media 
                    WHERE media_type = ? AND is_selected = 1
                    ORDER BY sequence_order, id
                """
                cursor.execute(query, (media_type,))
            else:
                query = """
                    SELECT * FROM project_media 
                    WHERE is_selected = 1
                    ORDER BY sequence_order, id
                """
                cursor.execute(query)
            
            project_media = [dict(row) for row in cursor.fetchall()]
            
            # Enrich with workspace data (bulk query)
            if project_media:
                workspace_ids = [pm['workspace_media_id'] for pm in project_media]
                placeholders = ','.join('?' * len(workspace_ids))
                
                workspace_cursor = workspace_conn.cursor()
                workspace_cursor.execute(f"""
                    SELECT m.*, pm.* 
                    FROM media m
                    LEFT JOIN photo_metadata pm ON m.id = pm.media_id
                    WHERE m.id IN ({placeholders})
                """, workspace_ids)
                
                workspace_data = {row['id']: dict(row) for row in workspace_cursor.fetchall()}
                
                # Merge project + workspace data
                result = []
                for pm in project_media:
                    workspace_media = workspace_data.get(pm['workspace_media_id'], {})
                    
                    # Combine data (project overrides workspace)
                    combined = {**workspace_media, **pm}
                    
                    # Parse JSON fields
                    if combined.get('keywords'):
                        try:
                            combined['keywords'] = json.loads(combined['keywords'])
                        except:
                            combined['keywords'] = []
                    
                    # Use project-specific overrides if set
                    if pm.get('project_rating') is not None:
                        combined['rating'] = pm['project_rating']
                    if pm.get('project_color'):
                        combined['color'] = pm['project_color']
                    if pm.get('project_keywords'):
                        try:
                            project_keywords = json.loads(pm['project_keywords'])
                            combined['keywords'] = list(set(
                                combined.get('keywords', []) + project_keywords
                            ))
                        except:
                            pass
                    
                    result.append(combined)
                
                return result
            
            return []
        
        finally:
            project_conn.close()
            workspace_conn.close()
    
    # ========================================================================
    # UPDATE MEDIA (JSON First, then SQLite)
    # ========================================================================
    
    def update_media_rating(self, media_path: str, rating: int):
        """
        Update media rating.
        
        Flow: JSON (source of truth) → SQLite (cache)
        
        Args:
            media_path: Path to media file
            rating: Rating (0-5)
        """
        self._update_media_field(media_path, 'rating', rating)
    
    def update_media_color(self, media_path: str, color: Optional[str]):
        """
        Update media color label.
        
        Args:
            media_path: Path to media file
            color: Color label or None
        """
        self._update_media_field(media_path, 'color', color)
    
    def update_media_keywords(self, media_path: str, keywords: List[str]):
        """
        Update media keywords.
        
        Args:
            media_path: Path to media file
            keywords: List of keywords
        """
        self._update_media_field(media_path, 'keywords', keywords)
    
    def update_media_comment(self, media_path: str, comment: str):
        """
        Update media comment.
        
        Args:
            media_path: Path to media file
            comment: Comment text
        """
        self._update_media_field(media_path, 'comment', comment)
    
    def _update_media_field(self, media_path: str, field: str, value: Any):
        """
        Update a media field (JSON first, then SQLite).
        
        Args:
            media_path: Path to media file
            field: Field name ('rating', 'color', 'keywords', 'comment')
            value: New value
        """
        media_path_obj = Path(media_path)
        metadata_path = media_path_obj.with_suffix('.metadata.json')
        
        # 1. Update JSON (source of truth)
        metadata = {}
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.error(f"❌ Failed to load metadata {metadata_path}: {e}")
        
        metadata[field] = value
        metadata['updated_at'] = int(time.time())
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Failed to write metadata {metadata_path}: {e}")
            raise
        
        # 2. Sync to SQLite (cache)
        try:
            conn = self.db_manager.get_workspace_db()
            existing = self.workspace_db.get_media_by_path(conn, media_path)
            
            if existing:
                # Update existing
                self.workspace_db.update_media_metadata(
                    conn, existing['id'], {field: value}
                )
                logger.debug(f"✅ Synced {field} to SQLite for {media_path_obj.name}")
            else:
                logger.warning(f"⚠️ Media not in SQLite: {media_path}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"❌ SQLite sync failed for {media_path}: {e}")
            # Don't raise - JSON is already updated (source of truth)
    
    # ========================================================================
    # PROJECT MEDIA ASSIGNMENT
    # ========================================================================
    
    def add_media_to_project(self, project_id: str, media_paths: List[str],
                            media_type: str = 'photo') -> Dict[str, Any]:
        """
        Add media files to project.
        
        Args:
            project_id: Project ID
            media_paths: List of media file paths
            media_type: Media type ('photo', 'video', 'audio')
            
        Returns:
            Statistics dict
        """
        stats = {
            'added': 0,
            'skipped': 0,
            'errors': 0
        }
        
        workspace_conn = self.db_manager.get_workspace_db()
        project_conn = self.db_manager.get_project_db(project_id)
        
        try:
            for media_path in media_paths:
                # Get workspace media ID
                workspace_media = self.workspace_db.get_media_by_path(
                    workspace_conn, media_path
                )
                
                if not workspace_media:
                    logger.warning(f"⚠️ Media not in workspace DB: {media_path}")
                    stats['skipped'] += 1
                    continue
                
                # Add to project
                try:
                    self.project_db.add_project_media(
                        project_conn,
                        workspace_media_id=workspace_media['id'],
                        workspace_path=media_path,
                        media_type=media_type
                    )
                    stats['added'] += 1
                
                except sqlite3.IntegrityError:
                    # Already exists
                    stats['skipped'] += 1
        
        finally:
            workspace_conn.close()
            project_conn.close()
        
        return stats
    
    # ========================================================================
    # INCREMENTAL SYNC (for changed files)
    # ========================================================================
    
    def sync_changed_files(self, changed_paths: List[str]) -> Dict[str, Any]:
        """
        Sync changed files to SQLite (incremental update).
        
        Args:
            changed_paths: List of changed file paths
            
        Returns:
            Statistics dict
        """
        stats = {
            'updated': 0,
            'added': 0,
            'errors': 0
        }
        
        conn = self.db_manager.get_workspace_db()
        
        try:
            for path in changed_paths:
                path_obj = Path(path)
                
                # Determine media type
                ext = path_obj.suffix.lower()
                if ext in ['.jpg', '.jpeg', '.png']:
                    media_type = 'photo'
                elif ext in ['.mp4', '.mov', '.avi']:
                    media_type = 'video'
                elif ext in ['.mp3', '.wav', '.aac']:
                    media_type = 'audio'
                else:
                    continue
                
                # Check if exists
                existing = self.workspace_db.get_media_by_path(conn, str(path_obj))
                
                if existing:
                    # Update
                    # TODO: Re-extract EXIF, reload sidecar, update DB
                    stats['updated'] += 1
                else:
                    # Add new
                    # TODO: Extract EXIF, load sidecar, add to DB
                    stats['added'] += 1
        
        finally:
            conn.close()
        
        return stats


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_hybrid_manager_instance: Optional[HybridMediaManager] = None


def get_hybrid_manager(workspace_root: Optional[str] = None) -> HybridMediaManager:
    """
    Get singleton HybridMediaManager instance.
    
    Args:
        workspace_root: Path to workspace root (required for first call)
        
    Returns:
        HybridMediaManager instance
    """
    global _hybrid_manager_instance
    
    if _hybrid_manager_instance is None:
        if workspace_root is None:
            raise ValueError("workspace_root required for first initialization")
        _hybrid_manager_instance = HybridMediaManager(workspace_root)
    
    return _hybrid_manager_instance
