"""
Migrate specific folders to SQLite database.
Simpler than resync - just migrates folders you specify.
"""
import sys
from pathlib import Path

# IMPORTANT: Windows multiprocessing guard
if __name__ != '__main__':
    exit(0)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui_poc.hybrid_manager import HybridMediaManager

# =============================================================================
# CONFIGURE YOUR FOLDERS HERE
# =============================================================================
FOLDERS_TO_MIGRATE = [
    r"E:\Lumix-2026-01\101_PANA",
    r"E:\Lumix-2026-01\102_PANA",
    r"E:\Lumix-2026-01\103_PANA",
    r"E:\Lumix-2026-01\104_PANA",
]

def main():
    """Migrate folders to SQLite"""
    print("\n" + "="*60)
    print("FOLDER MIGRATION UTILITY")
    print("="*60)
    print(f"Will migrate {len(FOLDERS_TO_MIGRATE)} folders:")
    for folder in FOLDERS_TO_MIGRATE:
        print(f"  - {folder}")
    print("="*60)
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Initialize manager
    workspace_root = Path(__file__).parent.parent
    print(f"\n📂 Workspace: {workspace_root}")
    
    hybrid_mgr = HybridMediaManager(str(workspace_root))
    
    # Migrate each folder
    print(f"\n🚀 Starting migration...")
    total_added = 0
    
    for i, folder in enumerate(FOLDERS_TO_MIGRATE, 1):
        print(f"\n[{i}/{len(FOLDERS_TO_MIGRATE)}] Migrating: {folder}")
        
        folder_path = Path(folder)
        if not folder_path.exists():
            print(f"  ⚠️ Folder does not exist, skipping")
            continue
        
        try:
            stats = hybrid_mgr.migrate_folders_if_needed([folder], force=True)
            if stats:
                items_added = stats.get('items_added', 0)
                total_added += items_added
                print(f"  ✅ Added {items_added} items")
            else:
                print(f"  ⚠️ No stats returned")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE!")
    print("="*60)
    print(f"\nTotal items added: {total_added}")
    print("Restart the server to use SQLite fast path.")

if __name__ == '__main__':
    main()
