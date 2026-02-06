"""
Project-Specific Sidecar Manager
Handles project-local metadata overrides (rating, color, keywords)
Falls back to global sidecar if no project override exists
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..util.logging import get_logger

logger = get_logger("project_sidecar")


class ProjectSidecarManager:
    """Manages project-specific metadata sidecars"""
    
    def __init__(self, project_dir: Path):
        """
        Initialize project sidecar manager
        
        Args:
            project_dir: Path to the project directory (e.g., workspace/projects/fotobuch)
        """
        self.project_dir = project_dir
        self.sidecar_dir = project_dir / ".sidecars"
        self.sidecar_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_sidecar_path(self, photo_path: Path) -> Path:
        """Get project sidecar path for a photo"""
        # Use photo filename as sidecar name
        return self.sidecar_dir / f"{photo_path.name}.json"
    
    def has_override(self, photo_path: Path) -> bool:
        """Check if photo has project-specific overrides"""
        sidecar_path = self._get_sidecar_path(photo_path)
        return sidecar_path.exists()
    
    def get_project_metadata(self, photo_path: Path) -> Optional[Dict[str, Any]]:
        """Load project-specific metadata if exists"""
        sidecar_path = self._get_sidecar_path(photo_path)
        
        if not sidecar_path.exists():
            return None
        
        try:
            with open(sidecar_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load project sidecar {sidecar_path}: {e}")
            return None
    
    def merge_metadata(self, global_meta: Dict[str, Any], photo_path: Path) -> Dict[str, Any]:
        """
        Merge global and project-specific metadata
        Project metadata takes precedence, but keywords are merged
        
        Args:
            global_meta: Metadata from global sidecar
            photo_path: Path to the photo
        
        Returns:
            Merged metadata dict
        """
        result = global_meta.copy()
        project_meta = self.get_project_metadata(photo_path)
        
        if not project_meta:
            # No project override - return global metadata
            result['_has_project_override'] = False
            return result
        
        # Apply project overrides
        result['_has_project_override'] = True
        
        # Rating override
        if 'rating' in project_meta:
            result['rating'] = project_meta['rating']
            result['_rating_source'] = 'project'
        else:
            result['_rating_source'] = 'global'
        
        # Color override
        if 'color' in project_meta:
            result['color'] = project_meta['color']
            result['_color_source'] = 'project'
        else:
            result['_color_source'] = 'global'
        
        # Keywords merge (combine global + project)
        global_keywords = set(global_meta.get('keywords', []))
        project_keywords = set(project_meta.get('keywords', []))
        result['keywords'] = sorted(list(global_keywords | project_keywords))
        result['_project_keywords'] = sorted(list(project_keywords))
        
        # Store project metadata timestamp
        result['_project_updated'] = project_meta.get('updated')
        
        return result
    
    def set_rating(self, photo_path: Path, rating: int):
        """Set project-specific rating"""
        self._set_field(photo_path, 'rating', rating)
    
    def set_color(self, photo_path: Path, color: Optional[str]):
        """Set project-specific color"""
        self._set_field(photo_path, 'color', color)
    
    def add_keyword(self, photo_path: Path, keyword: str):
        """Add project-specific keyword"""
        project_meta = self.get_project_metadata(photo_path) or {}
        keywords = set(project_meta.get('keywords', []))
        keywords.add(keyword)
        self._set_field(photo_path, 'keywords', sorted(list(keywords)))
    
    def remove_keyword(self, photo_path: Path, keyword: str):
        """Remove project-specific keyword"""
        project_meta = self.get_project_metadata(photo_path) or {}
        keywords = set(project_meta.get('keywords', []))
        keywords.discard(keyword)
        self._set_field(photo_path, 'keywords', sorted(list(keywords)))
    
    def _set_field(self, photo_path: Path, field: str, value: Any):
        """Set a field in project sidecar"""
        sidecar_path = self._get_sidecar_path(photo_path)
        
        # Load existing or create new
        data = {}
        if sidecar_path.exists():
            try:
                with open(sidecar_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                data = {}
        
        # Update field
        data[field] = value
        data['updated'] = datetime.now().isoformat()
        
        # Save
        try:
            with open(sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Updated project sidecar: {photo_path.name} -> {field}={value}")
        except Exception as e:
            logger.error(f"Failed to save project sidecar: {e}")
            raise
    
    def reset_to_global(self, photo_path: Path):
        """Remove all project overrides (reset to global)"""
        sidecar_path = self._get_sidecar_path(photo_path)
        if sidecar_path.exists():
            sidecar_path.unlink()
            logger.info(f"Removed project override for {photo_path.name}")
    
    def apply_to_global(self, photo_path: Path, global_sidecar_manager):
        """
        Apply project metadata to global sidecar
        (Copy project rating/color to global)
        """
        project_meta = self.get_project_metadata(photo_path)
        if not project_meta:
            return
        
        # Apply rating if exists
        if 'rating' in project_meta:
            from photo_tool.actions.rating import set_rating
            set_rating(photo_path, project_meta['rating'])
        
        # Apply color if exists
        if 'color' in project_meta:
            from photo_tool.actions.metadata import set_color_label
            set_color_label(photo_path, project_meta['color'])
        
        # Apply keywords (merge)
        if 'keywords' in project_meta:
            from photo_tool.actions.metadata import set_keywords, get_metadata
            global_meta = get_metadata(photo_path)
            global_keywords = set(global_meta.get('keywords', []))
            project_keywords = set(project_meta['keywords'])
            merged = sorted(list(global_keywords | project_keywords))
            set_keywords(photo_path, merged)
        
        logger.info(f"Applied project metadata to global for {photo_path.name}")
    
    def list_overrides(self) -> List[str]:
        """List all photos with project overrides"""
        if not self.sidecar_dir.exists():
            return []
        
        overrides = []
        for sidecar_file in self.sidecar_dir.glob("*.json"):
            overrides.append(sidecar_file.stem)  # Photo filename without .json
        
        return overrides
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about project overrides"""
        overrides = self.list_overrides()
        
        rating_overrides = 0
        color_overrides = 0
        keyword_overrides = 0
        
        for photo_name in overrides:
            sidecar_path = self.sidecar_dir / f"{photo_name}.json"
            try:
                with open(sidecar_path, 'r') as f:
                    data = json.load(f)
                    if 'rating' in data:
                        rating_overrides += 1
                    if 'color' in data:
                        color_overrides += 1
                    if 'keywords' in data:
                        keyword_overrides += 1
            except:
                pass
        
        return {
            'total_overrides': len(overrides),
            'rating_overrides': rating_overrides,
            'color_overrides': color_overrides,
            'keyword_overrides': keyword_overrides
        }
