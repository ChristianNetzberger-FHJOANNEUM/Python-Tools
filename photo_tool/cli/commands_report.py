"""
Report generation commands
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..workspace import Workspace
from ..config import load_config
from ..io import scan_multiple_directories, get_capture_time
from ..analysis import group_by_time, cluster_similar_photos
from ..analysis.similarity import detect_blur, HashMethod
from ..report import generate_text_report, generate_html_report
from ..util.timing import timer


app = typer.Typer()
console = Console()


@app.command()
def generate(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    format: str = typer.Option("text", "--format", "-f", help="Report format: text, html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    thumbnails: bool = typer.Option(True, "--thumbnails/--no-thumbnails", help="Include thumbnails (HTML only)"),
):
    """
    Generate analysis report
    
    Example:
        photo-tool report generate --format text
        photo-tool report generate --format html --output report.html
        photo-tool report generate --format html --no-thumbnails
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        console.print("[bold]Generating report...[/bold]\n")
        
        # Analyze photos
        console.print("Scanning and analyzing photos...")
        
        photos = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=True
        )
        
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
        
        # Group and cluster
        time_groups = group_by_time(
            photo_paths,
            capture_times,
            config.grouping.time_window_seconds,
            config.grouping.max_group_gap_seconds
        )
        
        # Blur scores
        blur_scores = {}
        if format == "html" or config.quality.compute_histogram:
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
        
        console.print(f"\nFound {len(clusters)} photo clusters")
        
        # Generate report
        console.print(f"\nGenerating {format.upper()} report...")
        
        if format == "text":
            # Determine output path
            if not output:
                output = ws.reports_dir / "cluster_report.txt"
            
            with timer("Report generation"):
                report_text = generate_text_report(clusters, output, include_blur_scores=True)
            
            # Also print to console
            console.print("\n" + "="*80)
            console.print(report_text)
        
        elif format == "html":
            # Determine output path
            if not output:
                output = ws.reports_dir / "cluster_report.html"
            
            with timer("Report generation"):
                generate_html_report(
                    clusters,
                    output,
                    ws.thumbnails_dir,
                    include_thumbnails=thumbnails
                )
        
        else:
            console.print(f"[red]Error:[/red] Unknown format: {format}")
            raise typer.Exit(1)
        
        console.print(f"\n[green]✓[/green] Report saved to: {output}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
