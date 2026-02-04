"""
Photo organization: move photos into folders by cluster
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Literal

from ..analysis.clustering import PhotoCluster
from ..util.paths import safe_filename
from ..util.logging import get_logger


logger = get_logger("organizer")


@dataclass
class OrganizeResult:
    """Result of organization operation"""
    clusters_processed: int = 0
    photos_moved: int = 0
    folders_created: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def organize_clusters(
    clusters: List[PhotoCluster],
    naming_strategy: Literal["first_filename", "timestamp", "sequential"] = "first_filename",
    min_cluster_size: int = 2,
    dry_run: bool = True,
    target_dir: Path = None
) -> OrganizeResult:
    """
    Organize photo clusters into folders
    
    For each cluster:
    - Create a folder named according to strategy
    - Move/copy photos into that folder
    
    Args:
        clusters: List of photo clusters
        naming_strategy: How to name folders
        min_cluster_size: Minimum photos in cluster to process
        dry_run: If True, only log what would be done
        target_dir: Optional target directory (default: same as source)
        
    Returns:
        OrganizeResult with statistics
    """
    result = OrganizeResult()
    
    # Filter by size
    clusters_to_process = [c for c in clusters if c.count >= min_cluster_size]
    
    logger.info(f"Processing {len(clusters_to_process)} clusters (min size: {min_cluster_size})")
    
    if dry_run:
        logger.info("DRY RUN - no files will be moved")
    
    for i, cluster in enumerate(clusters_to_process):
        try:
            # Determine folder name
            if naming_strategy == "first_filename":
                folder_name = cluster.photos[0].stem
            elif naming_strategy == "timestamp":
                # Use current timestamp
                folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")
            elif naming_strategy == "sequential":
                folder_name = f"burst_{i+1:04d}"
            else:
                raise ValueError(f"Unknown naming strategy: {naming_strategy}")
            
            folder_name = safe_filename(folder_name)
            
            # Determine folder location
            if target_dir:
                folder_path = target_dir / folder_name
            else:
                # Same directory as first photo
                folder_path = cluster.photos[0].parent / folder_name
            
            # Create folder
            if not dry_run:
                folder_path.mkdir(parents=True, exist_ok=True)
                result.folders_created += 1
            else:
                logger.info(f"Would create folder: {folder_path}")
            
            # Move photos
            for photo in cluster.photos:
                target_path = folder_path / photo.name
                
                if not dry_run:
                    try:
                        # Move file
                        shutil.move(str(photo), str(target_path))
                        result.photos_moved += 1
                        logger.debug(f"Moved: {photo} -> {target_path}")
                    except Exception as e:
                        error_msg = f"Error moving {photo}: {e}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                else:
                    logger.info(f"Would move: {photo} -> {target_path}")
                    result.photos_moved += 1
            
            result.clusters_processed += 1
        
        except Exception as e:
            error_msg = f"Error processing cluster {i}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
    
    # Summary
    logger.info("=" * 60)
    logger.info("Organization Summary:")
    logger.info(f"  Clusters processed: {result.clusters_processed}")
    logger.info(f"  Folders created: {result.folders_created}")
    logger.info(f"  Photos moved: {result.photos_moved}")
    if result.errors:
        logger.warning(f"  Errors: {len(result.errors)}")
    logger.info("=" * 60)
    
    return result


def copy_best_photos(
    clusters: List[PhotoCluster],
    output_dir: Path,
    dry_run: bool = True
) -> int:
    """
    Copy only the best photo from each cluster to output directory
    
    Useful for quickly curating a collection
    
    Args:
        clusters: Photo clusters
        output_dir: Output directory for best photos
        dry_run: Preview only
        
    Returns:
        Number of photos copied
    """
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    
    for cluster in clusters:
        best_photo = cluster.best_photo
        target_path = output_dir / best_photo.name
        
        if not dry_run:
            try:
                shutil.copy2(str(best_photo), str(target_path))
                count += 1
                logger.debug(f"Copied best: {best_photo} -> {target_path}")
            except Exception as e:
                logger.error(f"Error copying {best_photo}: {e}")
        else:
            logger.info(f"Would copy best: {best_photo} -> {target_path}")
            count += 1
    
    logger.info(f"{'Would copy' if dry_run else 'Copied'} {count} best photos to {output_dir}")
    
    return count
