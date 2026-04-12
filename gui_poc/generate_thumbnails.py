"""
Pre-generate thumbnails for scanned photos (SQLite → workspace/cache/thumbnails).
CLI shares implementation with the GUI (thumbnail_cache_service).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_GUI_POC = Path(__file__).resolve().parent
if str(_GUI_POC) not in sys.path:
    sys.path.insert(0, str(_GUI_POC))

from photo_tool.workspace.manager import WorkspaceManager, get_enabled_folders
from thumbnail_cache_service import (
    load_photo_paths_from_db,
    run_thumbnail_batch,
    workspace_db_path_default,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Fill thumbnail cache from workspace_media.db")
    p.add_argument(
        "--scope",
        choices=("all", "enabled"),
        default="all",
        help="all DB photos (is_available=1) or only paths under enabled workspace folders",
    )
    p.add_argument("--force", action="store_true", help="Regenerate even if cached JPEG exists")
    p.add_argument("--workers", type=int, default=8, help="Parallel workers (1–16)")
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    args = p.parse_args()
    workers = max(1, min(int(args.workers), 16))

    ws_manager = WorkspaceManager()
    workspace_path_str = ws_manager.get_current_workspace()
    if not workspace_path_str:
        print("ERROR: No workspace selected. Select workspace in GUI first!")
        sys.exit(1)

    workspace_path = Path(workspace_path_str)
    db_path = workspace_db_path_default()
    if not db_path.is_file():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    roots = get_enabled_folders(workspace_path) if args.scope == "enabled" else None
    filter_roots = roots if args.scope == "enabled" else None
    paths = load_photo_paths_from_db(db_path, enabled_roots=filter_roots)
    print(f"Workspace: {workspace_path}")
    print(f"Database: {db_path}")
    print(f"Scope: {args.scope} — {len(paths)} photo paths")

    if not args.yes:
        if input("\nGenerate thumbnails? (yes/no): ").strip().lower() != "yes":
            print("Cancelled.")
            return

    def progress(done: int, total: int, path: str, counts: dict) -> None:
        if total and (done % 100 == 0 or done == total or done == 0):
            print(f"  {done}/{total}  {counts}  {path or ''}".strip())

    counts = run_thumbnail_batch(
        workspace_path,
        db_path,
        scope=args.scope,
        force=args.force,
        max_workers=workers,
        enabled_roots=roots,
        progress=progress,
    )
    print("\nDone:", counts)


if __name__ == "__main__":
    main()
