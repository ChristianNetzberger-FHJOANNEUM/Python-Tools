"""
Video-specific commands
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..workspace import Workspace
from ..config import load_config
from ..io import (
    extract_video_metadata,
    get_video_capture_time,
    is_ffprobe_available,
    format_duration,
    format_file_size
)


app = typer.Typer()
console = Console()


@app.command("info")
def video_info(
    video: Path = typer.Argument(..., help="Path to video file"),
):
    """
    Show detailed information about a video file
    
    Example:
        photo-tool video info F:/Lumix/VIDEO001.mp4
    """
    try:
        if not video.exists():
            console.print(f"[red]Error:[/red] File not found: {video}")
            raise typer.Exit(1)
        
        # Check if ffprobe is available
        if not is_ffprobe_available():
            console.print("[yellow]Warning:[/yellow] ffprobe not found!")
            console.print("Install ffmpeg to get detailed video information:")
            console.print("  https://ffmpeg.org/download.html")
            console.print()
        
        console.print(f"[bold]Video information for:[/bold] {video.name}\n")
        
        # Get metadata
        metadata = extract_video_metadata(video)
        
        # Get capture time
        capture_time = get_video_capture_time(video)
        
        # Create table
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        # Add rows
        table.add_row("Filename", video.name)
        table.add_row("Path", str(video.parent))
        table.add_row("Size", format_file_size(metadata.get('size_bytes', 0)))
        
        if capture_time:
            table.add_row("Captured", capture_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        duration = metadata.get('duration', 0)
        if duration > 0:
            table.add_row("Duration", format_duration(duration))
        
        width = metadata.get('width', 0)
        height = metadata.get('height', 0)
        if width > 0 and height > 0:
            table.add_row("Resolution", f"{width}x{height}")
        
        fps = metadata.get('fps', 0)
        if fps > 0:
            table.add_row("Frame Rate", f"{fps:.2f} fps")
        
        codec = metadata.get('codec', 'unknown')
        if codec != 'unknown':
            table.add_row("Codec", codec)
        
        bit_rate = metadata.get('bit_rate', 0)
        if bit_rate > 0:
            table.add_row("Bit Rate", f"{bit_rate / 1_000_000:.1f} Mbps")
        
        format_name = metadata.get('format_name', 'unknown')
        if format_name != 'unknown':
            table.add_row("Format", format_name)
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("list")
def list_videos(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    sort_by: str = typer.Option("name", "--sort", help="Sort by: name, size, date, duration"),
):
    """
    List all videos in workspace with metadata
    
    Example:
        photo-tool video list --workspace D:/PhotoWorkspace
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        from ..io import scan_multiple_directories, filter_by_type
        
        console.print("[bold]Scanning for videos...[/bold]\n")
        
        # Scan for all media
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=True
        )
        
        # Filter videos only
        videos = filter_by_type(all_media, "video")
        
        if not videos:
            console.print("[yellow]No videos found[/yellow]")
            return
        
        console.print(f"\nFound {len(videos)} videos")
        
        # Get metadata for all videos
        console.print("\nCollecting video information...")
        video_data = []
        
        for video in videos:
            try:
                metadata = extract_video_metadata(video.path)
                capture_time = get_video_capture_time(video.path)
                
                video_data.append({
                    'path': video.path,
                    'name': video.filename,
                    'size': metadata.get('size_bytes', 0),
                    'duration': metadata.get('duration', 0),
                    'date': capture_time,
                    'resolution': f"{metadata.get('width', 0)}x{metadata.get('height', 0)}",
                })
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not read {video.filename}: {e}")
        
        # Sort
        if sort_by == "size":
            video_data.sort(key=lambda x: x['size'], reverse=True)
        elif sort_by == "date":
            video_data.sort(key=lambda x: x['date'] or '', reverse=True)
        elif sort_by == "duration":
            video_data.sort(key=lambda x: x['duration'], reverse=True)
        else:  # name
            video_data.sort(key=lambda x: x['name'])
        
        # Display table
        table = Table(title="Videos")
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="magenta")
        table.add_column("Duration", style="green")
        table.add_column("Resolution", style="blue")
        table.add_column("Date", style="yellow")
        
        for vid in video_data:
            table.add_row(
                vid['name'],
                format_file_size(vid['size']),
                format_duration(vid['duration']),
                vid['resolution'],
                vid['date'].strftime("%Y-%m-%d") if vid['date'] else "Unknown"
            )
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
