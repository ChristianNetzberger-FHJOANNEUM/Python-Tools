"""
Main CLI entry point
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .. import __version__
from ..util.logging import setup_logging

# Import command modules
from . import commands_workspace
from . import commands_scan
from . import commands_analyze
from . import commands_organize
from . import commands_report


# Create main app
app = typer.Typer(
    name="photo-tool",
    help="Modern photo management tool for organizing and curating photo collections",
    add_completion=False
)

console = Console()


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Photo Tool - Modern photo management"""
    
    # Setup logging
    if debug:
        log_level = "DEBUG"
    elif verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"
    
    setup_logging(level=log_level)


@app.command()
def version():
    """Show version information"""
    console.print(f"Photo Tool v{__version__}")


# Add subcommands
app.add_typer(commands_workspace.app, name="workspace", help="Workspace management")
app.add_typer(commands_scan.app, name="scan", help="Scan and index photos")
app.add_typer(commands_analyze.app, name="analyze", help="Analyze photos (bursts, quality)")
app.add_typer(commands_organize.app, name="organize", help="Organize and deduplicate")
app.add_typer(commands_report.app, name="report", help="Generate reports")


if __name__ == "__main__":
    app()
