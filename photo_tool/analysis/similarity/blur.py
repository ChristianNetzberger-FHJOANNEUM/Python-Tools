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
    LAPLACIAN = "laplacian"  # Variance of Laplacian (fast, general purpose)
    TENENGRAD = "tenengrad"  # Sobel gradient (better for sky/homogeneous areas)
    ROI = "roi"              # Region of Interest (adaptive, best for mixed scenes)
    VARIANCE = "variance"    # Simple variance (fast, basic)


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
        
        elif method == BlurMethod.TENENGRAD:
            # Tenengrad gradient method - better for images with sky/homogeneous areas
            gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            fm = np.sqrt(gx**2 + gy**2)
            score = fm.mean()
        
        elif method == BlurMethod.ROI:
            # ROI-based method - focuses on interesting areas (edges, objects)
            # Ignores homogeneous areas like sky
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                # Fallback to Laplacian if no edges found
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                score = laplacian.var()
            else:
                # Calculate blur only on regions of interest
                roi_scores = []
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    if w * h > 100:  # Ignore very small regions
                        roi = gray[y:y+h, x:x+w]
                        if roi.size > 0:
                            laplacian = cv2.Laplacian(roi, cv2.CV_64F)
                            roi_scores.append(laplacian.var())
                
                if roi_scores:
                    # Take mean of top 50% scores (ignore worst regions)
                    sorted_scores = sorted(roi_scores, reverse=True)
                    top_half = sorted_scores[:max(1, len(sorted_scores)//2)]
                    score = np.mean(top_half)
                else:
                    # Fallback
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
