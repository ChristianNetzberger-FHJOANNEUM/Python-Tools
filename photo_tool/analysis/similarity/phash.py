"""
Perceptual hashing for fast similarity detection
"""

from enum import Enum
from pathlib import Path
from typing import Tuple

import imagehash
from PIL import Image

from ...util.logging import get_logger


logger = get_logger("phash")


class HashMethod(Enum):
    """Perceptual hash methods"""
    PHASH = "phash"  # Most robust
    DHASH = "dhash"  # Faster, good for similar images
    AHASH = "ahash"  # Simplest, less accurate


def compute_phash(
    image_path: Path,
    method: HashMethod = HashMethod.PHASH,
    hash_size: int = 8
) -> str:
    """
    Compute perceptual hash of image
    
    Args:
        image_path: Path to image
        method: Hashing method
        hash_size: Hash size (default 8 = 64-bit hash)
        
    Returns:
        Hex string of hash
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Compute hash based on method
            if method == HashMethod.PHASH:
                hash_obj = imagehash.phash(img, hash_size=hash_size)
            elif method == HashMethod.DHASH:
                hash_obj = imagehash.dhash(img, hash_size=hash_size)
            elif method == HashMethod.AHASH:
                hash_obj = imagehash.average_hash(img, hash_size=hash_size)
            else:
                raise ValueError(f"Unknown hash method: {method}")
            
            return str(hash_obj)
    
    except Exception as e:
        logger.error(f"Error computing hash for {image_path}: {e}")
        raise


def compare_hashes(hash1: str, hash2: str) -> int:
    """
    Compare two perceptual hashes
    
    Args:
        hash1: First hash (hex string)
        hash2: Second hash (hex string)
        
    Returns:
        Hamming distance (0 = identical, larger = more different)
    """
    # Convert hex strings to imagehash objects
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    
    # Compute Hamming distance
    return h1 - h2


def are_similar(
    hash1: str,
    hash2: str,
    threshold: int = 6
) -> Tuple[bool, int]:
    """
    Check if two images are similar based on hash distance
    
    Args:
        hash1: First hash
        hash2: Second hash
        threshold: Maximum distance to consider similar
        
    Returns:
        (is_similar, distance) tuple
    """
    distance = compare_hashes(hash1, hash2)
    return (distance <= threshold, distance)
