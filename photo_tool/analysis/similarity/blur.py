"""
Blur/sharpness detection
"""

from enum import Enum
from pathlib import Path

import cv2
import numpy as np

from ...util.logging import get_logger


logger = get_logger("blur")


class BlurMethod(Enum):
    """Blur detection methods"""
    LAPLACIAN = "laplacian"  # Variance of Laplacian (recommended)
    VARIANCE = "variance"    # Simple variance


def detect_blur(
    image_path: Path,
    method: BlurMethod = BlurMethod.LAPLACIAN
) -> float:
    """
    Detect blur/sharpness of image
    
    Higher score = sharper image
    
    Args:
        image_path: Path to image
        method: Detection method
        
    Returns:
        Blur score (higher = sharper)
    """
    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        if method == BlurMethod.LAPLACIAN:
            # Compute variance of Laplacian
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            score = laplacian.var()
        
        elif method == BlurMethod.VARIANCE:
            # Simple variance method
            score = gray.var()
        
        else:
            raise ValueError(f"Unknown blur method: {method}")
        
        return float(score)
    
    except Exception as e:
        logger.error(f"Error detecting blur for {image_path}: {e}")
        raise


def is_blurry(
    image_path: Path,
    threshold: float = 120.0,
    method: BlurMethod = BlurMethod.LAPLACIAN
) -> tuple[bool, float]:
    """
    Check if image is blurry
    
    Args:
        image_path: Path to image
        threshold: Blur threshold (adjust based on your images)
        method: Detection method
        
    Returns:
        (is_blurry, score) tuple
    """
    score = detect_blur(image_path, method)
    return (score < threshold, score)
