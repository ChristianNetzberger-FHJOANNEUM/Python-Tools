"""
Project Manager for Photo Tool
Handles project creation, loading, saving, and deletion
"""

import copy
import re
import uuid
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, fields
from ..util.logging import get_logger
from ..config import load_config
from ..workspace import Workspace

logger = get_logger("projects")


def _folder_identity_key(path_str: str) -> str:
    """Normalize path for comparing workspace vs project folder entries (UNC-safe best-effort)."""
    try:
        return str(Path(path_str).resolve())
    except (OSError, ValueError):
        return str(Path(path_str))


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
    """Export settings for the project (persisted per project; Photo Tool export modal)."""
    slideshow_enabled: bool = True
    slideshow_duration: int = 5
    smart_tv_mode: bool = False
    template: str = "photoswipe"
    profile: str = "web"
    generate_webp: bool = False
    music_files: Optional[List[str]] = None
    music_autoplay: bool = False     # 🎵 Autoplay music on load
    music_ducking_volume: int = 30   # 🎚️ Music volume during pause (0-100%)
    quick_update: bool = False       # ⚡ Quick update (HTML only)
    splash_title: Optional[str] = None      # 🎬 Custom splash screen title
    splash_subtitle: Optional[str] = None   # 🎬 Custom splash screen subtitle
    remote_hub_ws_base: Optional[str] = None
    remote_session_id: str = "default"
    # If the slideshow is opened as file:///…, Hub still needs http(s) to slides.json — same folder as this export on the NAS
    gallery_public_http_base: Optional[str] = None
    # Parent folder for <output_name>/ (web root: index.html, slides.json, images/; empty = workspace/exports)
    export_base_path: Optional[str] = None
    project_to_couch_mode: str = "off"  # off | fill_empty | replace_all
    couch_import_slides_path: Optional[str] = None
    export_title: Optional[str] = None
    # Media tab rating layer preference (stored with export modal for convenience)
    active_rating_layer: str = "project"


@dataclass
class QualityDetectionSettings:
    """Quality detection settings for blur and burst detection"""
    # Blur detection
    blur_detection_enabled: bool = True
    blur_threshold: float = 100.0  # Laplacian variance threshold (lower = more blur)
    blur_auto_flag_color: str = "red"  # Auto-assign color to blurry photos
    
    # Burst detection
    burst_detection_enabled: bool = True
    burst_time_threshold: int = 3  # Max seconds between burst photos
    burst_similarity_threshold: float = 0.95  # Min similarity for burst grouping
    burst_auto_organize: bool = False  # Auto-move bursts to subfolders


@dataclass
class ProjectFolder:
    """Folder configuration for a project"""
    path: str
    enabled: bool = True
    photo_count: int = 0
    video_count: int = 0
    audio_count: int = 0


@dataclass
class Project:
    """Represents a photo project/collection"""
    id: str
    name: str
    created: str
    updated: str
    workspace_path: str  # Link to parent workspace
    
    # Folder selection (NEW!)
    folders: Optional[List[Dict[str, Any]]] = None  # List of ProjectFolder dicts
    
    # Photo selection
    selection_mode: str = 'filter'  # 'filter', 'explicit', 'hybrid'
    filters: Optional[ProjectFilters] = None
    photo_ids: Optional[List[str]] = None
    manual_additions: Optional[List[str]] = None
    manual_exclusions: Optional[List[str]] = None
    
    # Export settings (always mirrored from active export_profiles entry when profiles exist)
    export_settings: Optional[ExportSettings] = None
    
    # Named export targets (folder slug + full export_settings fields each); Couch/workflows per camera batch
    export_profiles: Optional[List[Dict[str, Any]]] = None
    active_export_profile_id: Optional[str] = None
    
    # Quality detection settings
    quality_settings: Optional[QualityDetectionSettings] = None
    
    # Metadata
    exports: Optional[List[Dict[str, Any]]] = None
    stats: Optional[Dict[str, Any]] = None

    # Audio library (paths under workspace-enabled folders; see /api/audio/*)
    audio_playlist: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Clean up None values
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary"""
        data = dict(data)

        ep_raw = data.get('export_profiles')
        raw_es = data.get('export_settings')
        if (
            (not ep_raw or not isinstance(ep_raw, list) or len(ep_raw) == 0)
            and isinstance(raw_es, dict)
        ):
            profs, aid = migrate_legacy_export_profiles(raw_es)
            data['export_profiles'] = profs
            data.setdefault('active_export_profile_id', aid)

        if 'filters' in data and data['filters']:
            data['filters'] = ProjectFilters(**data['filters'])
        if 'export_settings' in data:
            raw_es = data['export_settings']
            if raw_es is None:
                data['export_settings'] = None
            elif isinstance(raw_es, dict):
                data['export_settings'] = export_settings_from_dict(
                    raw_es if raw_es else {}
                )
            else:
                data['export_settings'] = None
        if 'quality_settings' in data and data['quality_settings']:
            data['quality_settings'] = QualityDetectionSettings(**data['quality_settings'])
        ap = data.get('audio_playlist')
        if ap is not None and not isinstance(ap, dict):
            data['audio_playlist'] = None

        proj = cls(**data)
        sync_export_settings_from_profiles(proj)
        return proj


def export_settings_from_dict(d: Optional[Dict[str, Any]]) -> Optional[ExportSettings]:
    """Build ExportSettings from YAML/API dict; ignore unknown keys (for forward compatibility)."""
    if d is None:
        return None
    if not isinstance(d, dict):
        return None
    allowed = {f.name for f in fields(ExportSettings)}
    filtered = {k: v for k, v in d.items() if k in allowed}
    try:
        return ExportSettings(**filtered)
    except TypeError:
        logger.warning("export_settings_from_dict: invalid fields, using defaults")
        return ExportSettings()


EXPORT_PROFILE_META_KEYS = frozenset({'id', 'slug', 'label'})


def slug_from_export_title(title: Optional[str]) -> str:
    """Folder slug from gallery title (same idea as gui exportGallery output_name)."""
    if not title or not str(title).strip():
        return 'default'
    s = str(title).lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s or 'default'


def export_profile_flat_to_settings(flat: Dict[str, Any]) -> ExportSettings:
    """One export profile dict → ExportSettings (strips id/slug/label)."""
    inner = {k: v for k, v in flat.items() if k not in EXPORT_PROFILE_META_KEYS}
    return export_settings_from_dict(inner) or ExportSettings()


def export_profile_to_flat_dict(
    profile_id: str,
    slug: str,
    label: Optional[str],
    es: ExportSettings,
) -> Dict[str, Any]:
    """Serialize one named export profile for YAML/API (flat: meta + ExportSettings fields)."""
    d = asdict(es)
    d['id'] = profile_id
    d['slug'] = (slug or '').strip() or 'default'
    if label is not None and str(label).strip():
        d['label'] = str(label).strip()
    return d


def merge_export_settings_into_active_profile(project: 'Project') -> None:
    """Copy project.export_settings fields into the active export_profiles row (if any)."""
    es = project.export_settings
    if not es or not project.export_profiles:
        return
    aid = project.active_export_profile_id
    payload = asdict(es)
    for p in project.export_profiles:
        if isinstance(p, dict) and p.get('id') == aid:
            for k, v in payload.items():
                p[k] = v
            return


def sync_export_settings_from_profiles(project: 'Project') -> None:
    """Mirror active profile into project.export_settings for legacy readers."""
    profiles = project.export_profiles
    if not profiles:
        return
    aid = project.active_export_profile_id
    prof = None
    for p in profiles:
        if isinstance(p, dict) and p.get('id') == aid:
            prof = p
            break
    if prof is None:
        prof = profiles[0] if isinstance(profiles[0], dict) else None
        if prof and prof.get('id'):
            project.active_export_profile_id = prof.get('id')
    if prof and isinstance(prof, dict):
        project.export_settings = export_profile_flat_to_settings(prof)


def migrate_legacy_export_profiles(
    export_settings_raw: Optional[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], str]:
    """Build a single export_profiles entry from legacy export_settings only."""
    es = export_settings_from_dict(export_settings_raw if isinstance(export_settings_raw, dict) else {})
    if es is None:
        es = ExportSettings()
    pid = str(uuid.uuid4())
    slug = slug_from_export_title(es.export_title)
    label = (es.export_title or '').strip() or None
    flat = export_profile_to_flat_dict(pid, slug, label, es)
    return [flat], pid


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
            
            sync_export_settings_from_profiles(project)

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
    
    def sync_folders_from_workspace(self, project_id: str) -> Optional[Project]:
        """
        Rebuild project.folders from the workspace config's folder list.
        Preserves enabled flag and counts for paths that still exist; new paths are disabled.
        Removes project entries that no longer exist on the workspace.
        """
        project = self.get_project(project_id)
        if not project:
            return None
        try:
            ws_root = Path(project.workspace_path)
        except Exception as e:
            logger.warning("sync_folders_from_workspace: bad workspace_path: %s", e)
            return project

        ws = Workspace(ws_root)
        if not ws.config_file.exists():
            logger.warning("sync_folders_from_workspace: missing %s", ws.config_file)
            return project

        config = load_config(ws.config_file)
        ws_folders = config.folders or []

        old_by_key: Dict[str, Dict[str, Any]] = {}
        for pf in project.folders or []:
            raw = pf.get("path")
            if not raw:
                continue
            old_by_key[_folder_identity_key(str(raw))] = dict(pf)

        merged: List[Dict[str, Any]] = []
        for wf in ws_folders:
            path = wf.get("path")
            if not path:
                continue
            key = _folder_identity_key(str(path))
            prev = old_by_key.get(key)
            pc = wf.get("photo_count")
            if pc is None:
                pc = (prev or {}).get("photo_count") or 0
            vc = wf.get("video_count")
            if vc is None:
                vc = (prev or {}).get("video_count") or 0
            ac = wf.get("audio_count")
            if ac is None:
                ac = (prev or {}).get("audio_count") or 0
            merged.append(
                {
                    "path": str(path),
                    "enabled": bool(prev.get("enabled")) if prev else False,
                    "photo_count": int(pc),
                    "video_count": int(vc),
                    "audio_count": int(ac),
                }
            )

        project.folders = merged
        self.save_project(project)
        logger.info(
            "sync_folders_from_workspace: project %s now has %s folders",
            project_id,
            len(merged),
        )
        return project

    def create_project(
        self,
        name: str,
        selection_mode: str,
        workspace_folders: Optional[List[Dict[str, Any]]] = None,
        filters: Optional[Dict[str, Any]] = None,
        photo_ids: Optional[List[str]] = None,
        export_settings: Optional[Dict[str, Any]] = None,
        quality_settings: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a new project
        
        Args:
            name: Project name
            selection_mode: Selection mode ('filter', 'explicit', 'hybrid')
            workspace_folders: Folders from workspace (will be disabled by default)
            filters: Optional filters
            photo_ids: Optional explicit photo IDs
            export_settings: Optional export settings
            quality_settings: Optional quality detection settings
        """
        
        # Generate ID from name
        project_id = name.lower().replace(' ', '-').replace('/', '-')
        # Add timestamp if ID exists
        if any(p['id'] == project_id for p in self.index['projects']):
            project_id = f"{project_id}-{int(datetime.now().timestamp())}"
        
        now = datetime.now().isoformat()
        
        # Initialize folders (all disabled by default)
        folders = None
        if workspace_folders:
            folders = []
            for wf in workspace_folders:
                folders.append({
                    'path': wf.get('path'),
                    'enabled': False,  # Disabled by default!
                    'photo_count': wf.get('photo_count', 0),
                    'video_count': wf.get('video_count', 0),
                    'audio_count': wf.get('audio_count', 0)
                })
        
        es_obj = export_settings_from_dict(export_settings) if export_settings else None
        profiles = None
        active_pid = None
        if es_obj:
            pid = str(uuid.uuid4())
            profiles = [
                export_profile_to_flat_dict(
                    pid,
                    slug_from_export_title(es_obj.export_title),
                    (es_obj.export_title or '').strip() or None,
                    es_obj,
                )
            ]
            active_pid = pid

        # Create project with default quality settings
        project = Project(
            id=project_id,
            name=name,
            created=now,
            updated=now,
            workspace_path=str(self.workspace_path),
            folders=folders,
            selection_mode=selection_mode,
            filters=ProjectFilters(**filters) if filters else None,
            photo_ids=photo_ids,
            export_settings=es_obj,
            export_profiles=profiles,
            active_export_profile_id=active_pid,
            quality_settings=QualityDetectionSettings(**quality_settings) if quality_settings else QualityDetectionSettings(),
            exports=[],
            stats={}
        )
        sync_export_settings_from_profiles(project)

        # Save it
        self.save_project(project)
        
        return project
    
    def clone_project(self, source_id: str, new_name: str) -> Optional[Project]:
        """Duplicate project folders, selection, export & quality settings; new id/name; empty export history."""
        src = self.get_project(source_id)
        if not src:
            return None
        name = (new_name or "").strip()
        if not name:
            return None
        base_id = name.lower().replace(" ", "-").replace("/", "-")
        project_id = base_id
        if any(p["id"] == project_id for p in self.index["projects"]):
            project_id = f"{base_id}-{int(datetime.now().timestamp())}"
        now = datetime.now().isoformat()
        dup_folders = copy.deepcopy(src.folders) if src.folders else None
        dup_filters = ProjectFilters(**asdict(src.filters)) if src.filters else None
        dup_photo_ids = list(src.photo_ids) if src.photo_ids else None
        dup_manual_add = list(src.manual_additions) if src.manual_additions else None
        dup_manual_exc = list(src.manual_exclusions) if src.manual_exclusions else None
        dup_export = (
            export_settings_from_dict(asdict(src.export_settings))
            if src.export_settings
            else None
        )
        dup_profiles = copy.deepcopy(src.export_profiles) if src.export_profiles else None
        dup_active = None
        if dup_profiles:
            id_map: Dict[str, str] = {}
            for p in dup_profiles:
                if not isinstance(p, dict):
                    continue
                oid = p.get('id')
                nid = str(uuid.uuid4())
                if isinstance(oid, str) and oid.strip():
                    id_map[oid.strip()] = nid
                p['id'] = nid
            old_active = src.active_export_profile_id
            if isinstance(old_active, str) and old_active.strip() in id_map:
                dup_active = id_map[old_active.strip()]
            elif dup_profiles and isinstance(dup_profiles[0], dict):
                dup_active = dup_profiles[0].get('id')
            dup_export = export_profile_flat_to_settings(dup_profiles[0]) if dup_profiles else dup_export

        dup_quality = (
            QualityDetectionSettings(**asdict(src.quality_settings))
            if src.quality_settings
            else QualityDetectionSettings()
        )
        dup_audio = copy.deepcopy(src.audio_playlist) if src.audio_playlist else None
        project = Project(
            id=project_id,
            name=name,
            created=now,
            updated=now,
            workspace_path=src.workspace_path,
            folders=dup_folders,
            selection_mode=src.selection_mode,
            filters=dup_filters,
            photo_ids=dup_photo_ids,
            manual_additions=dup_manual_add,
            manual_exclusions=dup_manual_exc,
            export_settings=dup_export,
            export_profiles=dup_profiles,
            active_export_profile_id=dup_active,
            quality_settings=dup_quality,
            exports=[],
            stats={},
            audio_playlist=dup_audio,
        )
        sync_export_settings_from_profiles(project)
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
