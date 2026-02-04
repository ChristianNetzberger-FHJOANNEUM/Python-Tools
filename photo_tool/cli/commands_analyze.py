"""
Photo analysis commands (bursts, quality, similarity)
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..workspace import Workspace
from ..config import load_config
from ..io import scan_multiple_directories, get_capture_time
from ..analysis import group_by_time, cluster_similar_photos
from ..analysis.similarity import detect_blur, compute_phash, HashMethod
from ..util.timing import timer


app = typer.Typer()
console = Console()


@app.command("bursts")
def find_bursts(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    time_window: Optional[float] = typer.Option(None, "--time-window", help="Override time window (seconds)"),
    threshold: Optional[int] = typer.Option(None, "--threshold", help="Override similarity threshold"),
):
    """
    Find burst photo sequences
    
    Example:
        photo-tool analyze bursts
        photo-tool analyze bursts --time-window 5.0 --threshold 8
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        # Override config if provided
        if time_window is not None:
            config.grouping.time_window_seconds = time_window
        if threshold is not None:
            config.similarity.phash_threshold = threshold
        
        console.print("[bold]Finding burst sequences...[/bold]\n")
        
        # Step 1: Scan photos
        console.print("Step 1: Scanning photos...")
        with timer("Scan"):
            photos = scan_multiple_directories(
                config.scan.roots,
                config.scan.extensions,
                config.scan.recurse,
                show_progress=True
            )
        
        if not photos:
            console.print("[yellow]No photos found[/yellow]")
            return
        
        # Step 2: Get capture times
        console.print("\nStep 2: Reading capture times...")
        capture_times = []
        photo_paths = []
        
        for photo in photos:
            capture_time = get_capture_time(photo.path)
            if capture_time:
                capture_times.append(capture_time)
                photo_paths.append(photo.path)
        
        console.print(f"  Photos with timestamps: {len(photo_paths)}")
        
        # Step 3: Time-based grouping
        console.print("\nStep 3: Grouping by time...")
        with timer("Time grouping"):
            time_groups = group_by_time(
                photo_paths,
                capture_times,
                config.grouping.time_window_seconds,
                config.grouping.max_group_gap_seconds
            )
        
        console.print(f"  Found {len(time_groups)} candidate groups")
        
        if not time_groups:
            console.print("[yellow]No burst sequences found[/yellow]")
            return
        
        # Step 4: Visual similarity clustering
        console.print("\nStep 4: Analyzing visual similarity...")
        
        # Optionally compute blur scores
        console.print("  Computing blur scores...")
        blur_scores = {}
        for group in time_groups:
            for photo in group.photos:
                try:
                    score = detect_blur(photo)
                    blur_scores[photo] = score
                except:
                    pass
        
        with timer("Clustering"):
            hash_method = HashMethod(config.similarity.method)
            clusters = cluster_similar_photos(
                time_groups,
                hash_method=hash_method,
                similarity_threshold=config.similarity.phash_threshold,
                blur_scores=blur_scores,
                show_progress=True
            )
        
        # Show results
        console.print(f"\n[green]✓[/green] Found {len(clusters)} burst sequences")
        
        table = Table(title="Burst Sequences")
        table.add_column("#", style="cyan")
        table.add_column("Photos", style="magenta")
        table.add_column("Best Photo", style="green")
        
        for i, cluster in enumerate(sorted(clusters, key=lambda c: c.count, reverse=True), 1):
            table.add_row(
                str(i),
                str(cluster.count),
                cluster.best_photo.name
            )
        
        console.print(table)
        
        console.print(f"\nNext: photo-tool organize bursts --dry-run")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("quality")
def analyze_quality(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    blur_only: bool = typer.Option(False, "--blur-only", help="Only detect blur"),
    top: int = typer.Option(20, "--top", help="Show top N results"),
):
    """
    Analyze photo quality (blur, exposure, etc.)
    
    Example:
        photo-tool analyze quality --top 50
        photo-tool analyze quality --blur-only
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        console.print("[bold]Analyzing photo quality...[/bold]\n")
        
        # Scan photos
        photos = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=True
        )
        
        if not photos:
            console.print("[yellow]No photos found[/yellow]")
            return
        
        # Compute blur scores
        console.print("\nComputing blur scores...")
        blur_results = []
        
        for photo in photos:
            try:
                score = detect_blur(photo.path)
                blur_results.append((photo.path, score))
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not analyze {photo.filename}: {e}")
        
        # Sort by score (lower = more blurry)
        blur_results.sort(key=lambda x: x[1])
        
        # Show results
        table = Table(title=f"Top {top} Blurriest Photos")
        table.add_column("#", style="cyan")
        table.add_column("Photo", style="white")
        table.add_column("Blur Score", style="red")
        
        for i, (photo, score) in enumerate(blur_results[:top], 1):
            table.add_row(str(i), photo.name, f"{score:.2f}")
        
        console.print(table)
        
        # Statistics
        console.print(f"\nStatistics:")
        scores = [s for _, s in blur_results]
        console.print(f"  Mean blur score: {sum(scores) / len(scores):.2f}")
        console.print(f"  Min (blurriest): {min(scores):.2f}")
        console.print(f"  Max (sharpest):  {max(scores):.2f}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
