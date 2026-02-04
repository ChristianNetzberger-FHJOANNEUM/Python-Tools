"""
Exposure and histogram analysis
"""

from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

from ...util.logging import get_logger


logger = get_logger("exposure")


def compute_histogram(image_path: Path) -> Dict[str, np.ndarray]:
    """
    Compute luminance histogram
    
    Args:
        image_path: Path to image
        
    Returns:
        Dict with 'histogram' (256 bins) and 'channels' (RGB histograms)
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale for luminance
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Compute histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Also get per-channel histograms
        b_hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        g_hist = cv2.calcHist([img], [1], None, [256], [0, 256])
        r_hist = cv2.calcHist([img], [2], None, [256], [0, 256])
        
        return {
            'luminance': hist.flatten(),
            'blue': b_hist.flatten(),
            'green': g_hist.flatten(),
            'red': r_hist.flatten()
        }
    
    except Exception as e:
        logger.error(f"Error computing histogram for {image_path}: {e}")
        raise


def detect_clipping(histogram: np.ndarray, threshold: float = 0.01) -> Dict[str, float]:
    """
    Detect clipped highlights and shadows
    
    Args:
        histogram: Luminance histogram (256 bins)
        threshold: Percentage threshold for clipping detection
        
    Returns:
        Dict with 'shadow_clipping' and 'highlight_clipping' percentages
    """
    total_pixels = histogram.sum()
    
    # Check first few bins (shadows)
    shadow_pixels = histogram[:5].sum()
    shadow_clipping = shadow_pixels / total_pixels
    
    # Check last few bins (highlights)
    highlight_pixels = histogram[-5:].sum()
    highlight_clipping = highlight_pixels / total_pixels
    
    return {
        'shadow_clipping': float(shadow_clipping),
        'highlight_clipping': float(highlight_clipping),
        'is_shadow_clipped': shadow_clipping > threshold,
        'is_highlight_clipped': highlight_clipping > threshold
    }


def compute_exposure_score(image_path: Path) -> Dict[str, float]:
    """
    Compute overall exposure metrics
    
    Returns:
        Dict with mean brightness, contrast, and clipping info
    """
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Basic stats
        mean_brightness = float(img.mean())
        std_dev = float(img.std())
        
        # Histogram analysis
        hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
        clipping = detect_clipping(hist)
        
        return {
            'mean_brightness': mean_brightness,
            'std_dev': std_dev,
            'contrast': std_dev / mean_brightness if mean_brightness > 0 else 0,
            **clipping
        }
    
    except Exception as e:
        logger.error(f"Error computing exposure for {image_path}: {e}")
        raise
