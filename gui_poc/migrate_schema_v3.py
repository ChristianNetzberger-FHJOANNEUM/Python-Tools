"""
Schema Migration v3: Future-Proof for Phase 4 (RAW+Edits)
==========================================================

Adds columns for:
- RAW+JPEG tandem management
- Non-destructive edit stack
- Render cache paths
- Advanced analyses (landscape, night, faces)

These columns are prepared now but will be used in Phase 4.

Usage:
    python migrate_schema_v3.py

Author: Phase 3c+4 Implementation
Date: 2026-02-08
"""

import sqlite3
import sys
from pathlib import Path

def migrate_schema():
    """Migrate database schema to v3 (future-proof)"""
    
    db_path = Path(__file__).parent / "db" / "workspace_media.db"
    
    if not db_path.exists():
        print("No existing database - will be created with new schema on first migration")
        return
    
    print(f"Migrating database schema to v3: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(photo_metadata)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    changes = []
    
    # ========================================================================
    # RAW + JPEG TANDEM (Phase 4a)
    # ========================================================================
    
    new_columns = {
        'has_raw_tandem': 'BOOLEAN DEFAULT 0',
        'raw_file_path': 'TEXT',
        'jpeg_file_path': 'TEXT',
        'tandem_primary': "TEXT CHECK(tandem_primary IN ('raw', 'jpeg', NULL))",
        'tandem_export_from': "TEXT CHECK(tandem_export_from IN ('raw', 'jpeg', 'auto', NULL)) DEFAULT 'auto'",
        
        # ========================================================================
        # NON-DESTRUCTIVE EDITS (Phase 4b)
        # ========================================================================
        'has_edits': 'BOOLEAN DEFAULT 0',
        'edit_stack': 'TEXT',
        'edit_version': "TEXT DEFAULT '1.0'",
        'edits_updated_at': 'INTEGER',
        'edits_applied_by': 'TEXT',
        
        # ========================================================================
        # RENDER CACHE (Phase 4c)
        # ========================================================================
        'cached_thumbnail_path': 'TEXT',
        'cached_preview_path': 'TEXT',
        'cached_fullres_path': 'TEXT',
        'cache_invalidated': 'BOOLEAN DEFAULT 0',
        'cache_date': 'INTEGER',
        'cache_size_bytes': 'INTEGER',
        
        # ========================================================================
        # ADVANCED ANALYSES (Phase 4d)
        # ========================================================================
        'analyses_extended': 'TEXT',
        'is_landscape_photo': 'BOOLEAN DEFAULT 0',
        'landscape_confidence': 'REAL',
        'horizon_angle': 'REAL',
        'is_night_photo': 'BOOLEAN DEFAULT 0',
        'night_detection_confidence': 'REAL',
        'face_count': 'INTEGER DEFAULT 0',
        'faces_data': 'TEXT'
    }
    
    # Add missing columns
    for col_name, col_type in new_columns.items():
        if col_name not in existing_cols:
            print(f"  Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE photo_metadata ADD COLUMN {col_name} {col_type}")
            changes.append(col_name)
    
    # Commit changes
    if changes:
        conn.commit()
        print(f"Schema migration complete! Added {len(changes)} columns.")
        
        # Create new indexes
        print("  Creating indexes for new columns...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photo_has_raw ON photo_metadata(has_raw_tandem)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photo_has_edits ON photo_metadata(has_edits)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photo_landscape ON photo_metadata(is_landscape_photo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photo_night ON photo_metadata(is_night_photo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photo_cache_invalid ON photo_metadata(cache_invalidated)")
            conn.commit()
            print("  Indexes created")
        except Exception as e:
            print(f"  Index warning: {e}")
    else:
        print("Schema already up to date (v3)!")
    
    # Update schema version in metadata
    cursor.execute("UPDATE db_metadata SET value = '3.0' WHERE key = 'schema_version'")
    conn.commit()
    
    # Stats
    cursor.execute("SELECT COUNT(*) as total FROM media")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as photos FROM media WHERE media_type = 'photo'")
    photos = cursor.fetchone()[0]
    
    print(f"\nDatabase Stats:")
    print(f"   Schema version:  3.0 (future-proof)")
    print(f"   Total media:     {total}")
    print(f"   Photos:          {photos}")
    print(f"   Ready for:       RAW Tandem, Non-Destructive Edits, Advanced Analyses")
    
    conn.close()

if __name__ == '__main__':
    try:
        migrate_schema()
        sys.exit(0)
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
