"""
Image Processing Module
========================

Standalone module for non-destructive image editing.
Supports: Histogram, Exposure, Contrast, Highlights, Shadows, etc.

Features:
- GPU-accelerated rendering (optional)
- RAW file support
- Non-destructive edits stored as metadata
- Export with applied edits

NO dependencies on existing photo_tool modules!
"""

from .histogram import calculate_histogram, calculate_rgb_histogram
from .adjustments import (
    apply_exposure,
    apply_contrast,
    apply_highlights,
    apply_shadows,
    apply_all_edits
)

__version__ = "1.0.0"
__all__ = [
    'calculate_histogram',
    'calculate_rgb_histogram',
    'apply_exposure',
    'apply_contrast',
    'apply_highlights',
    'apply_shadows',
    'apply_all_edits'
]
