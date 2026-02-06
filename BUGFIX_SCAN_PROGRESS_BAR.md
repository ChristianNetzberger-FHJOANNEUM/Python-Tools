# Bugfix - Scan Progress Bar Not Visible

## Problem

User reported that when starting a scan in Media Manager:
- Text "Scanning in Progress..." was visible
- Windows hourglass (spinner) was visible
- **Progress bar was NOT visible**
- Only showed "Discovering photos..." text

## Root Cause

The progress bar had a condition `v-if="scanProgress && scanProgress.total > 0"` which meant:
- During initialization phase: `total = 0` → Progress bar hidden
- Only after photo discovery: `total > 0` → Progress bar appears
- User sees no visual feedback during the initial phase

## Solution

### 1. Restructured Progress Display

**Before:**
```html
<div v-if="scanProgress && scanProgress.total > 0">
    <!-- Progress bar only visible when total > 0 -->
</div>
<div v-else>
    Discovering photos...  <!-- Just text, no progress bar -->
</div>
```

**After:**
```html
<div v-if="scanProgress">
    <!-- Always show progress info when scanning -->
    
    <div v-if="scanProgress.total > 0">
        <!-- Determinate progress bar (with percentage) -->
    </div>
    
    <div v-else>
        <!-- Indeterminate progress bar (pulse animation) -->
    </div>
</div>
```

### 2. Added Indeterminate Progress Bar

For the initialization phase (when `total = 0`):
- Shows animated pulse effect
- Visual feedback that something is happening
- Text shows current file or "Discovering photos..."

**CSS Animation:**
```css
@keyframes pulse-scan {
    0% { left: -50%; }
    100% { left: 100%; }
}
```

**HTML:**
```html
<div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; position: relative;">
    <div style="position: absolute; height: 100%; width: 50%; background: linear-gradient(90deg, transparent, #f59e0b, #ef4444, transparent); animation: pulse-scan 1.5s ease-in-out infinite;">
    </div>
</div>
```

### 3. Enhanced Progress Initialization

**Before:**
```javascript
this.scanProgress = {
    status: 'running',
    total: 0,
    completed: 0,
    current_file: 'Starting...',
    current_analyzer: 'blur',
    photos_per_second: 0,
    estimated_remaining_seconds: 0
};
```

**After:**
```javascript
this.scanProgress = {
    status: 'running',
    total: 0,
    completed: 0,
    current_file: 'Initializing scan...',
    current_analyzer: '',
    photos_per_second: 0,
    estimated_remaining_seconds: 0,
    elapsed_seconds: 0,
    error_count: 0
};

// Start SSE monitoring BEFORE triggering scan
this.monitorScanProgress(folderPath);

// Small delay for SSE connection
await new Promise(resolve => setTimeout(resolve, 100));
```

## Visual Improvements

### Phase 1: Initialization (total = 0)
```
┌────────────────────────────────────────┐
│ ⏳ Scanning in Progress...             │
│                                        │
│ Discovering photos...                  │
│ ▓▓▓░░░░░░░░░░░  (pulse animation)      │
└────────────────────────────────────────┘
```

### Phase 2: Scanning (total > 0)
```
┌────────────────────────────────────────┐
│ ⏳ Scanning in Progress...             │
│                                        │
│ IMG_1234.jpg              450 / 2188   │
│ ███████████████░░░░░░░░░░  20%         │
│ blur             3.5 photos/sec  ETA: 500s│
└────────────────────────────────────────┘
```

## Files Modified

### `gui_poc/static/index.html`

**1. CSS - Added pulse animation:**
```css
@keyframes pulse-scan {
    0% { left: -50%; }
    100% { left: 100%; }
}
```

**2. HTML - Restructured progress display:**
- Removed outer condition requiring `total > 0`
- Added separate branches for determinate/indeterminate progress
- Added indeterminate progress bar with pulse animation

**3. JavaScript - Enhanced initialization:**
- More complete progress object structure
- SSE monitoring starts before scan trigger
- Small delay for connection establishment
- Better initial messages

## Testing

### Before Fix
1. Click "🔍 Scan" in Media Manager
2. See "Scanning in Progress..." text ✓
3. See spinner ✓
4. Progress bar visible? ❌
5. User confused, no visual feedback

### After Fix
1. Click "🔍 Scan" in Media Manager
2. See "Scanning in Progress..." text ✓
3. See spinner ✓
4. See pulse progress bar during init ✓
5. See actual progress bar with % ✓
6. Clear visual feedback throughout!

## User Experience

### Before
```
User clicks Scan
↓
"Scanning in Progress..." + spinner appears
↓
... nothing happens visually ...
↓
(User waits, wondering if it's frozen)
↓
Suddenly progress bar appears at 10%
```

### After
```
User clicks Scan
↓
"Scanning in Progress..." + spinner appears
↓
Pulse animation shows activity ✓
↓
"Discovering photos..." updates
↓
Smooth transition to percentage progress bar ✓
↓
User confident it's working!
```

## Technical Details

### SSE Connection Timing

**Issue:** SSE connection might not establish instantly
**Solution:** 100ms delay after starting EventSource

```javascript
// Start monitoring
this.monitorScanProgress(folderPath);

// Wait for connection
await new Promise(resolve => setTimeout(resolve, 100));

// Then trigger scan
const res = await fetch(...);
```

### Vue Reactivity

**Issue:** Vue needs proper initial structure for reactivity
**Solution:** Initialize all progress properties upfront

```javascript
this.scanProgress = {
    status: 'running',
    total: 0,              // ← Present from start
    completed: 0,          // ← Vue tracks this
    current_file: '...',   // ← Updates visible
    // ... all properties
};
```

### Progress Bar States

1. **Idle:** No scan running, no progress shown
2. **Initializing:** `total = 0`, indeterminate pulse bar
3. **Scanning:** `total > 0`, determinate progress bar with %
4. **Complete:** Scan finished, progress removed

## Related Issues

### Similar Pattern in Other Components

This same pattern might exist in:
- Blur detection progress (Projects tab)
- Burst detection progress
- Export progress

**Recommendation:** Audit all progress indicators and apply similar fix.

### Alternative Solutions Considered

1. **Show percentage as 0-100% during init**
   - Problem: Misleading, not really progress
   - Rejected

2. **Hide progress entirely during init**
   - Problem: No visual feedback (current issue)
   - Rejected

3. **Use spinner only, no bar**
   - Problem: Less informative
   - Rejected

4. **Show both spinner and pulse bar** ✓
   - Clear visual feedback
   - Smooth transition to real progress
   - **Selected solution**

## Performance Impact

- **CSS Animation:** Negligible, GPU-accelerated
- **DOM Updates:** Minimal, same elements reused
- **SSE Connection:** Already existed, just started earlier
- **100ms Delay:** Acceptable for better UX

## Summary

✅ **Fixed:** Progress bar now visible during entire scan
✅ **Added:** Indeterminate pulse animation for init phase
✅ **Enhanced:** Smoother progress tracking
✅ **Improved:** Better user feedback and confidence

The fix ensures users always see visual feedback when scanning, eliminating confusion about whether the scan is working or frozen.
