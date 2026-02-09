/**
 * Image Canvas Processor for Live Preview
 * =========================================
 * 
 * Canvas-based image processing for real-time edit preview.
 * Applies exposure, contrast, highlights, shadows, whites, blacks.
 * 
 * Performance: ~50-100ms for 1000px images
 */

class ImageCanvasProcessor {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d', { willReadFrequently: true });
        this.originalImage = null;
        this.originalImageData = null;
        this.currentEdits = {
            exposure: 0,
            contrast: 0,
            highlights: 0,
            shadows: 0,
            whites: 0,
            blacks: 0
        };
        this.histogram = null;  // Cached histogram data
        this.performanceMs = 0;  // Last render time
    }

    /**
     * Load image from URL
     */
    async loadImage(imageUrl) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';  // For CORS
            
            img.onload = () => {
                this.originalImage = img;
                
                // AGGRESSIVE downsampling for performance!
                // Max 1200px on longest side for good performance
                const MAX_CANVAS_SIZE = 1200;
                
                let width = img.width;
                let height = img.height;
                
                // Scale to max 1200px on longest side
                const longestSide = Math.max(width, height);
                if (longestSide > MAX_CANVAS_SIZE) {
                    const scale = MAX_CANVAS_SIZE / longestSide;
                    width = Math.round(width * scale);
                    height = Math.round(height * scale);
                }
                
                // Also respect parent container
                const maxWidth = this.canvas.parentElement.clientWidth - 100;
                const maxHeight = this.canvas.parentElement.clientHeight - 100;
                
                if (width > maxWidth) {
                    height = Math.round((maxWidth / width) * height);
                    width = maxWidth;
                }
                if (height > maxHeight) {
                    width = Math.round((maxHeight / height) * width);
                    height = maxHeight;
                }
                
                this.canvas.width = width;
                this.canvas.height = height;
                
                // Draw original image
                this.ctx.drawImage(img, 0, 0, width, height);
                
                // Store original pixel data
                this.originalImageData = this.ctx.getImageData(0, 0, width, height);
                
                resolve();
            };
            
            img.onerror = (err) => {
                reject(new Error('Failed to load image'));
            };
            
            img.src = imageUrl;
        });
    }

    /**
     * Apply all edits and render to canvas
     */
    applyEdits(edits) {
        if (!this.originalImageData) return;
        
        const startTime = performance.now();
        
        this.currentEdits = { ...edits };
        
        // Clone original image data
        const imageData = new ImageData(
            new Uint8ClampedArray(this.originalImageData.data),
            this.originalImageData.width,
            this.originalImageData.height
        );
        
        const data = imageData.data;
        const len = data.length;
        
        // Apply edits in order (important for quality!)
        for (let i = 0; i < len; i += 4) {
            let r = data[i];
            let g = data[i + 1];
            let b = data[i + 2];
            
            // Calculate luminance for selective adjustments
            const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
            
            // 1. Exposure (global brightness)
            if (edits.exposure !== 0) {
                const multiplier = Math.pow(2, edits.exposure);
                r *= multiplier;
                g *= multiplier;
                b *= multiplier;
            }
            
            // 2. Contrast (global)
            if (edits.contrast !== 0) {
                const factor = (259 * (edits.contrast + 255)) / (255 * (259 - edits.contrast));
                r = factor * (r - 128) + 128;
                g = factor * (g - 128) + 128;
                b = factor * (b - 128) + 128;
            }
            
            // 3. Highlights (bright areas, luminance > 128)
            if (edits.highlights !== 0 && luminance > 128) {
                const mask = (luminance - 128) / 127;  // 0-1
                const adjustment = 1 + (edits.highlights / 100) * mask;
                r *= adjustment;
                g *= adjustment;
                b *= adjustment;
            }
            
            // 4. Shadows (dark areas, luminance < 128)
            if (edits.shadows !== 0 && luminance < 128) {
                const mask = (128 - luminance) / 128;  // 0-1
                const adjustment = 1 + (edits.shadows / 100) * mask;
                r *= adjustment;
                g *= adjustment;
                b *= adjustment;
            }
            
            // 5. Whites (very bright, luminance > 200)
            if (edits.whites !== 0 && luminance > 200) {
                const mask = (luminance - 200) / 55;  // 0-1
                const adjustment = 1 + (edits.whites / 100) * mask;
                r *= adjustment;
                g *= adjustment;
                b *= adjustment;
            }
            
            // 6. Blacks (very dark, luminance < 55)
            if (edits.blacks !== 0 && luminance < 55) {
                const mask = (55 - luminance) / 55;  // 0-1
                const adjustment = 1 + (edits.blacks / 100) * mask;
                r *= adjustment;
                g *= adjustment;
                b *= adjustment;
            }
            
            // Clamp values
            data[i] = Math.max(0, Math.min(255, r));
            data[i + 1] = Math.max(0, Math.min(255, g));
            data[i + 2] = Math.max(0, Math.min(255, b));
        }
        
        // Render to canvas
        this.ctx.putImageData(imageData, 0, 0);
        
        // Calculate histogram from processed image
        this.calculateHistogram(data);
        
        // Track performance
        this.performanceMs = Math.round(performance.now() - startTime);
    }

    /**
     * Reset to original image
     */
    reset() {
        if (this.originalImageData) {
            this.ctx.putImageData(this.originalImageData, 0, 0);
        }
    }

    /**
     * Calculate histogram from image data
     */
    calculateHistogram(pixelData) {
        const histogram = {
            luminance: new Array(256).fill(0),
            r: new Array(256).fill(0),
            g: new Array(256).fill(0),
            b: new Array(256).fill(0)
        };
        
        // Sample every 4th pixel for performance
        for (let i = 0; i < pixelData.length; i += 16) {  // Skip 4 pixels
            const r = pixelData[i];
            const g = pixelData[i + 1];
            const b = pixelData[i + 2];
            
            // Luminance
            const lum = Math.round(0.2126 * r + 0.7152 * g + 0.0722 * b);
            histogram.luminance[lum]++;
            
            // RGB channels
            histogram.r[r]++;
            histogram.g[g]++;
            histogram.b[b]++;
        }
        
        this.histogram = histogram;
    }

    /**
     * Get histogram data
     */
    getHistogram() {
        return this.histogram;
    }

    /**
     * Get last render performance
     */
    getPerformance() {
        return this.performanceMs;
    }

    /**
     * Get canvas as data URL
     */
    toDataURL(type = 'image/jpeg', quality = 0.95) {
        return this.canvas.toDataURL(type, quality);
    }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageCanvasProcessor;
}
