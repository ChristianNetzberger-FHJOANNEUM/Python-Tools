"""Quick re-migration script without unicode issues"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from migration import MigrationManager
import json

# Get workspace root
workspace_root = Path(__file__).parent.parent

# Get current workspace
workspace_registry = Path.home() / ".photo_tool" / "workspaces.json"
with open(workspace_registry, 'r') as f:
    ws_data = json.load(f)

current_ws_path = Path(ws_data.get('current_workspace'))
print(f"Workspace: {current_ws_path}")

# Get project
from photo_tool.projects import ProjectManager
pm = ProjectManager(current_ws_path)
projects = pm.list_projects()

if not projects:
    print("No projects found")
    sys.exit(1)

project = projects[0]
print(f"Project: {project['name']}")

# Get enabled folders
project_data = pm.get_project(project['id'])
enabled_folders = [Path(f['path']) for f in project_data.folders if f.get('enabled', False)]

print(f"Folders: {len(enabled_folders)}")
for f in enabled_folders:
    print(f"  - {f}")

# Run migration
print("\nStarting migration...")
manager = MigrationManager(str(workspace_root))
stats = manager.migrate_folders_to_sqlite([str(f) for f in enabled_folders])

print(f"\nDone in {stats['duration']:.2f}s")
print(f"Processed: {stats['items_processed']}")
print(f"Added: {stats['items_added']}")
print(f"Updated: {stats['items_updated']}")
print(f"Errors: {stats['items_errors']}")
