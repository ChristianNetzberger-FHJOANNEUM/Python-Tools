"""
Photo scanning commands
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..workspace import Workspace
from ..config import load_config
from ..io import (
    scan_directory,
    scan_multiple_directories,
    extract_exif,
    get_capture_time,
    filter_by_type,
    extract_video_metadata,
    get_video_capture_time
)
from ..util.timing import timer


app = typer.Typer()
console = Console()


@app.command()
def scan(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    roots: Optional[List[Path]] = typer.Option(None, "--root", help="Override scan roots"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Scan subdirectories"),
):
    """
    Scan photo directories and build index
    
    Example:
        photo-tool scan --workspace D:/PhotoWorkspace
        photo-tool scan --root E:/Photos --root F:/Camera
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        # Determine which directories to scan
        scan_roots = roots if roots else config.scan.roots
        
        if not scan_roots:
            console.print("[red]Error:[/red] No scan roots configured")
            console.print("Add roots to config.yaml or use --root option")
            raise typer.Exit(1)
        
        console.print(f"[bold]Scanning directories...[/bold]")
        
        with timer("Scan completed"):
            media_files = scan_multiple_directories(
                scan_roots,
                config.scan.extensions,
                recursive=recursive,
                show_progress=True
            )
        
        # Count by type
        photos = filter_by_type(media_files, "photo")
        videos = filter_by_type(media_files, "video")
        audio = filter_by_type(media_files, "audio")
        
        console.print(f"\n[green]✓[/green] Found {len(media_files)} files:")
        console.print(f"  Photos: {len(photos)}")
        console.print(f"  Videos: {len(videos)}")
        console.print(f"  Audio: {len(audio)}")
        
        # Show summary table
        table = Table(title="Scan Summary")
        table.add_column("Statistic", style="cyan")
        table.add_column("Value", style="magenta")
        
        total_size = sum(m.size_bytes for m in media_files)
        table.add_row("Total files", str(len(media_files)))
        table.add_row("Photos", str(len(photos)))
        table.add_row("Videos", str(len(videos)))
        table.add_row("Audio", str(len(audio)))
        table.add_row("Total size", f"{total_size / (1024**3):.2f} GB")
        
        # Extension breakdown
        extensions = {}
        for m in media_files:
            ext = m.extension
            extensions[ext] = extensions.get(ext, 0) + 1
        
        table.add_row("", "")  # Separator
        table.add_row("[bold]By extension", "")
        for ext, count in sorted(extensions.items()):
            table.add_row(f"  {ext}", str(count))
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("exif")
def show_exif(
    photo: Path = typer.Argument(..., help="Path to photo"),
):
    """Show EXIF metadata for a photo"""
    try:
        if not photo.exists():
            console.print(f"[red]Error:[/red] File not found: {photo}")
            raise typer.Exit(1)
        
        console.print(f"[bold]EXIF data for:[/bold] {photo.name}\n")
        
        exif = extract_exif(photo)
        
        if not exif:
            console.print("[yellow]No EXIF data found[/yellow]")
            return
        
        # Show key fields
        capture_time = get_capture_time(photo)
        if capture_time:
            console.print(f"[cyan]Capture time:[/cyan] {capture_time}")
        
        # Show all EXIF tags
        console.print("\n[bold]All EXIF tags:[/bold]")
        for key, value in sorted(exif.items()):
            console.print(f"  {key}: {value}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
