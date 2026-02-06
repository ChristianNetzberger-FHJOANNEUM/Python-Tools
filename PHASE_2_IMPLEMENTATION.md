# Phase 2 Implementation - Burst Detection & Enhanced Analyzers

## Overview

Phase 2 adds advanced pre-scanning capabilities with modular analyzer architecture:
- **Burst Detection** - Automatically groups burst photos
- **Modular Analyzers** - Clean separation of analysis logic
- **Enhanced Sidecars** - More comprehensive photo metadata

## New Features

### 1. Modular Analyzer Architecture

**Location:** `photo_tool/prescan/analyzers/`

**Structure:**
```
analyzers/
├── __init__.py          # Exports all analyzers
├── blur.py              # BlurAnalyzer
└── burst.py             # BurstAnalyzer
```

**Benefits:**
- Clean separation of concerns
- Easy to add new analyzers
- Consistent interface
- Independent testing

### 2. Blur Analyzer (`BlurAnalyzer`)

**File:** `photo_tool/prescan/analyzers/blur.py`

**Features:**
- Analyzes photos using all 3 blur methods
- Configurable method selection
- Error handling per method
- Consistent result format

**Usage:**
```python
from photo_tool.prescan.analyzers import BlurAnalyzer

analyzer = BlurAnalyzer()  # Uses all 3 methods by default
results = analyzer.analyze(photo_path)

# Results format:
{
    'laplacian': {
        'score': 125.4,
        'computed_at': '2024-06-20T10:00:00',
        'method_version': '1.0'
    },
    'tenengrad': {...},
    'roi': {...}
}
```

**Sidecar Storage:**
```json
{
    "analyses": {
        "blur": {
            "laplacian": {"score": 125.4, "computed_at": "..."},
            "tenengrad": {"score": 45.2, "computed_at": "..."},
            "roi": {"score": 87.3, "computed_at": "..."},
            "computed_at": "2024-06-20T10:00:00"
        }
    }
}
```

### 3. Burst Analyzer (`BurstAnalyzer`)

**File:** `photo_tool/prescan/analyzers/burst.py`

**Features:**
- Time-based burst detection (within N seconds)
- Visual similarity comparison
- Bi-directional neighbor links
- Configurable thresholds
- Batch processing for efficiency

**Parameters:**
- `time_threshold` - Max seconds between burst photos (default: 3)
- `similarity_threshold` - Min similarity score 0-1 (default: 0.85)
- `max_neighbors` - Max neighbors to check (default: 20)

**Algorithm:**
1. Sort photos by capture time
2. For each photo, check nearby photos (within time threshold)
3. Calculate visual similarity using histogram correlation
4. Link photos with similarity above threshold
5. Store bidirectional links in sidecars

**Similarity Calculation:**
- Resize images to 256x256 for speed
- Convert to grayscale
- Calculate histograms
- Compare using correlation method
- Returns score 0-1 (1 = identical)

**Usage:**
```python
from photo_tool.prescan.analyzers import BurstAnalyzer

analyzer = BurstAnalyzer(
    time_threshold=3,
    similarity_threshold=0.85
)

# Batch analyze all photos
results = analyzer.analyze_batch(
    photos,
    progress_callback=lambda c, t: print(f"{c}/{t}")
)

# Results format per photo:
{
    'burst_neighbors': [
        {
            'path': 'photo2.jpg',
            'time_diff': 0.5,      # seconds
            'similarity': 0.92,     # 0-1
            'direction': 'next'     # or 'previous'
        },
        ...
    ],
    'is_burst_candidate': True,
    'burst_group_size': 5,
    'computed_at': '2024-06-20T10:00:00'
}
```

**Sidecar Storage:**
```json
{
    "analyses": {
        "burst": {
            "burst_neighbors": [
                {
                    "path": "E:/Photos/IMG_1235.jpg",
                    "time_diff": 0.52,
                    "similarity": 0.923,
                    "direction": "next"
                }
            ],
            "is_burst_candidate": true,
            "burst_group_size": 3,
            "computed_at": "2024-06-20T10:00:00"
        }
    }
}
```

### 4. Enhanced Folder Scanner

**File:** `photo_tool/prescan/scanner.py`

**Updates:**
- Uses modular analyzers
- Supports burst detection in batch mode
- Progress tracking for burst analysis
- Updates all sidecars after burst detection

**Workflow:**
1. **Blur Detection Phase** (Parallel)
   - Scan each photo individually
   - Calculate blur scores (all 3 methods)
   - Save to sidecars

2. **Burst Detection Phase** (Batch)
   - Analyze all photos together
   - Find temporal and visual similarities
   - Update all sidecars with burst links

**Progress Tracking:**
```
Discovering photos... (Phase 0)
↓
Scanning photos... (Phase 1)
├─ Blur analysis: photo1.jpg
├─ Blur analysis: photo2.jpg
└─ ...
↓
Analyzing burst groups... (Phase 2)
├─ Burst analysis: 1/1000
├─ Burst analysis: 2/1000
└─ ...
↓
Complete!
```

## API Changes

### Updated Scan Endpoint

**Endpoint:** `POST /api/media/folders/<path>/scan`

**Body:**
```json
{
    "analyzers": ["blur", "burst"],  // New: burst support
    "force": false,
    "threads": 4
}
```

**Response:**
```json
{
    "success": true,
    "message": "Scan started",
    "folder": "E:/Photos/2024/"
}
```

**Scan Results:**
```json
{
    "total": 2188,
    "scanned": 1500,
    "skipped": 688,
    "errors": 0,
    "burst_groups": 87  // New: burst candidates count
}
```

## Sidecar Format Evolution

### Version 1.0 Structure

```json
{
    "version": "1.0",
    "photo": {
        "path": "E:/Photos/IMG_1234.jpg",
        "name": "IMG_1234.jpg",
        "size_bytes": 4567890,
        "modified_at": "2024-06-15T14:30:00"
    },
    "scan_info": {
        "scanned_at": "2024-06-20T10:00:00",
        "scanner_version": "1.0.0",
        "updated_at": "2024-06-20T10:05:30"
    },
    "analyses": {
        "blur": {
            "laplacian": {
                "score": 125.4,
                "computed_at": "2024-06-20T10:00:00",
                "method_version": "1.0"
            },
            "tenengrad": {
                "score": 45.2,
                "computed_at": "2024-06-20T10:00:00",
                "method_version": "1.0"
            },
            "roi": {
                "score": 87.3,
                "computed_at": "2024-06-20T10:00:00",
                "method_version": "1.0"
            },
            "computed_at": "2024-06-20T10:00:00"
        },
        "burst": {
            "burst_neighbors": [
                {
                    "path": "E:/Photos/IMG_1235.jpg",
                    "time_diff": 0.52,
                    "similarity": 0.923,
                    "direction": "next"
                },
                {
                    "path": "E:/Photos/IMG_1233.jpg",
                    "time_diff": 0.48,
                    "similarity": 0.915,
                    "direction": "previous"
                }
            ],
            "is_burst_candidate": true,
            "burst_group_size": 3,
            "computed_at": "2024-06-20T10:05:30"
        }
    }
}
```

## Performance Considerations

### Blur Analysis
- **Speed:** ~3-5 photos/second with 3 methods
- **Parallelism:** 4 threads by default
- **For 2000 photos:** ~10-15 minutes

### Burst Analysis
- **Speed:** ~50-100 photos/second (batch mode)
- **Sequential:** Single-threaded for temporal coherence
- **For 2000 photos:** ~30-60 seconds

### Total Scan Time
- **2000 photos:** ~15-20 minutes
- **10000 photos:** ~1-2 hours
- **Recommendation:** Run overnight for large archives

### Optimization Opportunities
1. **Burst Similarity:**
   - Currently uses histogram correlation
   - Could use perceptual hashing (faster)
   - Could use ORB features (more accurate)

2. **Parallelism:**
   - Blur: Already parallel
   - Burst: Could parallelize similarity calculations

3. **Caching:**
   - Skip unchanged photos
   - Incremental burst updates

## GUI Integration (Phase 2b)

### Planned Features

1. **Media Manager Enhancements:**
   - Burst analyzer toggle
   - Burst detection progress
   - Burst group statistics

2. **Photos Tab:**
   - Burst badges on thumbnails
   - Burst group viewer/lightbox
   - "Best of burst" selection
   - Burst navigator (prev/next in group)

3. **Workspace Tab:**
   - Show burst statistics
   - "Resolve bursts" action

4. **Projects Tab:**
   - Burst handling options:
     - Keep all
     - Keep best (by rating)
     - Manual selection
     - Skip bursts

## Testing

### Blur Analyzer Tests
```python
# Test all methods
analyzer = BlurAnalyzer()
results = analyzer.analyze(photo_path)
assert 'laplacian' in results
assert 'tenengrad' in results
assert 'roi' in results

# Test single method
analyzer = BlurAnalyzer(methods=[BlurMethod.LAPLACIAN])
results = analyzer.analyze(photo_path)
assert len(results) == 1
```

### Burst Analyzer Tests
```python
# Test time-based detection
photos = [photo1, photo2, photo3]  # 0.5s apart
results = analyzer.analyze_batch(photos)
assert results[str(photo1)]['is_burst_candidate']
assert len(results[str(photo1)]['burst_neighbors']) > 0

# Test similarity threshold
analyzer = BurstAnalyzer(similarity_threshold=0.95)  # Very strict
results = analyzer.analyze_batch(photos)
# Fewer bursts detected
```

### Integration Tests
```python
# Test full scan with both analyzers
scanner = FolderScanner(
    folder,
    analyzers=['blur', 'burst'],
    threads=4
)
results = scanner.scan()
assert results['scanned'] > 0
assert results['burst_groups'] > 0

# Verify sidecars
sidecar = SidecarManager(photos[0])
sidecar.load()
assert 'blur' in sidecar.get('analyses', {})
assert 'burst' in sidecar.get('analyses', {})
```

## Known Limitations

1. **Burst Detection Accuracy:**
   - Histogram correlation is fast but not perfect
   - May miss bursts with significant composition changes
   - May falsely link similar-looking photos
   - Threshold tuning required per camera

2. **Performance:**
   - Burst analysis is sequential (temporal coherence)
   - Large folders take time (but only once!)
   - Consider running overnight

3. **Memory Usage:**
   - Loads all photo paths in memory
   - Similarity calculation uses OpenCV
   - For 10000 photos: ~500MB RAM

4. **Capture Time Dependency:**
   - Requires valid EXIF timestamps
   - Photos without timestamps excluded
   - Camera clock sync issues affect grouping

## Future Enhancements (Phase 3)

1. **Histogram Analyzer**
   - Exposure histogram
   - Color distribution
   - Contrast metrics

2. **EXIF Analyzer**
   - Bulk EXIF extraction
   - Camera model
   - Lens info
   - GPS data

3. **Face Detection Analyzer**
   - Detect faces
   - Count faces
   - Face similarity

4. **Quality Metrics Analyzer**
   - Exposure quality
   - Noise level
   - Sharpness
   - Composition analysis

5. **Perceptual Hash Analyzer**
   - Fast duplicate detection
   - Near-duplicate finding
   - Crop detection

## Migration Guide

### Updating Existing Scans

If you already scanned folders with blur-only:
1. Re-scan with burst enabled
2. Burst analysis will update existing sidecars
3. Blur scores are preserved

### Sidecar Compatibility

- Version 1.0 sidecars fully compatible
- New analyzers add to `analyses` section
- Existing data never overwritten
- Safe to re-scan anytime

### Performance Tips

1. **First Scan:**
   - Enable both blur and burst
   - Run overnight
   - All data available immediately

2. **Incremental Updates:**
   - Use `force: false` (default)
   - Only scans new/modified photos
   - Fast for regular updates

3. **Burst Re-analysis:**
   - If you change thresholds
   - Re-scan with `force: true`
   - Blur scores preserved

## Documentation

- Architecture: `PRESCAN_ARCHITECTURE.md`
- Phase 1 fixes: `PHASE_1_FIXES_AND_ENHANCEMENTS.md`
- Blur methods: `BLUR_METHODS_USAGE_GUIDE.md`
- Media manager: `MEDIA_MANAGER_GUIDE.md`

## Summary

✅ **Modular Analyzer Architecture**
✅ **BlurAnalyzer** - Clean, testable, documented
✅ **BurstAnalyzer** - Time + similarity based grouping
✅ **Enhanced FolderScanner** - Multi-phase scanning
✅ **Comprehensive Sidecars** - All analysis data stored

**Phase 2 Core Complete** - Ready for GUI integration in Phase 2b!
