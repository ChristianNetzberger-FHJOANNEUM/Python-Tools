"""
Workspace initialization
"""

from pathlib import Path
from typing import List, Optional

from .model import Workspace
from ..config import PhotoToolConfig, save_config
from ..config.schema import WorkspaceConfig, ScanConfig
from ..util.logging import get_logger


logger = get_logger("workspace")


def create_workspace(
    path: Path,
    scan_roots: Optional[List[Path]] = None,
    force: bool = False
) -> Workspace:
    """
    Create a new workspace with default configuration
    
    Args:
        path: Root directory for workspace
        scan_roots: Optional list of source directories to scan
        force: Overwrite existing workspace
        
    Returns:
        Initialized Workspace object
    """
    workspace = Workspace(path)
    
    # Check if exists
    if workspace.exists() and not force:
        logger.warning(f"Workspace already exists at {path}")
        logger.info("Use --force to reinitialize")
        return workspace
    
    logger.info(f"Creating workspace at {path}")
    
    # Create directory structure
    workspace.ensure_structure()
    
    # Create default configuration
    config = PhotoToolConfig(
        workspace=WorkspaceConfig(path=workspace.root),
        scan=ScanConfig(roots=scan_roots or [])
    )
    
    # Save config
    save_config(config, workspace.config_file)
    
    # Create README
    readme_path = workspace.root / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(_get_workspace_readme(workspace))
    
    logger.info("Workspace created successfully")
    logger.info(f"Edit configuration: {workspace.config_file}")
    
    return workspace


def _get_workspace_readme(workspace: Workspace) -> str:
    """Generate workspace README content"""
    return f"""# Photo Tool Workspace

This directory contains a photo management workspace.

## Directory Structure

- `config.yaml` - Configuration file (edit this to customize settings)
- `cache/` - Cached thumbnails and hashes (safe to delete)
- `db/` - Photo index database
- `reports/` - Generated analysis reports
- `exports/` - Processed/exported images
- `logs/` - Application logs

## Getting Started

1. Edit `config.yaml` to add your photo source directories
2. Run `photo-tool scan` to index your photos
3. Run `photo-tool group-bursts --dry-run` to preview burst detection
4. Run `photo-tool apply --move-bursts` to organize photos

## Configuration

See `config.yaml` for all available settings:
- Time window for burst detection
- Similarity thresholds
- Quality analysis parameters
- Action settings (dry-run, folder naming, etc.)

## Commands

```bash
# Scan photos
photo-tool scan

# Find bursts
photo-tool group-bursts --dry-run

# Generate report
photo-tool report --format text

# Apply organization
photo-tool apply --move-bursts

# Quality analysis
photo-tool quality --detect-blur
```

Created: {workspace.root}
"""
