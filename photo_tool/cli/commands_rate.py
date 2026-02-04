"""
Rating commands for photos and videos
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..actions.rating import set_rating, get_rating_with_comment


app = typer.Typer()
console = Console()


@app.command("set")
def rate_file(
    file: Path = typer.Argument(..., help="Path to photo or video"),
    stars: int = typer.Option(..., "--stars", "-s", min=0, max=5, help="Rating (0-5 stars)"),
    comment: Optional[str] = typer.Option(None, "--comment", "-c", help="Optional comment"),
):
    """
    Rate a photo or video file
    
    Example:
        photo-tool rate set VIDEO001.mp4 --stars 5
        photo-tool rate set photo.jpg --stars 4 --comment "Great shot"
    """
    try:
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1)
        
        set_rating(file, stars, comment)
        
        console.print(f"[green]✓[/green] Set rating for {file.name}:")
        console.print(f"  Stars: {'⭐' * stars}")
        if comment:
            console.print(f"  Comment: {comment}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("get")
def get_rating_cmd(
    file: Path = typer.Argument(..., help="Path to photo or video"),
):
    """
    Get rating for a file
    
    Example:
        photo-tool rate get VIDEO001.mp4
    """
    try:
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1)
        
        rating, comment = get_rating_with_comment(file)
        
        if rating is None:
            console.print(f"[yellow]No rating set for {file.name}[/yellow]")
        else:
            console.print(f"[bold]{file.name}[/bold]")
            console.print(f"  Stars: {'⭐' * rating} ({rating}/5)")
            if comment:
                console.print(f"  Comment: {comment}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
