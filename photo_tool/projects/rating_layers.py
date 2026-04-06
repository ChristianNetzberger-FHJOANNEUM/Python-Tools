"""
Rating layers: archive (global) vs project curation vs couch/TV review.

UI/API choose an active layer; ProjectSidecarManager merges sidecars accordingly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

RATING_LAYER_GLOBAL = "global"
RATING_LAYER_PROJECT = "project"
RATING_LAYER_COUCH = "couch"

ALL_RATING_LAYERS = (RATING_LAYER_GLOBAL, RATING_LAYER_PROJECT, RATING_LAYER_COUCH)
DEFAULT_RATING_LAYER = RATING_LAYER_PROJECT


def normalize_rating_layer(value: Optional[str]) -> str:
    if not value:
        return DEFAULT_RATING_LAYER
    v = str(value).strip().lower()
    if v in ALL_RATING_LAYERS:
        return v
    return DEFAULT_RATING_LAYER


class RatingLayerManager:
    """
    Coordinates active rating layer for one project directory.
    Merge logic lives in ProjectSidecarManager.merge_metadata; this is a small facade.
    """

    def __init__(self, project_dir: Path):
        from .project_sidecar import ProjectSidecarManager

        self.psm = ProjectSidecarManager(project_dir)

    def merge_metadata(
        self,
        global_meta: Dict[str, Any],
        photo_path: Path,
        *,
        active_rating_layer: str,
    ) -> Dict[str, Any]:
        layer = normalize_rating_layer(active_rating_layer)
        return self.psm.merge_metadata(global_meta, photo_path, active_rating_layer=layer)
