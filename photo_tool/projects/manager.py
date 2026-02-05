"""
Project Manager for Photo Tool
Handles project creation, loading, saving, and deletion
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from ..util.logging import get_logger

logger = get_logger("projects")


@dataclass
class ProjectFilters:
    """Filter criteria for photo selection"""
    ratings: Optional[List[int]] = None
    colors: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    in_bursts: Optional[bool] = None
    date_range: Optional[Dict[str, str]] = None


@dataclass
class ExportSettings:
    """Export settings for the project"""
    slideshow_enabled: bool = True
    slideshow_duration: int = 5
    smart_tv_mode: bool = False
    template: str = "photoswipe"
    music_files: Optional[List[str]] = None


@dataclass
class Project:
    """Represents a photo project/collection"""
    id: str
    name: str
    created: str
    updated: str
    
    # Photo selection
    selection_mode: str  # 'filter', 'explicit', 'hybrid'
    filters: Optional[ProjectFilters] = None
    photo_ids: Optional[List[str]] = None
    manual_additions: Optional[List[str]] = None
    manual_exclusions: Optional[List[str]] = None
    
    # Export settings
    export_settings: Optional[ExportSettings] = None
    
    # Metadata
    exports: Optional[List[Dict[str, Any]]] = None
    stats: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Clean up None values
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary"""
        # Convert nested dicts to dataclasses
        if 'filters' in data and data['filters']:
            data['filters'] = ProjectFilters(**data['filters'])
        if 'export_settings' in data and data['export_settings']:
            data['export_settings'] = ExportSettings(**data['export_settings'])
        return cls(**data)


class ProjectManager:
    """Manages projects for a workspace"""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.projects_dir = workspace_path / "projects"
        self.projects_file = self.projects_dir / "projects.yaml"
        
        # Ensure directories exist
        self.projects_dir.mkdir(exist_ok=True)
        
        # Load or create project index
        self._load_index()
    
    def _load_index(self):
        """Load project index from file"""
        if self.projects_file.exists():
            try:
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.index = yaml.safe_load(f) or {'projects': []}
            except Exception as e:
                logger.error(f"Failed to load project index: {e}")
                self.index = {'projects': []}
        else:
            self.index = {'projects': []}
    
    def _save_index(self):
        """Save project index to file"""
        try:
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.index, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Failed to save project index: {e}")
            raise
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects with summary info"""
        return self.index.get('projects', [])
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Load a specific project"""
        project_file = self.projects_dir / f"{project_id}.yaml"
        
        if not project_file.exists():
            logger.warning(f"Project file not found: {project_id}")
            return None
        
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            return Project.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load project {project_id}: {e}")
            return None
    
    def save_project(self, project: Project) -> bool:
        """Save a project"""
        try:
            # Update timestamp
            project.updated = datetime.now().isoformat()
            
            # Save project file
            project_file = self.projects_dir / f"{project.id}.yaml"
            with open(project_file, 'w', encoding='utf-8') as f:
                yaml.dump(project.to_dict(), f, default_flow_style=False, allow_unicode=True)
            
            # Update index
            existing = next((p for p in self.index['projects'] if p['id'] == project.id), None)
            
            summary = {
                'id': project.id,
                'name': project.name,
                'created': project.created,
                'updated': project.updated,
                'selection_mode': project.selection_mode,
                'photo_count': len(project.photo_ids) if project.photo_ids else 0,
                'has_filters': project.filters is not None,
                'has_music': bool(project.export_settings and project.export_settings.music_files),
                'export_count': len(project.exports) if project.exports else 0
            }
            
            if existing:
                # Update existing
                idx = self.index['projects'].index(existing)
                self.index['projects'][idx] = summary
            else:
                # Add new
                self.index['projects'].append(summary)
            
            self._save_index()
            
            logger.info(f"Saved project: {project.name} ({project.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False
    
    def create_project(
        self,
        name: str,
        selection_mode: str,
        filters: Optional[Dict[str, Any]] = None,
        photo_ids: Optional[List[str]] = None,
        export_settings: Optional[Dict[str, Any]] = None
    ) -> Project:
        """Create a new project"""
        
        # Generate ID from name
        project_id = name.lower().replace(' ', '-').replace('/', '-')
        # Add timestamp if ID exists
        if any(p['id'] == project_id for p in self.index['projects']):
            project_id = f"{project_id}-{int(datetime.now().timestamp())}"
        
        now = datetime.now().isoformat()
        
        # Create project
        project = Project(
            id=project_id,
            name=name,
            created=now,
            updated=now,
            selection_mode=selection_mode,
            filters=ProjectFilters(**filters) if filters else None,
            photo_ids=photo_ids,
            export_settings=ExportSettings(**export_settings) if export_settings else None,
            exports=[],
            stats={}
        )
        
        # Save it
        self.save_project(project)
        
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        try:
            # Delete project file
            project_file = self.projects_dir / f"{project_id}.yaml"
            if project_file.exists():
                project_file.unlink()
            
            # Remove from index
            self.index['projects'] = [p for p in self.index['projects'] if p['id'] != project_id]
            self._save_index()
            
            logger.info(f"Deleted project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False
    
    def add_export_record(self, project_id: str, export_info: Dict[str, Any]) -> bool:
        """Add export record to project"""
        try:
            project = self.get_project(project_id)
            if not project:
                return False
            
            if not project.exports:
                project.exports = []
            
            export_record = {
                'date': datetime.now().isoformat(),
                **export_info
            }
            
            project.exports.append(export_record)
            
            return self.save_project(project)
            
        except Exception as e:
            logger.error(f"Failed to add export record: {e}")
            return False
