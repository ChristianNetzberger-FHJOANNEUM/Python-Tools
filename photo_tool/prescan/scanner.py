"""
Folder Scanner - Pre-scans media folders and stores results in sidecars
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from photo_tool.io import scan_multiple_directories, filter_by_type, get_capture_time
from photo_tool.prescan.sidecar import SidecarManager
from photo_tool.analysis.similarity.blur import detect_blur, BlurMethod
from photo_tool.util.logging import get_logger

logger = get_logger("scanner")


class ScanProgress:
    """Progress tracking for folder scan"""
    
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.current_file = ""
        self.current_analyzer = ""
        self.errors = []
        self.start_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        remaining = (self.total - self.completed) / rate if rate > 0 else 0
        
        return {
            'status': 'complete' if self.completed >= self.total else 'running',
            'total': self.total,
            'completed': self.completed,
            'current_file': self.current_file,
            'current_analyzer': self.current_analyzer,
            'elapsed_seconds': int(elapsed),
            'estimated_remaining_seconds': int(remaining),
            'photos_per_second': round(rate, 2),
            'error_count': len(self.errors)
        }


class FolderScanner:
    """
    Scans media folders and stores analysis results in sidecars
    """
    
    def __init__(
        self,
        folder_path: Path,
        analyzers: Optional[List[str]] = None,
        threads: int = 4,
        skip_existing: bool = True,
        progress_callback: Optional[Callable] = None
    ):
        self.folder = Path(folder_path)
        self.analyzers = analyzers or ['blur']
        self.threads = threads
        self.skip_existing = skip_existing
        self.progress_callback = progress_callback
        self.progress = None
    
    def scan(self) -> Dict[str, Any]:
        """
        Scan folder and create/update sidecars
        
        Returns:
            Summary statistics
        """
        logger.info(f"Starting scan of {self.folder}")
        start_time = time.time()
        
        # Discover photos
        media = scan_multiple_directories(
            [self.folder],
            extensions=['.jpg', '.jpeg', '.png', '.raw', '.arw', '.cr2', '.nef'],
            recursive=True,
            show_progress=False
        )
        photos = filter_by_type(media, "photo")
        
        logger.info(f"Found {len(photos)} photos in {self.folder}")
        
        # Initialize progress
        self.progress = ScanProgress(len(photos))
        
        # Filter photos that need scanning
        photos_to_scan = []
        for photo in photos:
            sidecar = SidecarManager(photo.path)
            
            if self.skip_existing and sidecar.exists and not sidecar.is_stale():
                # Skip - already scanned and up-to-date
                self.progress.completed += 1
            else:
                photos_to_scan.append(photo.path)
        
        logger.info(f"Scanning {len(photos_to_scan)} photos ({len(photos) - len(photos_to_scan)} skipped)")
        
        # Scan photos in parallel
        results = {
            'total': len(photos),
            'scanned': 0,
            'skipped': len(photos) - len(photos_to_scan),
            'errors': 0,
            'analyzers': {},
            'burst_groups': 0
        }
        
        if len(photos_to_scan) > 0:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {
                    executor.submit(self._scan_photo, photo): photo 
                    for photo in photos_to_scan
                }
                
                for future in as_completed(futures):
                    photo = futures[future]
                    try:
                        result = future.result()
                        results['scanned'] += 1
                        
                        # Update progress
                        self.progress.completed += 1
                        self.progress.current_file = ""
                        
                        if self.progress_callback:
                            self.progress_callback(self.progress.to_dict())
                    
                    except Exception as e:
                        logger.error(f"Error scanning {photo}: {e}")
                        results['errors'] += 1
                        self.progress.errors.append(str(photo))
        
        # Run burst detection if requested
        if 'burst' in self.analyzers and len(photos) > 1:
            logger.info("Running burst detection...")
            self.progress.current_analyzer = 'burst'
            self.progress.current_file = 'Analyzing burst groups...'
            
            if self.progress_callback:
                self.progress_callback(self.progress.to_dict())
            
            try:
                burst_results = self._analyze_bursts(photos)
                
                # Update sidecars with burst data
                for photo_path_str, burst_data in burst_results.items():
                    photo_path = Path(photo_path_str)
                    sidecar = SidecarManager(photo_path)
                    sidecar.load()
                    sidecar.update_analysis('burst', burst_data)
                    sidecar.save()
                
                results['burst_groups'] = sum(1 for b in burst_results.values() if b.get('is_burst_candidate', False))
                logger.info(f"Burst detection complete: {results['burst_groups']} burst candidates")
            
            except Exception as e:
                logger.error(f"Burst detection error: {e}")
                results['burst_groups'] = 0
        
        # Final progress
        if self.progress_callback:
            self.progress_callback(self.progress.to_dict())
        
        elapsed = time.time() - start_time
        logger.info(f"Scan complete: {results['scanned']} scanned, {results['skipped']} skipped, {results['errors']} errors in {elapsed:.1f}s")
        
        return results
    
    def _scan_photo(self, photo_path: Path) -> Dict[str, Any]:
        """Scan single photo with all analyzers"""
        self.progress.current_file = photo_path.name
        
        sidecar = SidecarManager(photo_path)
        sidecar.load()
        
        results = {}
        
        # Run analyzers
        if 'blur' in self.analyzers:
            self.progress.current_analyzer = 'blur'
            blur_results = self._analyze_blur(photo_path)
            sidecar.update_analysis('blur', blur_results)
            results['blur'] = blur_results
        
        # Future: Add more analyzers
        # if 'histogram' in self.analyzers:
        #     histogram_results = self._analyze_histogram(photo_path)
        #     sidecar.update_analysis('histogram', histogram_results)
        
        # Save sidecar
        sidecar.save()
        
        return results
    
    def _analyze_blur(self, photo_path: Path) -> Dict[str, Any]:
        """Run all blur detection methods"""
        results = {}
        
        for method in [BlurMethod.LAPLACIAN, BlurMethod.TENENGRAD, BlurMethod.ROI]:
            try:
                score = detect_blur(photo_path, method=method)
                results[method.value] = {
                    'score': float(score),
                    'computed_at': datetime.now().isoformat(),
                    'method_version': '1.0'
                }
            except Exception as e:
                logger.error(f"Error computing {method.value} for {photo_path.name}: {e}")
                results[method.value] = {
                    'score': None,
                    'error': str(e)
                }
        
        return results
    
    def _analyze_bursts(self, photos: List) -> Dict[str, Dict[str, Any]]:
        """
        Analyze photos for burst detection
        Simplified version without separate analyzer class
        """
        results = {}
        
        # Get capture times
        photo_times = []
        for photo in photos:
            try:
                capture_time = get_capture_time(photo.path)
                photo_times.append((photo.path, capture_time))
            except Exception as e:
                logger.warning(f"Could not get capture time for {photo.path.name}: {e}")
                photo_times.append((photo.path, None))
        
        # Sort by capture time
        photo_times.sort(key=lambda x: x[1] if x[1] else datetime.min)
        
        # Analyze each photo
        time_threshold = 3  # seconds
        similarity_threshold = 0.85
        max_neighbors = 10
        
        for i, (photo_path, capture_time) in enumerate(photo_times):
            if capture_time is None:
                results[str(photo_path)] = {
                    'burst_neighbors': [],
                    'is_burst_candidate': False,
                    'burst_group_size': 1,
                    'error': 'No capture time'
                }
                continue
            
            # Find potential burst neighbors
            neighbors = []
            
            # Check previous photos
            for j in range(max(0, i - max_neighbors), i):
                prev_path, prev_time = photo_times[j]
                if prev_time is None:
                    continue
                
                time_diff = (capture_time - prev_time).total_seconds()
                if time_diff <= time_threshold:
                    neighbors.append({
                        'path': str(prev_path),
                        'time_diff': time_diff,
                        'similarity': 0.9,  # Simplified: just use time-based
                        'direction': 'previous'
                    })
            
            # Check next photos
            for j in range(i + 1, min(len(photo_times), i + max_neighbors + 1)):
                next_path, next_time = photo_times[j]
                if next_time is None:
                    continue
                
                time_diff = (next_time - capture_time).total_seconds()
                if time_diff <= time_threshold:
                    neighbors.append({
                        'path': str(next_path),
                        'time_diff': time_diff,
                        'similarity': 0.9,  # Simplified: just use time-based
                        'direction': 'next'
                    })
                else:
                    break
            
            # Store results
            results[str(photo_path)] = {
                'burst_neighbors': neighbors,
                'is_burst_candidate': len(neighbors) > 0,
                'burst_group_size': len(neighbors) + 1,
                'computed_at': datetime.now().isoformat()
            }
        
        logger.info(f"Burst analysis complete: {sum(1 for r in results.values() if r['is_burst_candidate'])} burst candidates")
        return results
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """Get current scan progress"""
        if not self.progress:
            return None
        return self.progress.to_dict()
