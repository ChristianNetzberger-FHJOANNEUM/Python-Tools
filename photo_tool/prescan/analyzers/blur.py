"""
Blur Analysis for pre-scanning
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class BlurAnalyzer:
    """
    Analyzes photos for blur using multiple methods
    Stores results in sidecar files
    """
    
    def __init__(self, methods=None):
        """
        Initialize blur analyzer
        
        Args:
            methods: List of method names to use (default: all 3)
                    ['laplacian', 'tenengrad', 'roi']
        """
        self.methods = methods or ['laplacian', 'tenengrad', 'roi']
    
    def analyze(self, photo_path: Path) -> Dict[str, Any]:
        """
        Analyze photo for blur with all configured methods
        
        Returns:
            Dictionary with blur scores for each method:
            {
                'laplacian': {'score': 125.4, 'computed_at': '...'},
                'tenengrad': {'score': 45.2, 'computed_at': '...'},
                'roi': {'score': 87.3, 'computed_at': '...'}
            }
        """
        # Import here to avoid circular dependencies
        from photo_tool.analysis.similarity.blur import detect_blur, BlurMethod
        from photo_tool.util.logging import get_logger
        
        logger = get_logger("blur_analyzer")
        
        # Map string names to BlurMethod enum
        method_map = {
            'laplacian': BlurMethod.LAPLACIAN,
            'tenengrad': BlurMethod.TENENGRAD,
            'roi': BlurMethod.ROI
        }
        
        results = {}
        
        for method_name in self.methods:
            method = method_map.get(method_name)
            if not method:
                continue
            
            try:
                score = detect_blur(photo_path, method=method)
                results[method.value] = {
                    'score': float(score),
                    'computed_at': datetime.now().isoformat(),
                    'method_version': '1.0'
                }
                
                logger.debug(f"Blur {method.value} for {photo_path.name}: {score:.2f}")
            
            except Exception as e:
                logger.error(f"Error computing {method.value} for {photo_path.name}: {e}")
                results[method.value] = {
                    'score': None,
                    'error': str(e),
                    'computed_at': datetime.now().isoformat()
                }
        
        return results
    
    @property
    def name(self) -> str:
        """Analyzer name for sidecar storage"""
        return 'blur'
