"""
Burst Detection Analysis for pre-scanning
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class BurstLink:
    """Link to a burst neighbor"""
    photo_path: str
    time_diff_seconds: float
    similarity_score: float


class BurstAnalyzer:
    """
    Analyzes photos for burst grouping
    Stores burst links in sidecar files
    """
    
    def __init__(
        self,
        time_threshold: int = 3,
        similarity_threshold: float = 0.85,
        max_neighbors: int = 20
    ):
        """
        Initialize burst analyzer
        
        Args:
            time_threshold: Max seconds between burst photos
            similarity_threshold: Min similarity for burst grouping (0-1)
            max_neighbors: Max number of neighbors to compare
        """
        self.time_threshold = time_threshold
        self.similarity_threshold = similarity_threshold
        self.max_neighbors = max_neighbors
    
    def analyze_batch(
        self,
        photos: List[Path],
        progress_callback=None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze a batch of photos for burst detection
        
        Args:
            photos: List of photo paths (should be sorted by capture time)
            progress_callback: Optional callback(completed, total)
        
        Returns:
            Dictionary mapping photo path to burst analysis (Version 2 format):
            {
                'photo1.jpg': {
                    'is_burst_candidate': True,
                    'burst_id': 'a4720613550b',
                    'neighbors': ['photo2.jpg', 'photo3.jpg'],
                    'score': 0.92,
                    'detection_date': 1739024645
                },
                ...
            }
        
        Format: Version 2 (Spec-compliant)
        - Uses 'neighbors' (array of strings) not 'burst_neighbors' (array of objects)
        - Generates 'burst_id' for each burst group
        - Uses 'detection_date' (Unix timestamp) not 'computed_at' (ISO string)
        """
        import hashlib
        import time
        
        # Import here to avoid circular dependencies
        from photo_tool.io import get_capture_time
        from photo_tool.util.logging import get_logger
        
        logger = get_logger("burst_analyzer")
        logger.info(f"Analyzing {len(photos)} photos for bursts...")
        
        # Phase 1: Find neighbors for each photo
        photo_neighbors = {}  # path -> list of neighbor paths
        
        # Get capture times
        photo_times = []
        for photo in photos:
            try:
                capture_time = get_capture_time(photo)
                photo_times.append((photo, capture_time))
            except Exception as e:
                logger.warning(f"Could not get capture time for {photo.name}: {e}")
                photo_times.append((photo, None))
        
        # Sort by capture time
        photo_times.sort(key=lambda x: x[1] if x[1] else datetime.min)
        
        # Analyze each photo
        for i, (photo, capture_time) in enumerate(photo_times):
            if progress_callback:
                progress_callback(i + 1, len(photo_times))
            
            if capture_time is None:
                photo_neighbors[str(photo)] = []
                continue
            
            # Find potential burst neighbors
            neighbors = []
            similarities = []
            
            # Check previous photos
            for j in range(max(0, i - self.max_neighbors), i):
                prev_photo, prev_time = photo_times[j]
                if prev_time is None:
                    continue
                
                time_diff = (capture_time - prev_time).total_seconds()
                if time_diff <= self.time_threshold:
                    # Calculate similarity
                    similarity = self._calculate_similarity(photo, prev_photo)
                    if similarity >= self.similarity_threshold:
                        neighbors.append(str(prev_photo))
                        similarities.append(similarity)
            
            # Check next photos
            for j in range(i + 1, min(len(photo_times), i + self.max_neighbors + 1)):
                next_photo, next_time = photo_times[j]
                if next_time is None:
                    continue
                
                time_diff = (next_time - capture_time).total_seconds()
                if time_diff <= self.time_threshold:
                    # Calculate similarity
                    similarity = self._calculate_similarity(photo, next_photo)
                    if similarity >= self.similarity_threshold:
                        neighbors.append(str(next_photo))
                        similarities.append(similarity)
                else:
                    break  # Too far apart, no need to check further
            
            photo_neighbors[str(photo)] = {
                'neighbors': neighbors,
                'avg_similarity': sum(similarities) / len(similarities) if similarities else 0.0
            }
        
        # Phase 2: Group photos into burst groups (connected components)
        visited = set()
        burst_groups = []
        
        def dfs(photo_path, group):
            """Depth-first search to find all photos in a burst group"""
            if photo_path in visited:
                return
            visited.add(photo_path)
            group.append(photo_path)
            
            # Visit all neighbors
            for neighbor_path in photo_neighbors.get(photo_path, {}).get('neighbors', []):
                dfs(neighbor_path, group)
        
        # Find all burst groups
        for photo_path in photo_neighbors:
            if photo_path not in visited and photo_neighbors[photo_path]['neighbors']:
                group = []
                dfs(photo_path, group)
                if len(group) > 1:
                    burst_groups.append(sorted(group))  # Sort for consistency
        
        logger.info(f"Found {len(burst_groups)} burst groups")
        
        # Phase 3: Assign burst_id to each group
        burst_ids = {}  # photo_path -> burst_id
        detection_ts = int(time.time())
        
        for group in burst_groups:
            # Generate consistent burst_id from sorted group members
            group_str = '|'.join(sorted(group))
            burst_id = hashlib.md5(group_str.encode()).hexdigest()[:12]
            
            for photo_path in group:
                burst_ids[photo_path] = burst_id
        
        # Phase 4: Build results in Version 2 format
        results = {}
        for photo_path, neighbor_info in photo_neighbors.items():
            neighbors = neighbor_info['neighbors']
            avg_similarity = neighbor_info['avg_similarity']
            
            if neighbors:
                # Photo is in a burst
                results[photo_path] = {
                    'is_burst_candidate': True,
                    'burst_id': burst_ids.get(photo_path),
                    'neighbors': neighbors,
                    'score': round(avg_similarity, 2),
                    'detection_date': detection_ts
                }
                logger.debug(f"Burst: {Path(photo_path).name} -> group {burst_ids.get(photo_path)}")
            else:
                # Photo is not in a burst
                results[photo_path] = {
                    'is_burst_candidate': False,
                    'burst_id': None,
                    'neighbors': [],
                    'score': 0.0,
                    'detection_date': detection_ts
                }
        
        logger.info(f"Burst analysis complete: {sum(1 for r in results.values() if r['is_burst_candidate'])} burst candidates in {len(burst_groups)} groups")
        
        return results
    
    def _calculate_similarity(self, photo1: Path, photo2: Path) -> float:
        """
        Calculate visual similarity between two photos
        
        Returns:
            Similarity score 0-1 (1 = identical)
        """
        from photo_tool.util.logging import get_logger
        logger = get_logger("burst_analyzer")
        
        try:
            # Load images
            img1 = cv2.imread(str(photo1))
            img2 = cv2.imread(str(photo2))
            
            if img1 is None or img2 is None:
                return 0.0
            
            # Resize to same size for comparison
            target_size = (256, 256)
            img1 = cv2.resize(img1, target_size)
            img2 = cv2.resize(img2, target_size)
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Calculate histogram correlation
            hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
            
            # Normalize histograms
            cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
            
            # Compare histograms
            similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            return max(0.0, min(1.0, similarity))
        
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    @property
    def name(self) -> str:
        """Analyzer name for sidecar storage"""
        return 'burst'
