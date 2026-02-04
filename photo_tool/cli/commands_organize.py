"""
Organization and deduplication commands
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..workspace import Workspace
from ..config import load_config
from ..io import scan_multiple_directories, get_capture_time, get_video_capture_time, filter_by_type
from ..analysis import group_by_time, cluster_similar_photos
from ..analysis.similarity import detect_blur, HashMethod
from ..actions import organize_clusters, deduplicate_photos
from ..util.timing import timer


app = typer.Typer()
console = Console()


@app.command("bursts")
def organize_bursts(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview changes"),
    min_size: Optional[int] = typer.Option(None, "--min-size", help="Minimum cluster size"),
):
    """
    Organize burst photos into folders
    
    Example:
        photo-tool organize bursts --dry-run
        photo-tool organize bursts --apply --min-size 3
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        # Override dry-run setting
        config.actions.dry_run = dry_run
        if min_size is not None:
            config.actions.min_group_size = min_size
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be moved[/yellow]\n")
        else:
            console.print("[red]APPLYING CHANGES - Files will be moved![/red]\n")
        
        console.print("[bold]Organizing burst photos...[/bold]\n")
        
        # Scan and analyze (same as analyze command)
        console.print("Scanning and analyzing media files...")
        
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=True
        )
        
        if not all_media:
            console.print("[yellow]No files found[/yellow]")
            return
        
        # Filter photos only (burst organization for photos)
        photos = filter_by_type(all_media, "photo")
        other_count = len(all_media) - len(photos)
        
        if other_count > 0:
            console.print(f"[dim]Note: Skipping {other_count} video/audio files (burst organization for photos only)[/dim]")
        
        if not photos:
            console.print("[yellow]No photos found[/yellow]")
            return
        
        # Get capture times
        capture_times = []
        photo_paths = []
        for photo in photos:
            capture_time = get_capture_time(photo.path)
            if capture_time:
                capture_times.append(capture_time)
                photo_paths.append(photo.path)
        
        # Group by time
        time_groups = group_by_time(
            photo_paths,
            capture_times,
            config.grouping.time_window_seconds,
            config.grouping.max_group_gap_seconds
        )
        
        # Compute blur scores
        blur_scores = {}
        console.print("Computing quality scores...")
        for group in time_groups:
            for photo in group.photos:
                try:
                    score = detect_blur(photo)
                    blur_scores[photo] = score
                except:
                    pass
        
        # Cluster
        hash_method = HashMethod(config.similarity.method)
        clusters = cluster_similar_photos(
            time_groups,
            hash_method=hash_method,
            similarity_threshold=config.similarity.phash_threshold,
            blur_scores=blur_scores,
            show_progress=True
        )
        
        console.print(f"\nFound {len(clusters)} burst sequences")
        
        # Organize
        console.print("\nOrganizing into folders...")
        with timer("Organization"):
            result = organize_clusters(
                clusters,
                naming_strategy=config.actions.burst_folder_naming,
                min_cluster_size=config.actions.min_group_size,
                dry_run=config.actions.dry_run
            )
        
        # Summary
        console.print(f"\n[green]✓[/green] Done!")
        console.print(f"  Clusters processed: {result.clusters_processed}")
        console.print(f"  Folders created: {result.folders_created}")
        console.print(f"  Photos moved: {result.photos_moved}")
        
        if result.errors:
            console.print(f"[red]  Errors: {len(result.errors)}[/red]")
            for error in result.errors[:5]:
                console.print(f"    {error}")
        
        if dry_run:
            console.print("\n[yellow]This was a dry run. Use --apply to make changes.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("dedupe")
def dedupe(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    strategy: str = typer.Option("keep_best", "--strategy", help="keep_best, keep_first, keep_all"),
    action: str = typer.Option("list", "--action", help="list, delete, move"),
    move_to: Optional[Path] = typer.Option(None, "--move-to", help="Target directory for move action"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview changes"),
):
    """
    Find and handle duplicate photos
    
    Example:
        photo-tool organize dedupe --dry-run
        photo-tool organize dedupe --action delete --apply
        photo-tool organize dedupe --action move --move-to duplicates/ --apply
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        if not dry_run and action != "list":
            console.print(f"[red]WARNING: This will {action} duplicate files![/red]\n")
            confirm = typer.confirm("Are you sure?")
            if not confirm:
                raise typer.Exit(0)
        
        console.print("[bold]Finding duplicates...[/bold]\n")
        
        # Scan media files
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=True
        )
        
        if not all_media:
            console.print("[yellow]No files found[/yellow]")
            return
        
        # Filter photos only (deduplication for photos)
        photos = filter_by_type(all_media, "photo")
        other_count = len(all_media) - len(photos)
        
        if other_count > 0:
            console.print(f"[dim]Note: Skipping {other_count} video/audio files (deduplication for photos only)[/dim]")
        
        if not photos:
            console.print("[yellow]No photos found[/yellow]")
            return
        
        # Get capture times and cluster
        capture_times = []
        photo_paths = []
        for photo in photos:
            capture_time = get_capture_time(photo.path)
            if capture_time:
                capture_times.append(capture_time)
                photo_paths.append(photo.path)
        
        time_groups = group_by_time(
            photo_paths,
            capture_times,
            config.grouping.time_window_seconds,
            config.grouping.max_group_gap_seconds
        )
        
        # Blur scores
        blur_scores = {}
        console.print("Computing quality scores...")
        for group in time_groups:
            for photo in group.photos:
                try:
                    blur_scores[photo] = detect_blur(photo)
                except:
                    pass
        
        hash_method = HashMethod(config.similarity.method)
        clusters = cluster_similar_photos(
            time_groups,
            hash_method=hash_method,
            similarity_threshold=config.similarity.phash_threshold,
            blur_scores=blur_scores,
            show_progress=True
        )
        
        console.print(f"\nFound {len(clusters)} groups of similar photos")
        
        # Deduplicate
        affected = deduplicate_photos(
            clusters,
            strategy=strategy,
            action=action,
            move_to=move_to,
            dry_run=dry_run
        )
        
        console.print(f"\n[green]✓[/green] {len(affected)} duplicate(s) found")
        
        if dry_run and action != "list":
            console.print("\n[yellow]This was a dry run. Use --apply to make changes.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("undo")
def undo_organization(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview changes"),
):
    """
    Undo burst organization - move photos back from burst folders
    
    Finds all burst folders (folders containing only photos) and moves
    photos back to their parent directory, then removes empty folders.
    
    Example:
        photo-tool organize undo --dry-run
        photo-tool organize undo --apply
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be moved[/yellow]\n")
        else:
            console.print("[red]APPLYING CHANGES - Files will be moved![/red]\n")
        
        console.print("Undoing burst organization...\n")
        
        # Scan for media to find burst folders
        console.print("Scanning for burst folders...")
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=True
        )
        
        # Find burst folders (folders that contain photos)
        burst_folders = set()
        for media in all_media:
            # If file is in a subfolder, check if it's a burst folder
            if media.path.parent != media.path.parent.parent:
                # Check if parent folder looks like a burst folder
                # (typically named after a photo, like P1022811)
                parent_name = media.path.parent.name
                if parent_name.startswith('P') or parent_name.startswith('IMG'):
                    burst_folders.add(media.path.parent)
        
        if not burst_folders:
            console.print("[yellow]No burst folders found[/yellow]")
            return
        
        console.print(f"\nFound {len(burst_folders)} burst folder(s)")
        
        # Move photos back and remove folders
        import shutil
        
        photos_moved = 0
        folders_removed = 0
        
        for burst_folder in sorted(burst_folders):
            console.print(f"\nProcessing: {burst_folder.name}")
            
            # Get all files in this folder
            files_in_folder = list(burst_folder.glob("*"))
            photo_files = [f for f in files_in_folder if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
            
            if not photo_files:
                continue
            
            console.print(f"  Found {len(photo_files)} photo(s) to move back")
            
            # Move each photo back to parent
            for photo in photo_files:
                target = burst_folder.parent / photo.name
                
                if not dry_run:
                    try:
                        shutil.move(str(photo), str(target))
                        console.print(f"  ✓ Moved: {photo.name} → {target.parent.name}/")
                        photos_moved += 1
                    except Exception as e:
                        console.print(f"  [red]Error moving {photo.name}:[/red] {e}")
                else:
                    console.print(f"  Would move: {photo.name} → {target.parent.name}/")
                    photos_moved += 1
            
            # Remove empty folder
            if not dry_run:
                try:
                    # Check if folder is empty
                    remaining = list(burst_folder.glob("*"))
                    if not remaining:
                        burst_folder.rmdir()
                        console.print(f"  ✓ Removed empty folder: {burst_folder.name}")
                        folders_removed += 1
                except Exception as e:
                    console.print(f"  [yellow]Could not remove folder:[/yellow] {e}")
            else:
                console.print(f"  Would remove folder: {burst_folder.name}")
                folders_removed += 1
        
        console.print(f"\n[green]✓[/green] Done!")
        console.print(f"  Photos moved: {photos_moved}")
        console.print(f"  Folders removed: {folders_removed}")
        
        if dry_run:
            console.print("\n[yellow]This was a dry run. Use --apply to make changes.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
