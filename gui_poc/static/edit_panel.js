/**
 * Edit Panel Component for Lightbox
 * ==================================
 * 
 * Non-destructive image editing panel with:
 * - Live histogram
 * - Exposure, Contrast, Highlights, Shadows sliders
 * - Real-time preview
 * - Auto-save to JSON metadata
 * 
 * Usage in app.js:
 *   Import this file and add EditPanelMixin to your Vue app
 */

const EditPanelMixin = {
    data() {
        return {
            // Edit panel state
            showEditPanel: false,
            editPanelLoading: false,
            
            // Current edits for active photo
            currentEdits: {
                exposure: 0,
                contrast: 0,
                highlights: 0,
                shadows: 0,
                whites: 0,
                blacks: 0
            },
            
            // Histogram data
            histogram: null,
            histogramMode: 'luminance', // 'luminance' or 'rgb'
            
            // Preview state
            previewLoading: false,
            previewDebounceTimer: null,
            
            // Has unsaved changes
            hasUnsavedEdits: false
        };
    },
    
    computed: {
        // Check if any edits are non-zero
        hasActiveEdits() {
            return Object.values(this.currentEdits).some(v => v !== 0);
        },
        
        // Format edit values for display
        formattedEdits() {
            return {
                exposure: this.currentEdits.exposure.toFixed(2),
                contrast: Math.round(this.currentEdits.contrast),
                highlights: Math.round(this.currentEdits.highlights),
                shadows: Math.round(this.currentEdits.shadows),
                whites: Math.round(this.currentEdits.whites),
                blacks: Math.round(this.currentEdits.blacks)
            };
        }
    },
    
    methods: {
        // ============================================================
        // Load/Save Edits
        // ============================================================
        
        async loadEditsForPhoto(photoPath) {
            if (!photoPath) return;
            
            this.editPanelLoading = true;
            
            try {
                const response = await fetch(`/api/photos/${encodeURIComponent(photoPath)}/edits`);
                const data = await response.json();
                
                if (data.success && data.edits) {
                    // Load edits (use defaults if not set)
                    this.currentEdits = {
                        exposure: data.edits.exposure || 0,
                        contrast: data.edits.contrast || 0,
                        highlights: data.edits.highlights || 0,
                        shadows: data.edits.shadows || 0,
                        whites: data.edits.whites || 0,
                        blacks: data.edits.blacks || 0
                    };
                    
                    this.hasUnsavedEdits = false;
                } else {
                    // No edits, use defaults
                    this.resetEdits();
                }
            } catch (err) {
                console.error('Error loading edits:', err);
                this.resetEdits();
            } finally {
                this.editPanelLoading = false;
            }
        },
        
        async saveEdits(photoPath) {
            if (!photoPath) return false;
            
            try {
                const response = await fetch(`/api/photos/${encodeURIComponent(photoPath)}/edits`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.currentEdits)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.hasUnsavedEdits = false;
                    console.log('✅ Edits saved');
                    return true;
                } else {
                    console.error('❌ Failed to save edits:', data.error);
                    return false;
                }
            } catch (err) {
                console.error('❌ Error saving edits:', err);
                return false;
            }
        },
        
        async clearAllEdits(photoPath) {
            if (!photoPath) return false;
            
            if (!confirm('Reset all edits to defaults?')) {
                return false;
            }
            
            try {
                const response = await fetch(`/api/photos/${encodeURIComponent(photoPath)}/edits`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.resetEdits();
                    console.log('✅ Edits cleared');
                    return true;
                } else {
                    console.error('❌ Failed to clear edits:', data.error);
                    return false;
                }
            } catch (err) {
                console.error('❌ Error clearing edits:', err);
                return false;
            }
        },
        
        resetEdits() {
            this.currentEdits = {
                exposure: 0,
                contrast: 0,
                highlights: 0,
                shadows: 0,
                whites: 0,
                blacks: 0
            };
            this.hasUnsavedEdits = false;
        },
        
        // ============================================================
        // Histogram
        // ============================================================
        
        async loadHistogram(photoPath) {
            if (!photoPath) return;
            
            try {
                const response = await fetch(
                    `/api/photos/${encodeURIComponent(photoPath)}/histogram?mode=${this.histogramMode}&downsample=4`
                );
                const data = await response.json();
                
                if (data.success) {
                    this.histogram = data.histogram;
                } else {
                    console.error('Error loading histogram:', data.error);
                    this.histogram = null;
                }
            } catch (err) {
                console.error('Error loading histogram:', err);
                this.histogram = null;
            }
        },
        
        // ============================================================
        // Edit Handlers (with auto-save)
        // ============================================================
        
        onEditChange(photoPath) {
            this.hasUnsavedEdits = true;
            
            // Auto-save after 1 second of no changes
            clearTimeout(this.previewDebounceTimer);
            this.previewDebounceTimer = setTimeout(() => {
                this.saveEdits(photoPath);
            }, 1000);
        },
        
        // ============================================================
        // Canvas Rendering (for histogram display)
        // ============================================================
        
        drawHistogram(canvasId) {
            if (!this.histogram) return;
            
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const width = canvas.width;
            const height = canvas.height;
            
            // Clear canvas
            ctx.fillStyle = '#1a1a1a';
            ctx.fillRect(0, 0, width, height);
            
            if (this.histogram.mode === 'luminance') {
                // Draw luminance histogram
                const hist = this.histogram.histogram;
                const max = Math.max(...hist);
                
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                
                for (let i = 0; i < hist.length; i++) {
                    const x = (i / hist.length) * width;
                    const h = (hist[i] / max) * height;
                    const barWidth = width / hist.length;
                    
                    ctx.fillRect(x, height - h, barWidth, h);
                }
            } else if (this.histogram.mode === 'rgb') {
                // Draw RGB histogram (overlaid)
                const histR = this.histogram.histogram.r;
                const histG = this.histogram.histogram.g;
                const histB = this.histogram.histogram.b;
                const max = Math.max(...histR, ...histG, ...histB);
                
                // Draw each channel
                const drawChannel = (hist, color, alpha) => {
                    ctx.fillStyle = color;
                    ctx.globalAlpha = alpha;
                    
                    for (let i = 0; i < hist.length; i++) {
                        const x = (i / hist.length) * width;
                        const h = (hist[i] / max) * height;
                        const barWidth = width / hist.length;
                        
                        ctx.fillRect(x, height - h, barWidth, h);
                    }
                };
                
                drawChannel(histR, 'rgba(255, 50, 50, 0.5)', 0.5);
                drawChannel(histG, 'rgba(50, 255, 50, 0.5)', 0.5);
                drawChannel(histB, 'rgba(50, 50, 255, 0.5)', 0.5);
                
                ctx.globalAlpha = 1.0;
            }
        }
    }
};

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EditPanelMixin;
}
