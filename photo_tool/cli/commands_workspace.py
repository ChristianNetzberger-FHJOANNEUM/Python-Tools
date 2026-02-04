"""
Workspace management commands
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from ..workspace import create_workspace, Workspace
from ..config import load_config


app = typer.Typer()
console = Console()


@app.command("init")
def init_workspace(
    path: Path = typer.Argument(..., help="Workspace directory path"),
    scan_roots: Optional[List[Path]] = typer.Option(None, "--root", help="Photo source directories"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing workspace"),
):
    """
    Initialize a new workspace
    
    Example:
        photo-tool workspace init D:/PhotoWorkspace --root E:/Photos --root F:/Camera
    """
    try:
        workspace = create_workspace(path, scan_roots=scan_roots, force=force)
        
        console.print(f"[green]✓[/green] Workspace created: {workspace.root}")
        console.print(f"\nNext steps:")
        console.print(f"  1. Edit configuration: {workspace.config_file}")
        console.print(f"  2. Run: photo-tool scan")
        console.print(f"  3. Run: photo-tool analyze bursts --dry-run")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("info")
def workspace_info(
    workspace: Path = typer.Option(".", "--workspace", "-w", help="Workspace directory")
):
    """Show workspace information"""
    try:
        ws = Workspace(workspace)
        
        if not ws.exists():
            console.print(f"[red]Error:[/red] Not a valid workspace: {workspace}")
            raise typer.Exit(1)
        
        console.print(f"[bold]Workspace:[/bold] {ws.root}")
        console.print(f"\nDirectories:")
        console.print(f"  Config:     {ws.config_file}")
        console.print(f"  Cache:      {ws.cache_dir}")
        console.print(f"  Database:   {ws.db_file}")
        console.print(f"  Reports:    {ws.reports_dir}")
        console.print(f"  Exports:    {ws.exports_dir}")
        
        # Load config
        config = load_config(ws.config_file)
        console.print(f"\nScan roots:")
        if config.scan.roots:
            for root in config.scan.roots:
                console.print(f"  - {root}")
        else:
            console.print("  (none configured)")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
