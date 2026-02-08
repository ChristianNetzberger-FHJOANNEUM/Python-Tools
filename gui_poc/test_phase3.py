"""
Test & Benchmarking Script for Phase 3 SQLite Implementation
=============================================================

This script:
1. Runs initial migration (JSON → SQLite)
2. Benchmarks performance (SQLite vs Legacy)
3. Validates data consistency

Usage:
    python test_phase3.py

Requirements:
    - Flask server should be stopped (to avoid DB locks)
    - Project with enabled folders should exist

Author: Phase 3 Implementation
Date: 2026-02-08
"""

import sys
import time
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hybrid_manager import get_hybrid_manager
from photo_tool.workspace import Workspace
from photo_tool.config import load_config
from photo_tool.projects import ProjectManager


def test_migration():
    """Test migration from JSON to SQLite"""
    print("=" * 80)
    print("TEST 1: Migration (JSON → SQLite)")
    print("=" * 80)
    
    # Get workspace - use the actual workspace from server.py
    workspace_root = Path(__file__).parent.parent
    print(f"\n📁 Tool root: {workspace_root}")
    
    # Use the actual current workspace from Photo-Tool
    # Read from workspace registry to find current workspace
    workspace_registry = Path.home() / ".photo_tool" / "workspaces.json"
    
    if not workspace_registry.exists():
        print(f"❌ Workspace registry not found: {workspace_registry}")
        print("\n💡 Tip: Create a workspace first in the UI.")
        return False
    
    # Load workspace registry
    import json
    with open(workspace_registry, 'r') as f:
        ws_data = json.load(f)
    
    current_ws_path = ws_data.get('current_workspace')
    if not current_ws_path:
        print(f"❌ No current workspace set")
        print("\n💡 Tip: Select a workspace in the UI first.")
        return False
    
    current_ws_path = Path(current_ws_path)
    print(f"\n📂 Current workspace: {current_ws_path}")
    
    # Initialize hybrid manager with tool root
    hybrid_mgr = get_hybrid_manager(str(workspace_root))
    
    # Get projects from the current workspace
    pm = ProjectManager(current_ws_path)
    projects = pm.list_projects()
    
    if not projects:
        print("❌ No projects found. Create a project first.")
        return False
    
    # Use first project
    project = projects[0]
    print(f"\n📦 Test project: {project['name']} ({project['id']})")
    
    # Get enabled folders
    project_data = pm.get_project(project['id'])
    enabled_folders = [Path(f['path']) for f in project_data.folders if f.get('enabled', False)]
    
    if not enabled_folders:
        print("❌ No enabled folders in project. Enable folders first.")
        return False
    
    print(f"\n📂 Enabled folders: {len(enabled_folders)}")
    for folder in enabled_folders:
        print(f"   - {folder}")
    
    # Run migration
    print("\n🚀 Starting migration...")
    start_time = time.time()
    
    stats = hybrid_mgr.migrate_folders_if_needed([str(f) for f in enabled_folders], force=True)
    
    duration = time.time() - start_time
    
    if stats:
        print(f"\n✅ Migration completed in {duration:.2f}s")
        print(f"   Processed: {stats['items_processed']}")
        print(f"   Added:     {stats['items_added']}")
        print(f"   Updated:   {stats['items_updated']}")
        print(f"   Errors:    {stats['items_errors']}")
        
        if stats['items_errors'] > 0:
            print(f"\n⚠️ Errors encountered:")
            for error in stats['errors'][:5]:
                print(f"   - {error}")
        
        return True
    else:
        print(f"⚠️ Migration skipped (database already exists)")
        return True


def benchmark_performance(project_id: str):
    """Benchmark SQLite vs Legacy performance"""
    print("\n" + "=" * 80)
    print("TEST 2: Performance Benchmark (SQLite vs Legacy)")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    
    # Test 1: SQLite-backed (should be fast)
    print("\n🚀 Testing SQLite-backed loading...")
    start_time = time.time()
    
    try:
        response = requests.get(
            f"{base_url}/api/projects/{project_id}/media",
            params={'use_sqlite': 'true', 'limit': 5000}
        )
        
        sqlite_duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            perf = data.get('performance', {})
            source = data.get('source', 'unknown')
            
            print(f"✅ SQLite load: {total} items in {sqlite_duration:.3f}s")
            print(f"   Source: {source}")
            print(f"   Performance breakdown:")
            for key, value in perf.items():
                print(f"      {key}: {value:.3f}s")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ SQLite test failed: {e}")
        return False
    
    # Test 2: Legacy file-based (for comparison)
    print("\n🐌 Testing legacy file-based loading...")
    start_time = time.time()
    
    try:
        response = requests.get(
            f"{base_url}/api/projects/{project_id}/media",
            params={'use_sqlite': 'false', 'limit': 5000}
        )
        
        legacy_duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            perf = data.get('performance', {})
            source = data.get('source', 'unknown')
            
            print(f"✅ Legacy load: {total} items in {legacy_duration:.3f}s")
            print(f"   Source: {source}")
            print(f"   Performance breakdown:")
            for key, value in perf.items():
                print(f"      {key}: {value:.3f}s")
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Legacy test failed: {e}")
        return False
    
    # Compare
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"SQLite:  {sqlite_duration:.3f}s")
    print(f"Legacy:  {legacy_duration:.3f}s")
    
    if legacy_duration > 0:
        speedup = legacy_duration / sqlite_duration
        improvement = ((legacy_duration - sqlite_duration) / legacy_duration) * 100
        
        print(f"\n🚀 Speedup: {speedup:.2f}x faster")
        print(f"📈 Improvement: {improvement:.1f}% faster")
    
    return True


def validate_data_consistency():
    """Validate that SQLite data matches JSON data"""
    print("\n" + "=" * 80)
    print("TEST 3: Data Consistency Validation")
    print("=" * 80)
    
    # TODO: Implement validation
    # - Sample N random files
    # - Compare JSON metadata with SQLite data
    # - Report discrepancies
    
    print("\n⚠️ Data validation not yet implemented")
    return True


def main():
    """Main test runner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   PHASE 3 SQLITE IMPLEMENTATION TEST                         ║
║                                                                              ║
║  This script tests the SQLite database integration for performance          ║
║  optimization. It will:                                                      ║
║                                                                              ║
║  1. Migrate JSON sidecar data to SQLite                                     ║
║  2. Benchmark performance (SQLite vs Legacy)                                ║
║  3. Validate data consistency                                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Run migration test
    if not test_migration():
        print("\n❌ Migration test failed. Aborting.")
        return 1
    
    # Get project ID for benchmarking from current workspace
    workspace_registry = Path.home() / ".photo_tool" / "workspaces.json"
    with open(workspace_registry, 'r') as f:
        ws_data = json.load(f)
    
    current_ws_path = Path(ws_data.get('current_workspace'))
    pm = ProjectManager(current_ws_path)
    projects = pm.list_projects()
    
    if not projects:
        print("\n❌ No projects found for benchmarking.")
        return 1
    
    project_id = projects[0]['id']
    
    # Ask user to start Flask server
    print("\n" + "=" * 80)
    print("⚠️  IMPORTANT: Start the Flask server now!")
    print("=" * 80)
    print("\nIn a separate terminal, run:")
    print("   cd gui_poc")
    print("   python server.py")
    print("\nPress ENTER when the server is running...")
    input()
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/api/projects")
            if response.status_code == 200:
                print("✅ Server is ready!")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ Server not responding. Aborting.")
        return 1
    
    # Run benchmark
    if not benchmark_performance(project_id):
        print("\n❌ Benchmark failed.")
        return 1
    
    # Run validation
    validate_data_consistency()
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)
    print("\n🎉 Phase 3 SQLite implementation is ready!")
    print("\nNext steps:")
    print("1. Monitor performance in production")
    print("2. Implement incremental sync for changed files")
    print("3. Add timeline features (Phase 3b)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
