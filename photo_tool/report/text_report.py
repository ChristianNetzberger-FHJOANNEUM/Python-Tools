"""
Text-based reports
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..analysis.clustering import PhotoCluster
from ..util.logging import get_logger


logger = get_logger("report")


def generate_text_report(
    clusters: List[PhotoCluster],
    output_path: Optional[Path] = None,
    include_blur_scores: bool = True
) -> str:
    """
    Generate text report of photo clusters
    
    Args:
        clusters: Photo clusters to report on
        output_path: Optional file to write report to
        include_blur_scores: Include blur/sharpness scores
        
    Returns:
        Report text
    """
    lines = []
    lines.append("=" * 80)
    lines.append("PHOTO TOOL - CLUSTER REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total clusters: {len(clusters)}")
    lines.append(f"Total photos: {sum(c.count for c in clusters)}")
    lines.append("")
    
    # Sort by cluster size
    sorted_clusters = sorted(clusters, key=lambda c: c.count, reverse=True)
    
    for i, cluster in enumerate(sorted_clusters, 1):
        lines.append("-" * 80)
        lines.append(f"CLUSTER #{i} - {cluster.count} photos")
        lines.append("-" * 80)
        
        # Best photo
        best_idx = cluster.best_photo_idx
        lines.append(f"Best photo (sharpest): {cluster.photos[best_idx].name}")
        
        if include_blur_scores and cluster.blur_scores:
            best_score = cluster.blur_scores[best_idx]
            if best_score is not None:
                lines.append(f"  Blur score: {best_score:.2f}")
        
        lines.append("")
        lines.append("Photos in cluster:")
        
        for j, (photo, hash_val) in enumerate(zip(cluster.photos, cluster.hashes)):
            marker = "★" if j == best_idx else " "
            line = f"  {marker} {photo.name}"
            
            if include_blur_scores and cluster.blur_scores:
                score = cluster.blur_scores[j]
                if score is not None:
                    line += f" (blur: {score:.2f})"
            
            lines.append(line)
        
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    
    # Write to file if requested
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logger.info(f"Report written to {output_path}")
    
    return report_text


def generate_summary(clusters: List[PhotoCluster]) -> str:
    """
    Generate short summary of clusters
    
    Returns:
        Summary text
    """
    total_photos = sum(c.count for c in clusters)
    
    lines = [
        f"Found {len(clusters)} clusters containing {total_photos} photos",
        "",
        "Cluster size distribution:"
    ]
    
    # Size distribution
    size_counts = {}
    for cluster in clusters:
        size = cluster.count
        size_counts[size] = size_counts.get(size, 0) + 1
    
    for size in sorted(size_counts.keys(), reverse=True):
        count = size_counts[size]
        lines.append(f"  {count} clusters with {size} photos")
    
    return "\n".join(lines)
