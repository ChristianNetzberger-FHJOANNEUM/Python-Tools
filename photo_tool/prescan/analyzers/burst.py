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
            Dictionary mapping photo path to burst analysis:
            {
                'photo1.jpg': {
                    'burst_neighbors': [
                        {'path': 'photo2.jpg', 'time_diff': 0.5, 'similarity': 0.92},
                        ...
                    ],
                    'is_burst_candidate': True,
                    'burst_group_size': 5
                },
                ...
            }
        """
        # Import here to avoid circular dependencies
        from photo_tool.io import get_capture_time
        from photo_tool.util.logging import get_logger
        
        logger = get_logger("burst_analyzer")
        logger.info(f"Analyzing {len(photos)} photos for bursts...")
        
        results = {}
        
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
                results[str(photo)] = {
                    'burst_neighbors': [],
                    'is_burst_candidate': False,
                    'burst_group_size': 1,
                    'error': 'No capture time'
                }
                continue
            
            # Find potential burst neighbors
            neighbors = []
            
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
                        neighbors.append({
                            'path': str(prev_photo),
                            'time_diff': time_diff,
                            'similarity': similarity,
                            'direction': 'previous'
                        })
            
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
                        neighbors.append({
                            'path': str(next_photo),
                            'time_diff': time_diff,
                            'similarity': similarity,
                            'direction': 'next'
                        })
                else:
                    break  # Too far apart, no need to check further
            
            # Store results
            results[str(photo)] = {
                'burst_neighbors': neighbors,
                'is_burst_candidate': len(neighbors) > 0,
                'burst_group_size': len(neighbors) + 1,
                'computed_at': datetime.now().isoformat()
            }
            
            if len(neighbors) > 0:
                logger.debug(f"Found burst: {photo.name} has {len(neighbors)} neighbors")
        
        logger.info(f"Burst analysis complete: {sum(1 for r in results.values() if r['is_burst_candidate'])} burst candidates found")
        
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
