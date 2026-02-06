#!/usr/bin/env python3
"""
Workspace Cleanup Utility
Finds and removes workspaces with invalid/missing configs
"""

from pathlib import Path
from photo_tool.workspace.manager import WorkspaceManager
from photo_tool.config import load_config
import sys


def check_workspace(ws):
    """Check if workspace config is valid"""
    ws_path = Path(ws['path'])
    config_file = ws_path / "config.yaml"
    
    # Check if path exists
    if not ws_path.exists():
        return False, "Path does not exist"
    
    # Check if config exists
    if not config_file.exists():
        return False, "config.yaml not found"
    
    # Try to load config
    try:
        load_config(config_file)
        return True, "Valid"
    except Exception as e:
        return False, f"Invalid config: {str(e)[:50]}"


def cleanup_workspaces(dry_run=True):
    """
    Find and optionally remove invalid workspaces
    
    Args:
        dry_run: If True, only show what would be deleted
    """
    print("=" * 70)
    print("WORKSPACE CLEANUP UTILITY")
    print("=" * 70)
    print()
    
    wm = WorkspaceManager()
    
    if not wm.workspaces:
        print("✓ No workspaces registered.")
        return
    
    print(f"Found {len(wm.workspaces)} registered workspace(s):\n")
    
    valid_workspaces = []
    invalid_workspaces = []
    
    # Check all workspaces
    for ws in wm.workspaces:
        is_valid, reason = check_workspace(ws)
        
        if is_valid:
            valid_workspaces.append(ws)
            print(f"✓ VALID:   {ws['name']}")
            print(f"           {ws['path']}")
        else:
            invalid_workspaces.append((ws, reason))
            print(f"❌ INVALID: {ws['name']}")
            print(f"           {ws['path']}")
            print(f"           Reason: {reason}")
        print()
    
    # Summary
    print("=" * 70)
    print(f"Valid workspaces:   {len(valid_workspaces)}")
    print(f"Invalid workspaces: {len(invalid_workspaces)}")
    print("=" * 70)
    print()
    
    # Ask for cleanup
    if invalid_workspaces:
        if dry_run:
            print("DRY RUN MODE - No changes will be made")
            print()
            print("To actually delete, run:")
            print("    python cleanup_workspaces.py --delete")
            print()
        else:
            print("DANGER ZONE!")
            print()
            print("This will:")
            print("  1. Remove invalid workspaces from registry")
            print("  2. DELETE their config.yaml files")
            print("  3. Keep all media files untouched")
            print()
            
            response = input("Continue? Type 'DELETE' to confirm: ")
            
            if response == 'DELETE':
                print()
                print("Deleting invalid workspaces...")
                print()
                
                for ws, reason in invalid_workspaces:
                    try:
                        success = wm.remove_workspace(ws['path'], delete_config=True)
                        if success:
                            print(f"✓ Removed: {ws['name']}")
                        else:
                            print(f"✗ Failed:  {ws['name']}")
                    except Exception as e:
                        print(f"✗ Error:   {ws['name']} - {e}")
                
                print()
                print("=" * 70)
                print("✓ CLEANUP COMPLETE!")
                print("=" * 70)
                print()
                print(f"Removed {len(invalid_workspaces)} invalid workspace(s)")
                print(f"Kept {len(valid_workspaces)} valid workspace(s)")
                print()
            else:
                print()
                print("Aborted. No changes made.")
                print()
    else:
        print("✓ All workspaces are valid!")
        print()


def main():
    """Main entry point"""
    dry_run = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--delete', '-d']:
            dry_run = False
        elif sys.argv[1] in ['--help', '-h']:
            print("Usage:")
            print("  python cleanup_workspaces.py          # Dry run (show only)")
            print("  python cleanup_workspaces.py --delete # Actually delete")
            print("  python cleanup_workspaces.py --help   # Show this help")
            return
    
    try:
        cleanup_workspaces(dry_run=dry_run)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
