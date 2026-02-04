"""
Audio-specific commands
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..workspace import Workspace
from ..config import load_config
from ..io import (
    extract_audio_metadata,
    get_audio_capture_time,
    format_duration,
    format_file_size
)
from ..io.audio_metadata import format_sample_rate, format_channels


app = typer.Typer()
console = Console()


@app.command("info")
def audio_info(
    audio: Path = typer.Argument(..., help="Path to audio file"),
):
    """
    Show detailed information about an audio file
    
    Example:
        photo-tool audio info F:/Sounds/recording.mp3
    """
    try:
        if not audio.exists():
            console.print(f"[red]Error:[/red] File not found: {audio}")
            raise typer.Exit(1)
        
        # Check if ffprobe is available
        from ..io.video_metadata import is_ffprobe_available
        
        if not is_ffprobe_available():
            console.print("[yellow]Warning:[/yellow] ffprobe not found!")
            console.print("Install ffmpeg to get detailed audio information:")
            console.print("  https://ffmpeg.org/download.html")
            console.print()
        
        console.print(f"[bold]Audio information for:[/bold] {audio.name}\n")
        
        # Get metadata
        metadata = extract_audio_metadata(audio)
        
        # Get capture time
        capture_time = get_audio_capture_time(audio)
        
        # Create table
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        # Add rows
        table.add_row("Filename", audio.name)
        table.add_row("Path", str(audio.parent))
        table.add_row("Size", format_file_size(metadata.get('size_bytes', 0)))
        
        if capture_time:
            table.add_row("Date", capture_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        duration = metadata.get('duration', 0)
        if duration > 0:
            table.add_row("Duration", format_duration(duration))
        
        # Audio-specific metadata
        title = metadata.get('title', '')
        if title:
            table.add_row("Title", title)
        
        artist = metadata.get('artist', '')
        if artist:
            table.add_row("Artist", artist)
        
        album = metadata.get('album', '')
        if album:
            table.add_row("Album", album)
        
        genre = metadata.get('genre', '')
        if genre:
            table.add_row("Genre", genre)
        
        # Technical details
        sample_rate = metadata.get('sample_rate', 0)
        if sample_rate > 0:
            table.add_row("Sample Rate", format_sample_rate(sample_rate))
        
        channels = metadata.get('channels', 0)
        channel_layout = metadata.get('channel_layout', '')
        if channels > 0:
            table.add_row("Channels", format_channels(channels, channel_layout))
        
        codec = metadata.get('codec', 'unknown')
        if codec != 'unknown':
            table.add_row("Codec", codec)
        
        bit_rate = metadata.get('bit_rate', 0)
        if bit_rate > 0:
            table.add_row("Bit Rate", f"{bit_rate / 1000:.0f} kbps")
        
        format_name = metadata.get('format_name', 'unknown')
        if format_name != 'unknown':
            table.add_row("Format", format_name)
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("list")
def list_audio(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    sort_by: str = typer.Option("name", "--sort", help="Sort by: name, size, date, duration"),
):
    """
    List all audio files in workspace with metadata
    
    Example:
        photo-tool audio list --workspace D:/MediaWorkspace
        photo-tool audio list --sort duration
    """
    try:
        ws = Workspace(workspace)
        config = load_config(ws.config_file)
        
        from ..io import scan_multiple_directories, filter_by_type
        
        console.print("[bold]Scanning for audio files...[/bold]\n")
        
        # Scan for all media
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=True
        )
        
        # Filter audio only
        audio_files = filter_by_type(all_media, "audio")
        
        if not audio_files:
            console.print("[yellow]No audio files found[/yellow]")
            return
        
        console.print(f"\nFound {len(audio_files)} audio files")
        
        # Get metadata for all audio files
        console.print("\nCollecting audio information...")
        audio_data = []
        
        for audio in audio_files:
            try:
                metadata = extract_audio_metadata(audio.path)
                capture_time = get_audio_capture_time(audio.path)
                
                audio_data.append({
                    'path': audio.path,
                    'name': audio.filename,
                    'size': metadata.get('size_bytes', 0),
                    'duration': metadata.get('duration', 0),
                    'date': capture_time,
                    'title': metadata.get('title', ''),
                    'artist': metadata.get('artist', ''),
                    'sample_rate': format_sample_rate(metadata.get('sample_rate', 0)),
                })
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not read {audio.filename}: {e}")
        
        # Sort
        if sort_by == "size":
            audio_data.sort(key=lambda x: x['size'], reverse=True)
        elif sort_by == "date":
            audio_data.sort(key=lambda x: x['date'] or '', reverse=True)
        elif sort_by == "duration":
            audio_data.sort(key=lambda x: x['duration'], reverse=True)
        else:  # name
            audio_data.sort(key=lambda x: x['name'])
        
        # Display table
        table = Table(title="Audio Files")
        table.add_column("Name", style="cyan")
        table.add_column("Title/Artist", style="white")
        table.add_column("Duration", style="green")
        table.add_column("Size", style="magenta")
        table.add_column("Sample Rate", style="blue")
        
        for aud in audio_data:
            # Combine title and artist
            title_artist = ""
            if aud['title'] and aud['artist']:
                title_artist = f"{aud['title']} - {aud['artist']}"
            elif aud['title']:
                title_artist = aud['title']
            elif aud['artist']:
                title_artist = f"by {aud['artist']}"
            
            table.add_row(
                aud['name'],
                title_artist or "[dim]No metadata[/dim]",
                format_duration(aud['duration']),
                format_file_size(aud['size']),
                aud['sample_rate']
            )
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
