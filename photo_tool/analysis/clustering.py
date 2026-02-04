"""
Stage 3: Clustering similar photos within time groups
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

from tqdm import tqdm

from .time_grouping import TimeGroup
from .similarity import compute_phash, compare_hashes, HashMethod
from ..util.logging import get_logger


logger = get_logger("clustering")


@dataclass
class PhotoCluster:
    """Cluster of similar photos"""
    photos: List[Path] = field(default_factory=list)
    hashes: List[str] = field(default_factory=list)
    blur_scores: List[Optional[float]] = field(default_factory=list)
    
    @property
    def count(self) -> int:
        """Number of photos in cluster"""
        return len(self.photos)
    
    @property
    def best_photo_idx(self) -> int:
        """Index of best photo (sharpest)"""
        if not self.blur_scores or all(s is None for s in self.blur_scores):
            return 0  # Default to first
        
        # Return index with highest blur score (sharpest)
        valid_scores = [(i, s) for i, s in enumerate(self.blur_scores) if s is not None]
        if not valid_scores:
            return 0
        
        return max(valid_scores, key=lambda x: x[1])[0]
    
    @property
    def best_photo(self) -> Path:
        """Path to best photo"""
        return self.photos[self.best_photo_idx]
    
    def __repr__(self) -> str:
        return f"PhotoCluster({self.count} photos)"


def cluster_similar_photos(
    time_groups: List[TimeGroup],
    hash_method: HashMethod = HashMethod.PHASH,
    similarity_threshold: int = 6,
    blur_scores: Optional[Dict[Path, float]] = None,
    show_progress: bool = True
) -> List[PhotoCluster]:
    """
    Cluster similar photos within time groups
    
    This is Stage 2+3 of the pipeline:
    - Compute perceptual hashes
    - Group similar photos together
    
    Args:
        time_groups: Time-based groups from stage 1
        hash_method: Hashing method to use
        similarity_threshold: Max hash distance for similarity
        blur_scores: Optional dict of blur scores for ranking
        show_progress: Show progress bar
        
    Returns:
        List of PhotoCluster objects
    """
    all_clusters = []
    
    iterator = tqdm(time_groups, desc="Clustering photos") if show_progress else time_groups
    
    for time_group in iterator:
        # Compute hashes for all photos in group
        photo_hashes = []
        for photo in time_group.photos:
            try:
                hash_str = compute_phash(photo, method=hash_method)
                photo_hashes.append(hash_str)
            except Exception as e:
                logger.warning(f"Could not hash {photo}: {e}")
                photo_hashes.append(None)
        
        # Build clusters using simple sequential grouping
        # (More sophisticated: use graph clustering, but this is fast and works well)
        clusters = []
        used = set()
        
        for i, (photo, hash_val) in enumerate(zip(time_group.photos, photo_hashes)):
            if i in used or hash_val is None:
                continue
            
            # Start new cluster
            cluster_photos = [photo]
            cluster_hashes = [hash_val]
            cluster_blur_scores = [blur_scores.get(photo) if blur_scores else None]
            used.add(i)
            
            # Find similar photos
            for j, (other_photo, other_hash) in enumerate(zip(time_group.photos, photo_hashes)):
                if j <= i or j in used or other_hash is None:
                    continue
                
                # Compare hashes
                distance = compare_hashes(hash_val, other_hash)
                
                if distance <= similarity_threshold:
                    cluster_photos.append(other_photo)
                    cluster_hashes.append(other_hash)
                    cluster_blur_scores.append(blur_scores.get(other_photo) if blur_scores else None)
                    used.add(j)
            
            # Only create cluster if multiple photos
            if len(cluster_photos) >= 2:
                clusters.append(PhotoCluster(
                    photos=cluster_photos,
                    hashes=cluster_hashes,
                    blur_scores=cluster_blur_scores
                ))
        
        all_clusters.extend(clusters)
    
    logger.info(f"Created {len(all_clusters)} photo clusters")
    
    return all_clusters


def cluster_single_group(
    photos: List[Path],
    hash_method: HashMethod = HashMethod.PHASH,
    similarity_threshold: int = 6,
    blur_scores: Optional[Dict[Path, float]] = None
) -> List[PhotoCluster]:
    """
    Cluster photos without time grouping (use all photos as one group)
    
    Useful for when you want to find duplicates across entire collection
    
    Args:
        photos: List of photo paths
        hash_method: Hashing method
        similarity_threshold: Max distance for similarity
        blur_scores: Optional blur scores
        
    Returns:
        List of PhotoCluster objects
    """
    if not photos:
        return []
    
    logger.info(f"Computing hashes for {len(photos)} photos")
    
    # Compute all hashes
    photo_hashes = []
    for photo in tqdm(photos, desc="Computing hashes"):
        try:
            hash_str = compute_phash(photo, method=hash_method)
            photo_hashes.append(hash_str)
        except Exception as e:
            logger.warning(f"Could not hash {photo}: {e}")
            photo_hashes.append(None)
    
    # Build similarity graph (this can be slow for large collections)
    logger.info("Building similarity clusters")
    
    clusters = []
    used = set()
    
    for i, (photo, hash_val) in enumerate(tqdm(list(zip(photos, photo_hashes)), desc="Clustering")):
        if i in used or hash_val is None:
            continue
        
        # Start new cluster
        cluster_photos = [photo]
        cluster_hashes = [hash_val]
        cluster_blur_scores = [blur_scores.get(photo) if blur_scores else None]
        used.add(i)
        
        # Find all similar photos
        for j, (other_photo, other_hash) in enumerate(zip(photos, photo_hashes)):
            if j <= i or j in used or other_hash is None:
                continue
            
            distance = compare_hashes(hash_val, other_hash)
            
            if distance <= similarity_threshold:
                cluster_photos.append(other_photo)
                cluster_hashes.append(other_hash)
                cluster_blur_scores.append(blur_scores.get(other_photo) if blur_scores else None)
                used.add(j)
        
        # Only save if multiple photos
        if len(cluster_photos) >= 2:
            clusters.append(PhotoCluster(
                photos=cluster_photos,
                hashes=cluster_hashes,
                blur_scores=cluster_blur_scores
            ))
    
    logger.info(f"Found {len(clusters)} clusters")
    
    return clusters
