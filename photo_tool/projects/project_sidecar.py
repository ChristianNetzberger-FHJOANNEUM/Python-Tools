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
from ..actions.rating import get_rating
from .rating_layers import (
    normalize_rating_layer,
    RATING_LAYER_GLOBAL,
    RATING_LAYER_PROJECT,
    RATING_LAYER_COUCH,
    DEFAULT_RATING_LAYER,
)

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
    
    def merge_metadata(
        self,
        global_meta: Dict[str, Any],
        photo_path: Path,
        *,
        active_rating_layer: str = DEFAULT_RATING_LAYER,
    ) -> Dict[str, Any]:
        """
        Merge global and project-specific metadata (color/keywords unchanged).
        ``rating`` follows ``active_rating_layer``: global | project | couch.

        Couch ratings live in the project sidecar as ``couch_rating`` (0–5).
        Fallback chain for couch layer: couch → project → global archive rating.
        """
        layer = normalize_rating_layer(active_rating_layer)
        result = global_meta.copy()
        gr_file = get_rating(photo_path)
        base_global = int(gr_file) if gr_file is not None else int(global_meta.get('rating') or 0)

        project_meta = self.get_project_metadata(photo_path)
        has_pm = bool(project_meta)

        proj_set = has_pm and 'rating' in project_meta
        proj_r = int(project_meta['rating']) if proj_set else None

        couch_set = (
            has_pm
            and 'couch_rating' in project_meta
            and project_meta['couch_rating'] is not None
        )
        couch_r = int(project_meta['couch_rating']) if couch_set else None

        result['_rating_global'] = base_global
        result['_rating_project'] = proj_r
        result['_rating_couch'] = couch_r
        result['_active_rating_layer'] = layer

        if layer == RATING_LAYER_GLOBAL:
            result['rating'] = base_global
            result['_rating_source'] = 'global'
        elif layer == RATING_LAYER_PROJECT:
            if proj_set:
                result['rating'] = proj_r
                result['_rating_source'] = 'project'
            else:
                result['rating'] = base_global
                result['_rating_source'] = 'global'
        else:  # couch
            if couch_set:
                result['rating'] = couch_r
                result['_rating_source'] = 'couch'
            elif proj_set:
                result['rating'] = proj_r
                result['_rating_source'] = 'project'
            else:
                result['rating'] = base_global
                result['_rating_source'] = 'global'

        base_g_color = global_meta.get('color')

        if not has_pm:
            result['_has_project_override'] = False
            result['color'] = base_g_color
            result['_color_source'] = 'global'
            result['_color_global'] = base_g_color
            result['_color_project'] = None
            result['_color_couch'] = None
            return result

        result['_has_project_override'] = True

        proj_color_set = 'color' in project_meta and project_meta.get('color') not in (None, '')
        couch_color_val = project_meta.get('couch_color')
        couch_color_set = (
            'couch_color' in project_meta
            and couch_color_val not in (None, '')
        )

        result['_color_global'] = base_g_color
        result['_color_project'] = project_meta.get('color') if proj_color_set else None
        result['_color_couch'] = couch_color_val if couch_color_set else None

        if layer == RATING_LAYER_GLOBAL:
            result['color'] = base_g_color
            result['_color_source'] = 'global'
        elif layer == RATING_LAYER_PROJECT:
            if proj_color_set:
                result['color'] = project_meta['color']
                result['_color_source'] = 'project'
            else:
                result['color'] = base_g_color
                result['_color_source'] = 'global'
        else:  # couch
            if couch_color_set:
                result['color'] = couch_color_val
                result['_color_source'] = 'couch'
            elif proj_color_set:
                result['color'] = project_meta['color']
                result['_color_source'] = 'project'
            else:
                result['color'] = base_g_color
                result['_color_source'] = 'global'

        # Keywords merge (combine global + project)
        global_keywords = set(global_meta.get('keywords', []))
        project_keywords = set(project_meta.get('keywords', []))
        result['keywords'] = sorted(list(global_keywords | project_keywords))
        result['_project_keywords'] = sorted(list(project_keywords))

        result['_project_updated'] = project_meta.get('updated')

        return result
    
    def set_rating(self, photo_path: Path, rating: int):
        """Set project-specific rating"""
        self._set_field(photo_path, 'rating', rating)

    def set_couch_rating(self, photo_path: Path, rating: int):
        """Set couch/TV review rating (project sidecar only, 0–5)."""
        if not 0 <= rating <= 5:
            raise ValueError('Couch rating must be between 0 and 5')
        self._set_field(photo_path, 'couch_rating', rating)
    
    def set_color(self, photo_path: Path, color: Optional[str]):
        """Set project-specific color"""
        self._set_field(photo_path, 'color', color)

    def set_couch_color(self, photo_path: Path, color: Optional[str]):
        """Couch / TV color label (project sidecar only). None clears the field."""
        valid = {'red', 'yellow', 'green', 'blue', 'purple', None}
        if color not in valid:
            raise ValueError(f"Couch color must be one of {sorted(x for x in valid if x)} or null")
        if color is None:
            sidecar_path = self._get_sidecar_path(photo_path)
            if not sidecar_path.exists():
                return
            try:
                with open(sidecar_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                return
            data.pop('couch_color', None)
            data['updated'] = datetime.now().isoformat()
            with open(sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return
        self._set_field(photo_path, 'couch_color', color)
    
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

    def promote_couch_to_project(
        self,
        *,
        promote_ratings: bool = True,
        promote_colors: bool = False,
        clear_couch_ratings: bool = False,
        clear_couch_colors: bool = False,
    ) -> Dict[str, Any]:
        """
        Copy couch_rating → rating and/or couch_color → color in each project sidecar.
        """
        promoted_ratings = 0
        promoted_colors = 0
        if not self.sidecar_dir.is_dir():
            return {'promoted_ratings': 0, 'promoted_colors': 0}
        for sidecar_path in sorted(self.sidecar_dir.glob("*.json")):
            try:
                with open(sidecar_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                continue
            changed = False
            if promote_ratings:
                cr = data.get('couch_rating')
                if cr is not None and isinstance(cr, (int, float)) and 0 <= int(cr) <= 5:
                    data['rating'] = int(cr)
                    promoted_ratings += 1
                    changed = True
                    if clear_couch_ratings:
                        data.pop('couch_rating', None)
            if promote_colors:
                cc = data.get('couch_color')
                if cc not in (None, ''):
                    data['color'] = cc
                    promoted_colors += 1
                    changed = True
                    if clear_couch_colors:
                        data.pop('couch_color', None)
            if changed:
                data['updated'] = datetime.now().isoformat()
                with open(sidecar_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        return {
            'promoted_ratings': promoted_ratings,
            'promoted_colors': promoted_colors,
        }
    
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
        couch_rating_overrides = 0
        couch_color_overrides = 0
        color_overrides = 0
        keyword_overrides = 0
        
        for photo_name in overrides:
            sidecar_path = self.sidecar_dir / f"{photo_name}.json"
            try:
                with open(sidecar_path, 'r') as f:
                    data = json.load(f)
                    if 'rating' in data:
                        rating_overrides += 1
                    if 'couch_rating' in data and data.get('couch_rating') is not None:
                        couch_rating_overrides += 1
                    if 'couch_color' in data and data.get('couch_color') not in (None, ''):
                        couch_color_overrides += 1
                    if 'color' in data:
                        color_overrides += 1
                    if 'keywords' in data:
                        keyword_overrides += 1
            except:
                pass
        
        return {
            'total_overrides': len(overrides),
            'rating_overrides': rating_overrides,
            'couch_rating_overrides': couch_rating_overrides,
            'couch_color_overrides': couch_color_overrides,
            'color_overrides': color_overrides,
            'keyword_overrides': keyword_overrides
        }
