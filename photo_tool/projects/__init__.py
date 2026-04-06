"""
Project management for Photo Tool
Allows saving and loading photo selections with export settings
"""

from .manager import ProjectManager, Project
from .project_sidecar import ProjectSidecarManager
from .rating_layers import (
    RatingLayerManager,
    normalize_rating_layer,
    RATING_LAYER_GLOBAL,
    RATING_LAYER_PROJECT,
    RATING_LAYER_COUCH,
    DEFAULT_RATING_LAYER,
    ALL_RATING_LAYERS,
)

__all__ = [
    'ProjectManager',
    'Project',
    'ProjectSidecarManager',
    'RatingLayerManager',
    'normalize_rating_layer',
    'RATING_LAYER_GLOBAL',
    'RATING_LAYER_PROJECT',
    'RATING_LAYER_COUCH',
    'DEFAULT_RATING_LAYER',
    'ALL_RATING_LAYERS',
]
