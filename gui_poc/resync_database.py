"""
Re-sync database with current JSON sidecar files.
Use this when JSON files have been updated/deleted and database is out of sync.
"""
import sys
from pathlib import Path

# IMPORTANT: Must check this BEFORE importing anything that uses ProcessPoolExecutor
if __name__ != '__main__':
    exit(0)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui_poc.hybrid_manager import HybridMediaManager

print("\n" + "="*60)
print("DATABASE RE-SYNC UTILITY")
print("="*60)
print("This will:")
print("  1. Clear all metadata from workspace database")
print("  2. Re-scan all JSON sidecar files")
print("  3. Import fresh data into database")
print("="*60)

response = input("\nContinue? (yes/no): ")
if response.lower() != 'yes':
    print("Cancelled.")
    exit(0)

def main():
    """Main function to run the resync"""
    # Initialize manager
    workspace_root = Path(__file__).parent.parent
    print(f"\n📂 Workspace: {workspace_root}")

    hybrid_mgr = HybridMediaManager(str(workspace_root))

    # Get all folders from database
    import sqlite3
    db_path = workspace_root / "gui_poc" / "db" / "workspace_media.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT folder FROM media WHERE media_type = 'photo' ORDER BY folder")
    folders = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"\n📁 Found {len(folders)} folders in database:")
    for folder in folders:
        print(f"  - {folder}")

    # Clear all photo metadata
    print(f"\n🗑️ Clearing old metadata...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM photo_metadata")
    cursor.execute("DELETE FROM media")
    conn.commit()
    conn.close()
    print("✅ Database cleared")

    # Re-migrate all folders
    print(f"\n🚀 Re-migrating {len(folders)} folders...")
    for i, folder in enumerate(folders, 1):
        print(f"\n[{i}/{len(folders)}] Migrating: {folder}")
        try:
            stats = hybrid_mgr.migrate_folders_if_needed([folder], force=True)
            if stats:
                print(f"  ✅ Added {stats['items_added']} items")
            else:
                print(f"  ⚠️ No stats returned")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("✅ DATABASE RE-SYNC COMPLETE!")
    print("="*60)
    print("\nRestart the server to use the updated database.")

if __name__ == '__main__':
    main()
