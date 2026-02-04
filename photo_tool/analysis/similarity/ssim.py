"""
Structural Similarity (SSIM) for refined comparison
"""

from pathlib import Path

import cv2
from skimage.metrics import structural_similarity as ssim

from ...util.logging import get_logger


logger = get_logger("ssim")


def compute_ssim(image1_path: Path, image2_path: Path) -> float:
    """
    Compute SSIM between two images
    
    SSIM ranges from -1 to 1, where 1 means identical
    
    Args:
        image1_path: First image
        image2_path: Second image
        
    Returns:
        SSIM score (0-1, higher = more similar)
    """
    try:
        # Read images
        img1 = cv2.imread(str(image1_path), cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(str(image2_path), cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            raise ValueError("Could not read one or both images")
        
        # Resize to same dimensions if needed
        if img1.shape != img2.shape:
            # Resize to smaller dimensions
            h = min(img1.shape[0], img2.shape[0])
            w = min(img1.shape[1], img2.shape[1])
            img1 = cv2.resize(img1, (w, h))
            img2 = cv2.resize(img2, (w, h))
        
        # Compute SSIM
        score = ssim(img1, img2)
        
        return float(score)
    
    except Exception as e:
        logger.error(f"Error computing SSIM: {e}")
        raise


def are_similar_ssim(
    image1_path: Path,
    image2_path: Path,
    threshold: float = 0.92
) -> tuple[bool, float]:
    """
    Check if two images are similar using SSIM
    
    Args:
        image1_path: First image
        image2_path: Second image
        threshold: Similarity threshold
        
    Returns:
        (is_similar, score) tuple
    """
    score = compute_ssim(image1_path, image2_path)
    return (score >= threshold, score)
