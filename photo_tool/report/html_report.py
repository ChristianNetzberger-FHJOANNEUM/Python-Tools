"""
HTML report generation with thumbnails
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..analysis.clustering import PhotoCluster
from ..io.thumbnails import generate_thumbnail
from ..util.logging import get_logger


logger = get_logger("html_report")


def generate_html_report(
    clusters: List[PhotoCluster],
    output_path: Path,
    thumbnails_dir: Path,
    include_thumbnails: bool = True
) -> None:
    """
    Generate HTML report with thumbnails
    
    Args:
        clusters: Photo clusters
        output_path: Output HTML file
        thumbnails_dir: Directory for thumbnail cache
        include_thumbnails: Generate and include thumbnails
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    html_parts = []
    html_parts.append(_get_html_header())
    
    html_parts.append("<body>")
    html_parts.append("<div class='container'>")
    html_parts.append("<h1>Photo Tool - Cluster Report</h1>")
    html_parts.append(f"<p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
    html_parts.append(f"<p class='meta'>Total clusters: {len(clusters)} | Total photos: {sum(c.count for c in clusters)}</p>")
    
    # Sort by size
    sorted_clusters = sorted(clusters, key=lambda c: c.count, reverse=True)
    
    for i, cluster in enumerate(sorted_clusters, 1):
        html_parts.append("<div class='cluster'>")
        html_parts.append(f"<h2>Cluster #{i} - {cluster.count} photos</h2>")
        
        best_idx = cluster.best_photo_idx
        html_parts.append(f"<p class='best'>Best photo: {cluster.photos[best_idx].name}</p>")
        
        if include_thumbnails:
            html_parts.append("<div class='filmstrip'>")
            
            for j, photo in enumerate(cluster.photos):
                is_best = j == best_idx
                
                try:
                    # Generate thumbnail
                    thumb_path = generate_thumbnail(photo, thumbnails_dir)
                    rel_thumb_path = Path(thumb_path).relative_to(output_path.parent)
                    
                    css_class = "photo best" if is_best else "photo"
                    html_parts.append(f"<div class='{css_class}'>")
                    html_parts.append(f"<img src='{rel_thumb_path}' alt='{photo.name}'>")
                    html_parts.append(f"<p class='filename'>{photo.name}</p>")
                    
                    if cluster.blur_scores and cluster.blur_scores[j] is not None:
                        score = cluster.blur_scores[j]
                        html_parts.append(f"<p class='score'>Sharpness: {score:.1f}</p>")
                    
                    html_parts.append("</div>")
                
                except Exception as e:
                    logger.warning(f"Could not generate thumbnail for {photo}: {e}")
            
            html_parts.append("</div>")  # filmstrip
        else:
            html_parts.append("<ul>")
            for j, photo in enumerate(cluster.photos):
                marker = "★" if j == best_idx else ""
                html_parts.append(f"<li>{marker} {photo.name}</li>")
            html_parts.append("</ul>")
        
        html_parts.append("</div>")  # cluster
    
    html_parts.append("</div>")  # container
    html_parts.append("</body></html>")
    
    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_parts))
    
    logger.info(f"HTML report written to {output_path}")


def _get_html_header() -> str:
    """Get HTML header with CSS"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photo Tool Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        h2 {
            color: #555;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
        }
        .meta {
            color: #777;
            font-size: 14px;
        }
        .cluster {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            background: #fafafa;
        }
        .best {
            color: #2196F3;
            font-weight: 600;
        }
        .filmstrip {
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding: 10px 0;
        }
        .photo {
            flex-shrink: 0;
            text-align: center;
            width: 200px;
        }
        .photo.best {
            border: 3px solid #2196F3;
            border-radius: 8px;
            padding: 5px;
            background: white;
        }
        .photo img {
            width: 100%;
            height: auto;
            border-radius: 4px;
            display: block;
        }
        .filename {
            font-size: 12px;
            color: #666;
            margin: 5px 0;
            word-break: break-all;
        }
        .score {
            font-size: 11px;
            color: #999;
            margin: 3px 0;
        }
    </style>
</head>"""
