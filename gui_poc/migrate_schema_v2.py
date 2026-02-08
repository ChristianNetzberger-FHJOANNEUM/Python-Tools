"""
Database Schema Migration: Add workspace_path and is_available columns
=======================================================================

This script updates the existing workspace_media.db schema to add:
- workspace_path column (for multi-workspace support)
- is_available column (for soft delete)
- last_verified column (for file existence tracking)

Usage:
    python migrate_schema_v2.py

Author: Phase 3b Implementation
Date: 2026-02-08
"""

import sqlite3
import sys
from pathlib import Path

def migrate_schema():
    """Migrate existing database schema to v2"""
    
    # Database path
    db_path = Path(__file__).parent / "db" / "workspace_media.db"
    
    if not db_path.exists():
        print("No existing database found - will be created with new schema")
        return
    
    print(f"Migrating database schema: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(media)")
    columns = {row[1] for row in cursor.fetchall()}
    
    changes_made = False
    
    # Add workspace_path column if missing
    if 'workspace_path' not in columns:
        print("  Adding workspace_path column...")
        cursor.execute("ALTER TABLE media ADD COLUMN workspace_path TEXT")
        changes_made = True
    else:
        print("  workspace_path column already exists")
    
    # Add is_available column if missing
    if 'is_available' not in columns:
        print("  Adding is_available column...")
        cursor.execute("ALTER TABLE media ADD COLUMN is_available BOOLEAN DEFAULT 1")
        changes_made = True
    else:
        print("  is_available column already exists")
    
    # Add last_verified column if missing
    if 'last_verified' not in columns:
        print("  Adding last_verified column...")
        cursor.execute("ALTER TABLE media ADD COLUMN last_verified INTEGER")
        changes_made = True
    else:
        print("  last_verified column already exists")
    
    # Commit changes
    if changes_made:
        conn.commit()
        print("Schema migration complete!")
        
        # Create new indexes
        print("  Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workspace ON media(workspace_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_available ON media(is_available)")
            conn.commit()
            print("  Indexes created")
        except Exception as e:
            print(f"  Index creation warning: {e}")
    else:
        print("Schema already up to date!")
    
    # Show stats
    cursor.execute("SELECT COUNT(*) as total FROM media")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as available FROM media WHERE is_available = 1 OR is_available IS NULL")
    available = cursor.fetchone()[0]
    
    print(f"\nDatabase Stats:")
    print(f"   Total media:     {total}")
    print(f"   Available:       {available}")
    print(f"   Unavailable:     {total - available}")
    
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
