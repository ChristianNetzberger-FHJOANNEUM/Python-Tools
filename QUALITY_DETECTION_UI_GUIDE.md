# Quality Detection UI - Complete Guide

## New Features Implemented

### 1. **Project Selector in Header** ✅
- Added project dropdown next to workspace selector
- Allows quick project switching from any tab
- Shows "No project selected" when none is active
- Automatically loads project settings on selection

### 2. **Quality Detection Settings in Projects Tab** ✅
- **Blur Detection Controls:**
  - Enable/disable toggle
  - Adjustable blur threshold slider (50-200)
    - 50 = Very strict (flags more photos)
    - 100 = Default (balanced)
    - 200 = Very lenient (only very blurry photos)
  - Configurable auto-flag color (Red, Yellow, Blue, Purple)
  - "Detect Blurry Photos" button
  - Real-time progress bar showing:
    - Current file being analyzed
    - Progress (X / Y photos)
    - Number of photos flagged
  - Completion message with statistics
  - Score distribution chart showing quality breakdown

- **Burst Detection Controls:**
  - Enable/disable toggle
  - Time threshold slider (1-10 seconds)
  - Similarity threshold slider (80-99%)
  - Info message about automatic processing

### 3. **Enhanced Statistics Display** ✅
- Added "Blurry Photos" stat card in header
- Displays after blur detection runs
- Red background with count of flagged photos
- Shows alongside:
  - Total Photos
  - Rated Photos
  - Burst Groups

### 4. **Improved Blur Detection Reporting** ✅
- **Score Distribution:** Shows breakdown of all photos by quality:
  - Very Blurry (0-50)
  - Blurry (50-100)
  - Acceptable (100-150)
  - Sharp (150-200)
  - Very Sharp (200+)
- **Detailed Statistics:**
  - Total photos analyzed
  - Number flagged as blurry
  - Threshold used
- **Real-time Progress:**
  - Visual progress bar
  - Current filename being processed
  - Live count of flagged photos

## User Workflow

### Step 1: Select Workspace and Project
```
1. Use workspace dropdown to select your photo collection
2. Use project dropdown to select or create a project
3. Navigate to "Projects" tab
```

### Step 2: Configure Quality Detection Settings
```
1. In Projects tab, scroll to "Quality Detection Settings"
2. Adjust blur threshold:
   - Move slider left for stricter detection
   - Move slider right for more lenient detection
3. Choose flag color (default: red)
4. Configure burst detection parameters if needed
5. Click "💾 Save Settings"
```

### Step 3: Run Blur Detection
```
1. Click "🔍 Detect Blurry Photos" button
2. Watch progress bar:
   - See current file being analyzed
   - Track progress (e.g., "234 / 961")
   - Monitor flagged count
3. Wait for completion message
4. Review score distribution
```

### Step 4: Review Flagged Photos
```
1. Navigate to "Photos" tab
2. Use color filter to show only red (or your chosen color)
3. Review flagged photos
4. Delete unwanted blurry photos
5. Re-export gallery without blurry photos
```

## Threshold Recommendations

### Conservative (High Quality Galleries)
```yaml
blur_threshold: 120-150
use_case: Professional portfolios, print galleries
result: Flags moderately blurry photos
```

### Balanced (Default)
```yaml
blur_threshold: 100
use_case: General photo collections, web galleries
result: Flags noticeably blurry photos
```

### Lenient (Casual Collections)
```yaml
blur_threshold: 70-90
use_case: Family snapshots, casual slideshows
result: Only flags very blurry photos
```

### Very Strict (Ultra High Quality)
```yaml
blur_threshold: 150-200
use_case: Magazine quality, exhibitions
result: Flags anything not perfectly sharp
```

## Understanding Blur Scores

### Score Interpretation
| Score Range | Quality Level | Description |
|-------------|---------------|-------------|
| 200+        | Very Sharp    | Excellent focus, crisp details |
| 150-200     | Sharp         | Good focus, clear details |
| 100-150     | Acceptable    | Adequate sharpness for most uses |
| 50-100      | Blurry        | Noticeable blur, details soft |
| 0-50        | Very Blurry   | Severe blur, unusable |

### Example Scenarios

**Scenario 1: First Run - No Photos Flagged**
- **Cause:** Threshold too low (e.g., default 100 but all photos score > 100)
- **Solution:** Increase threshold to 120-150 and re-run
- **Expected Result:** More photos will be flagged

**Scenario 2: Too Many Photos Flagged**
- **Cause:** Threshold too high for your photo quality
- **Solution:** Decrease threshold to 70-90 and re-run
- **Expected Result:** Fewer photos flagged

**Scenario 3: Mixed Photo Sources**
- **Problem:** DSLR photos (high quality) mixed with smartphone photos (variable quality)
- **Solution:** 
  - Use separate projects with different thresholds
  - Or use moderate threshold (90-110) for balanced filtering

## Technical Details

### API Endpoints

#### Update Quality Settings
```http
PUT /api/projects/{project_id}/quality-settings
Content-Type: application/json

{
  "quality_settings": {
    "blur_detection_enabled": true,
    "blur_threshold": 100.0,
    "blur_auto_flag_color": "red",
    "burst_detection_enabled": true,
    "burst_time_threshold": 3,
    "burst_similarity_threshold": 0.95
  }
}
```

#### Run Blur Detection
```http
POST /api/quality/detect-blur
Content-Type: application/json

{
  "threshold": 100.0,
  "auto_flag": true,
  "flag_color": "red"
}
```

#### Monitor Progress (SSE)
```http
GET /api/quality/blur-progress
```

### Data Structure

**Quality Settings (stored per project):**
```python
@dataclass
class QualityDetectionSettings:
    # Blur detection
    blur_detection_enabled: bool = True
    blur_threshold: float = 100.0
    blur_auto_flag_color: str = "red"
    
    # Burst detection
    burst_detection_enabled: bool = True
    burst_time_threshold: int = 3
    burst_similarity_threshold: float = 0.95
    burst_auto_organize: bool = False
```

**Blur Detection Results:**
```javascript
{
  total_analyzed: 961,
  flagged_count: 27,
  threshold: 100.0,
  score_distribution: {
    'Very Blurry (0-50)': 3,
    'Blurry (50-100)': 24,
    'Acceptable (100-150)': 234,
    'Sharp (150-200)': 456,
    'Very Sharp (200+)': 244
  }
}
```

## Troubleshooting

### Issue: "No photos flagged but I see blurry photos"

**Diagnosis Steps:**
1. Check the score distribution chart
2. Identify which range your blurry photos fall into
3. Adjust threshold accordingly

**Example:**
```
If distribution shows:
- Very Blurry (0-50): 0
- Blurry (50-100): 0
- Acceptable (100-150): 234  ← Your "blurry" photos are here
- Sharp (150-200): 456
- Very Sharp (200+): 271

Solution: Increase threshold to 150 to flag "Acceptable" range
```

### Issue: "Too many good photos are flagged"

**Diagnosis:**
- Check if threshold is too high
- Review score distribution

**Solution:**
1. Lower threshold (e.g., from 120 to 80)
2. Re-run detection
3. Or manually remove red flags from good photos

### Issue: "Progress bar stuck"

**Possible Causes:**
- Large photo file (slow to process)
- Server overload
- Network issue

**Solution:**
1. Check browser console for errors
2. Refresh page
3. Re-run detection

### Issue: "Score distribution not showing"

**Cause:**
- Detection hasn't been run yet
- Or completed but stats not loaded

**Solution:**
1. Ensure detection completes successfully
2. Check for "Complete!" message
3. Refresh page if needed

## Best Practices

### 1. **Test Before Full Scan**
- Start with a small test project
- Adjust threshold based on results
- Then apply to full collection

### 2. **Use Different Projects for Different Quality Standards**
```
Project: "Portfolio 2024" → threshold: 150 (strict)
Project: "Family Vacation" → threshold: 90 (lenient)
Project: "Best of Year" → threshold: 130 (moderate)
```

### 3. **Review Before Deleting**
- Always manually review flagged photos
- Blur detection is a suggestion, not final decision
- Some artistic photos may be intentionally soft

### 4. **Combine with Other Filters**
- Use color filters to organize workflow:
  - Red = Blurry (for deletion)
  - Yellow = Review needed
  - Green = Approved for export
- Combine with rating filters for refined selection

### 5. **Save Settings Per Project**
- Each project remembers its quality settings
- No need to reconfigure every time
- Settings persist across sessions

## Performance

### Processing Speed
- ~5-15 photos/second (varies by resolution)
- 1000 photos ≈ 1-3 minutes
- Progress updates every 0.5 seconds

### Optimization Tips
- Close other applications during detection
- Use lower resolution for faster testing
- Run on fewer photos initially to test threshold

## Future Enhancements

### Planned Features
1. **Batch Operations:**
   - Delete all flagged photos at once
   - Change all flagged photos to different color
   
2. **Advanced Blur Detection:**
   - Face-aware blur detection
   - Region-of-interest analysis
   - Motion blur vs focus blur detection

3. **Burst Management:**
   - Automatic burst subfolder organization
   - Lightbox for burst photo selection
   - Best-photo auto-selection from bursts

4. **Quality Scoring:**
   - Overall quality metric
   - Exposure analysis
   - Composition scoring

5. **Export Integration:**
   - Auto-exclude flagged photos from gallery
   - Quality-based photo ordering in slideshows

---

**Status:** ✅ **FULLY IMPLEMENTED AND TESTED**

All features are now available in the GUI. Start by selecting a project from the header dropdown, then navigate to the Projects tab to configure quality detection settings.
