"""
Deduplication: find and handle duplicate photos
"""

from pathlib import Path
from typing import List, Literal

from ..analysis.clustering import PhotoCluster
from ..util.logging import get_logger


logger = get_logger("dedupe")


def deduplicate_photos(
    clusters: List[PhotoCluster],
    strategy: Literal["keep_best", "keep_first", "keep_all"] = "keep_best",
    action: Literal["delete", "move", "list"] = "list",
    move_to: Path = None,
    dry_run: bool = True
) -> List[Path]:
    """
    Handle duplicate photos in clusters
    
    Args:
        clusters: Photo clusters
        strategy: Which photo to keep
        action: What to do with duplicates
        move_to: Where to move duplicates (if action="move")
        dry_run: Preview only
        
    Returns:
        List of photos that would be/were acted upon
    """
    affected_photos = []
    
    for cluster in clusters:
        # Determine which photo to keep
        if strategy == "keep_best":
            keep_idx = cluster.best_photo_idx
        elif strategy == "keep_first":
            keep_idx = 0
        elif strategy == "keep_all":
            continue  # Don't remove anything
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Get duplicates (all except the one we keep)
        duplicates = [p for i, p in enumerate(cluster.photos) if i != keep_idx]
        
        for duplicate in duplicates:
            affected_photos.append(duplicate)
            
            if action == "delete":
                if not dry_run:
                    try:
                        duplicate.unlink()
                        logger.info(f"Deleted: {duplicate}")
                    except Exception as e:
                        logger.error(f"Error deleting {duplicate}: {e}")
                else:
                    logger.info(f"Would delete: {duplicate}")
            
            elif action == "move":
                if not move_to:
                    raise ValueError("move_to must be specified for action='move'")
                
                target_path = move_to / duplicate.name
                
                if not dry_run:
                    try:
                        move_to.mkdir(parents=True, exist_ok=True)
                        duplicate.rename(target_path)
                        logger.info(f"Moved: {duplicate} -> {target_path}")
                    except Exception as e:
                        logger.error(f"Error moving {duplicate}: {e}")
                else:
                    logger.info(f"Would move: {duplicate} -> {target_path}")
            
            elif action == "list":
                logger.info(f"Duplicate: {duplicate} (keeping {cluster.photos[keep_idx]})")
    
    logger.info(f"Found {len(affected_photos)} duplicate photos")
    
    return affected_photos
