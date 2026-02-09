"""
Histogram Calculation
=====================

Calculate luminance and RGB histograms from images.
Supports JPEG, PNG, and RAW formats.
"""

import numpy as np
from PIL import Image
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import rawpy
    HAS_RAWPY = True
except ImportError:
    HAS_RAWPY = False


def load_image(image_path: str | Path) -> np.ndarray:
    """
    Load image as numpy array (RGB, 0-255).
    Supports JPEG, PNG, and RAW formats.
    
    Args:
        image_path: Path to image file
        
    Returns:
        RGB array (height, width, 3) with values 0-255
    """
    path = Path(image_path)
    
    # Check if RAW file
    if HAS_RAWPY and path.suffix.upper() in ['.NEF', '.CR2', '.ARW', '.DNG', '.RAF', '.ORF', '.RW2']:
        with rawpy.imread(str(path)) as raw:
            rgb = raw.postprocess(
                use_camera_wb=True,
                output_bps=8
            )
        return rgb
    
    # Regular image file
    img = Image.open(path)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    return np.array(img)


def calculate_luminance_histogram(image_array: np.ndarray, bins: int = 256) -> List[int]:
    """
    Calculate luminance histogram from RGB image.
    Uses ITU-R BT.709 weights for RGB to luminance conversion.
    
    Args:
        image_array: RGB array (height, width, 3)
        bins: Number of histogram bins (default: 256)
        
    Returns:
        List of histogram values (length = bins)
    """
    # Convert RGB to luminance using ITU-R BT.709 weights
    # Y = 0.2126*R + 0.7152*G + 0.0722*B
    r, g, b = image_array[:, :, 0], image_array[:, :, 1], image_array[:, :, 2]
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b).astype(np.uint8)
    
    # Calculate histogram
    hist, _ = np.histogram(luminance.flatten(), bins=bins, range=(0, 256))
    
    return hist.tolist()


def calculate_rgb_histogram(image_array: np.ndarray, bins: int = 256) -> Dict[str, List[int]]:
    """
    Calculate separate R, G, B histograms.
    
    Args:
        image_array: RGB array (height, width, 3)
        bins: Number of histogram bins (default: 256)
        
    Returns:
        Dict with keys 'r', 'g', 'b' containing histogram lists
    """
    r, g, b = image_array[:, :, 0], image_array[:, :, 1], image_array[:, :, 2]
    
    hist_r, _ = np.histogram(r.flatten(), bins=bins, range=(0, 256))
    hist_g, _ = np.histogram(g.flatten(), bins=bins, range=(0, 256))
    hist_b, _ = np.histogram(b.flatten(), bins=bins, range=(0, 256))
    
    return {
        'r': hist_r.tolist(),
        'g': hist_g.tolist(),
        'b': hist_b.tolist()
    }


def calculate_histogram(
    image_path: str | Path,
    mode: str = 'luminance',
    bins: int = 256,
    downsample: Optional[int] = None
) -> Dict:
    """
    Calculate histogram from image file.
    Main entry point for histogram calculation.
    
    Args:
        image_path: Path to image file
        mode: 'luminance' or 'rgb' (default: 'luminance')
        bins: Number of histogram bins (default: 256)
        downsample: Downsample factor for faster calculation (e.g., 4 = 1/4 resolution)
        
    Returns:
        Dict with histogram data and statistics
        
    Example:
        >>> hist = calculate_histogram('photo.jpg')
        >>> print(hist['histogram'])  # List of 256 values
        >>> print(hist['stats']['mean'])  # Average brightness
    """
    # Load image
    img = load_image(image_path)
    
    # Downsample for performance
    if downsample and downsample > 1:
        h, w = img.shape[:2]
        img = img[::downsample, ::downsample, :]
    
    # Calculate histogram
    if mode == 'luminance':
        histogram = calculate_luminance_histogram(img, bins)
        
        # Calculate statistics
        luminance = (0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2])
        
        return {
            'mode': 'luminance',
            'histogram': histogram,
            'bins': bins,
            'stats': {
                'mean': float(np.mean(luminance)),
                'median': float(np.median(luminance)),
                'std': float(np.std(luminance)),
                'min': int(np.min(luminance)),
                'max': int(np.max(luminance))
            }
        }
    
    elif mode == 'rgb':
        histogram = calculate_rgb_histogram(img, bins)
        
        return {
            'mode': 'rgb',
            'histogram': histogram,
            'bins': bins,
            'stats': {
                'r_mean': float(np.mean(img[:, :, 0])),
                'g_mean': float(np.mean(img[:, :, 1])),
                'b_mean': float(np.mean(img[:, :, 2]))
            }
        }
    
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'luminance' or 'rgb'.")


# Standalone test
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python histogram.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print(f"\n📊 Calculating histogram for: {image_path}")
    print("=" * 60)
    
    # Luminance histogram
    hist_data = calculate_histogram(image_path, mode='luminance', downsample=4)
    
    print(f"\n✅ Histogram calculated ({hist_data['bins']} bins)")
    print(f"\n📈 Statistics:")
    for key, value in hist_data['stats'].items():
        print(f"  {key:10s}: {value:.2f}")
    
    print(f"\n💡 Histogram preview (first 10 values):")
    print(f"  {hist_data['histogram'][:10]}")
    
    # RGB histogram
    hist_rgb = calculate_histogram(image_path, mode='rgb', downsample=4)
    print(f"\n🎨 RGB Means:")
    for key, value in hist_rgb['stats'].items():
        print(f"  {key:10s}: {value:.2f}")
