"""
Workspace Manager
Handles multiple workspaces and folder activation
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config import load_config, save_config
from ..util.logging import get_logger
from .model import Workspace

logger = get_logger("workspace_manager")


class FolderInfo:
    """Information about a media folder"""
    
    def __init__(self, path: str, enabled: bool = True, photo_count: int = 0, last_scan: Optional[str] = None):
        self.path = path
        self.enabled = enabled
        self.photo_count = photo_count
        self.last_scan = last_scan or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'enabled': self.enabled,
            'photo_count': self.photo_count,
            'last_scan': self.last_scan
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FolderInfo':
        return cls(
            path=data['path'],
            enabled=data.get('enabled', True),
            photo_count=data.get('photo_count', 0),
            last_scan=data.get('last_scan')
        )


class WorkspaceManager:
    """Manages multiple workspaces"""
    
    def __init__(self, workspaces_file: Path = None):
        # Default location for workspace list
        if workspaces_file is None:
            # Store in user's home directory
            home = Path.home()
            config_dir = home / ".photo_tool"
            config_dir.mkdir(exist_ok=True)
            workspaces_file = config_dir / "workspaces.json"
        
        self.workspaces_file = workspaces_file
        self._load_workspaces()
    
    def _load_workspaces(self):
        """Load workspace list from file"""
        if self.workspaces_file.exists():
            try:
                with open(self.workspaces_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.workspaces = data.get('workspaces', [])
                    self.current_workspace = data.get('current_workspace')
            except Exception as e:
                logger.error(f"Failed to load workspaces: {e}")
                self.workspaces = []
                self.current_workspace = None
        else:
            self.workspaces = []
            self.current_workspace = None
    
    def _save_workspaces(self):
        """Save workspace list to file"""
        try:
            data = {
                'workspaces': self.workspaces,
                'current_workspace': self.current_workspace
            }
            with open(self.workspaces_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workspaces: {e}")
            raise
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all registered workspaces"""
        return self.workspaces
    
    def get_current_workspace(self) -> Optional[str]:
        """Get current workspace path"""
        return self.current_workspace
    
    def add_workspace(self, path: Path, name: Optional[str] = None) -> bool:
        """Add a workspace to the list, creating it if it doesn't exist"""
        try:
            workspace = Workspace(path)
            
            # If workspace doesn't exist, create it
            if not workspace.exists():
                from ..workspace.init import create_workspace
                logger.info(f"Creating new workspace: {path}")
                create_workspace(path, scan_roots=[], force=False)
            
            path_str = str(path)
            
            # Check if already exists in list
            if any(ws['path'] == path_str for ws in self.workspaces):
                logger.info(f"Workspace already registered: {path}")
                return True
            
            # Load config to get name
            try:
                config = load_config(workspace.config_file)
                workspace_name = name or path.name
            except:
                workspace_name = name or path.name
            
            self.workspaces.append({
                'path': path_str,
                'name': workspace_name,
                'added': datetime.now().isoformat()
            })
            
            # Set as current if first workspace
            if len(self.workspaces) == 1:
                self.current_workspace = path_str
            
            self._save_workspaces()
            logger.info(f"Added workspace: {workspace_name} ({path})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add workspace: {e}")
            return False
    
    def switch_workspace(self, path: str) -> bool:
        """Switch to a different workspace"""
        try:
            if not any(ws['path'] == path for ws in self.workspaces):
                logger.error(f"Workspace not registered: {path}")
                return False
            
            self.current_workspace = path
            self._save_workspaces()
            
            logger.info(f"Switched to workspace: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch workspace: {e}")
            return False
    
    def remove_workspace(self, path: str) -> bool:
        """Remove a workspace from the list (doesn't delete files)"""
        try:
            self.workspaces = [ws for ws in self.workspaces if ws['path'] != path]
            
            if self.current_workspace == path:
                self.current_workspace = self.workspaces[0]['path'] if self.workspaces else None
            
            self._save_workspaces()
            logger.info(f"Removed workspace: {path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove workspace: {e}")
            return False
    
    def get_workspace_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a workspace"""
        try:
            workspace = Workspace(Path(path))
            
            if not workspace.exists():
                return None
            
            config = load_config(workspace.config_file)
            
            # Count folders and their status
            folders = []
            total_enabled = 0
            total_disabled = 0
            
            for root in config.scan.roots:
                # Check if folder info exists in config
                folder_enabled = True  # Default
                folder_count = 0
                
                # TODO: Get actual counts from scan cache
                
                folders.append({
                    'path': str(root),
                    'enabled': folder_enabled,
                    'photo_count': folder_count
                })
                
                if folder_enabled:
                    total_enabled += 1
                else:
                    total_disabled += 1
            
            return {
                'path': str(path),
                'name': Path(path).name,
                'folders': folders,
                'folder_stats': {
                    'total': len(folders),
                    'enabled': total_enabled,
                    'disabled': total_disabled
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get workspace info: {e}")
            return None


def get_workspace_folders(workspace_path: Path) -> List[FolderInfo]:
    """Get folder list with enabled status for a workspace"""
    try:
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        folders = []
        for root in config.scan.roots:
            # For now, default to enabled
            # Later we'll store this in config
            folders.append(FolderInfo(
                path=str(root),
                enabled=True,
                photo_count=0  # Will be updated during scan
            ))
        
        return folders
        
    except Exception as e:
        logger.error(f"Failed to get workspace folders: {e}")
        return []


def toggle_folder(workspace_path: Path, folder_path: str, enabled: bool) -> bool:
    """Toggle folder enabled status"""
    try:
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # For now, we'll use a simple approach:
        # Store enabled status in a separate file until we update config schema
        
        enabled_file = ws.root / "enabled_folders.json"
        
        # Load current enabled status
        if enabled_file.exists():
            with open(enabled_file, 'r') as f:
                enabled_folders = json.load(f)
        else:
            # Default: all enabled
            enabled_folders = {str(root): True for root in config.scan.roots}
        
        # Update status
        enabled_folders[folder_path] = enabled
        
        # Save
        with open(enabled_file, 'w') as f:
            json.dump(enabled_folders, f, indent=2)
        
        logger.info(f"Folder {folder_path} {'enabled' if enabled else 'disabled'}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to toggle folder: {e}")
        return False


def get_enabled_folders(workspace_path: Path) -> List[Path]:
    """Get list of enabled folders for scanning"""
    try:
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        enabled_file = ws.root / "enabled_folders.json"
        
        if enabled_file.exists():
            with open(enabled_file, 'r') as f:
                enabled_folders = json.load(f)
        else:
            # Default: all enabled
            enabled_folders = {str(root): True for root in config.scan.roots}
        
        # Return only enabled folders
        return [Path(path) for path, enabled in enabled_folders.items() if enabled]
        
    except Exception as e:
        logger.error(f"Failed to get enabled folders: {e}")
        return []
