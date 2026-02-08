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
        print(f"\n{'='*60}")
        print(f"SCANNER.SCAN() CALLED")
        print(f"Folder: {self.folder}")
        print(f"Analyzers: {self.analyzers}")
        print(f"Threads: {self.threads}")
        print(f"Skip existing: {self.skip_existing}")
        print(f"{'='*60}\n")
        
        logger.info(f"Starting scan of {self.folder}")
        start_time = time.time()
        
        print("DEBUG: Discovering photos...")
        # Discover photos
        media = scan_multiple_directories(
            [self.folder],
            extensions=['.jpg', '.jpeg', '.png', '.raw', '.arw', '.cr2', '.nef'],
            recursive=True,
            show_progress=False
        )
        photos = filter_by_type(media, "photo")
        
        print(f"DEBUG: Found {len(photos)} photos")
        logger.info(f"Found {len(photos)} photos in {self.folder}")
        
        # Initialize progress
        self.progress = ScanProgress(len(photos))
        
        print(f"DEBUG: Progress initialized, checking which photos to scan...")
        # Filter photos that need scanning
        # IMPORTANT: For burst analysis, we should scan ALL photos together,
        # even if some were already scanned. Burst detection needs to see
        # relationships between ALL photos in the folder.
        photos_to_scan = []
        for photo in photos:
            sidecar = SidecarManager(photo.path)
            
            if self.skip_existing and sidecar.exists and not sidecar.is_stale():
                # Skip - already scanned and up-to-date
                # WARNING: This can break burst detection if only some photos are skipped!
                self.progress.completed += 1
            else:
                photos_to_scan.append(photo.path)
        
        print(f"DEBUG: {len(photos_to_scan)} photos to scan, {len(photos) - len(photos_to_scan)} skipped")
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
            print(f"DEBUG: Starting ThreadPoolExecutor with {self.threads} workers...")
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {
                    executor.submit(self._scan_photo, photo): photo 
                    for photo in photos_to_scan
                }
                
                print(f"DEBUG: Submitted {len(futures)} scan jobs")
                
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
        
        print(f"DEBUG: Completed individual photo scans: {results['scanned']} scanned")
        
        print(f"\n{'='*60}")
        print(f"BEFORE BURST CHECK")
        print(f"'burst' in self.analyzers: {'burst' in self.analyzers}")
        print(f"len(photos) > 1: {len(photos) > 1}")
        print(f"self.analyzers: {self.analyzers}")
        print(f"{'='*60}\n")
        
        # Run burst detection if requested
        if 'burst' in self.analyzers and len(photos) > 1:
            print(f"\n{'='*60}")
            print(f"BURST ANALYSIS STARTING")
            print(f"{'='*60}")
            print(f"Analyzers list: {self.analyzers}")
            print(f"Total photos: {len(photos)}")
            print(f"{'='*60}\n")
            
            logger.info("Running burst detection...")
            self.progress.current_analyzer = 'burst'
            self.progress.current_file = 'Analyzing burst groups...'
            
            if self.progress_callback:
                self.progress_callback(self.progress.to_dict())
            
            try:
                burst_results = self._analyze_bursts(photos)
                
                print(f"\n{'='*60}")
                print(f"BURST RESULTS: {len(burst_results)} photos analyzed")
                print(f"{'='*60}\n")
                
                # Update sidecars with burst data
                for photo_path_str, burst_data in burst_results.items():
                    photo_path = Path(photo_path_str)
                    sidecar = SidecarManager(photo_path)
                    sidecar.load()
                    sidecar.update_analysis('burst', burst_data)
                    sidecar.save()
                
                results['burst_groups'] = sum(1 for b in burst_results.values() if b.get('is_burst_candidate', False))
                logger.info(f"Burst detection complete: {results['burst_groups']} burst candidates")
                
                print(f"\n{'='*60}")
                print(f"BURST COMPLETE: {results['burst_groups']} candidates found")
                print(f"{'='*60}\n")
            
            except Exception as e:
                print(f"\n{'='*60}")
                print(f"BURST ERROR: {e}")
                print(f"{'='*60}\n")
                logger.error(f"Burst detection error: {e}")
                import traceback
                traceback.print_exc()
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
        Analyze photos for burst detection using BurstAnalyzer
        """
        from photo_tool.prescan.analyzers.burst import BurstAnalyzer
        
        logger.info(f"Running burst analysis on {len(photos)} photos...")
        
        # Extract photo paths
        photo_paths = [photo.path for photo in photos]
        
        # Create analyzer and run
        analyzer = BurstAnalyzer(
            time_threshold=3,
            similarity_threshold=0.85,
            max_neighbors=20
        )
        
        results = analyzer.analyze_batch(photo_paths)
        
        logger.info(f"Burst analysis complete: {sum(1 for r in results.values() if r['is_burst_candidate'])} burst candidates")
        return results
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """Get current scan progress"""
        if not self.progress:
            return None
        return self.progress.to_dict()
