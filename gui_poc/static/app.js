const { createApp } = Vue;
        
        createApp({
            data() {
                return {
                    currentView: 'projects',
                    photos: [],
                    videos: [],
                    audio: [],
                    bursts: [],
                    stats: null,
                    loading: true,
                    loadingBursts: false,
                    error: null,
                    burstError: null,
                    totalPhotos: 0,
                    mediaCount: 0,
                    offset: 0,
                    limit: 2500,
                    hoveredPhoto: null,
                    hoverStar: 0,
                    selectedBurst: null,
                    currentBurstPhotoIndex: 0,
                    activeBurstId: null,  // For filtering media tab to show only one burst
                    expandedBursts: new Set(),  // Track which bursts are expanded inline
                    burstDebugModal: null,  // Photo object for burst debug modal
                    showQuickRateMenu: false,  // Toggle for Quick Rate All dropdown
                    burstProgress: {
                        show: false,
                        step: '',
                        progress: 0,
                        total: 0,
                        message: ''
                    },
                    burstsFromCache: false,
                    // Blur Detection
                    blurDetectionRunning: false,
                    blurDetectionProgress: null,
                    blurScores: [],
                    blurHistogram: null,
                    blurThreshold: 100,  // Threshold value for blur detection
                    blurThresholdValue: 0,
                    blurThresholdEnabled: false,
                    applyingThreshold: false,
                    blurDetectionMethod: 'laplacian',  // Selected method
                    blurMethodInfo: {
                        laplacian: { name: 'Laplacian Variance', range: '0-300', desc: 'Fast, general purpose' },
                        tenengrad: { name: 'Tenengrad (Sobel)', range: '0-50', desc: 'Better for sky/homogeneous areas' },
                        roi: { name: 'ROI-based', range: '0-300', desc: 'Adaptive, focuses on interesting areas' }
                    },
                    // Keywords
                    allKeywords: [],
                    keywordInput: '',
                    showKeywordInput: null,
                    keywordSuggestions: [],
                    // Export
                    showExportModal: false,
                    exportTitle: '',
                    exportTemplate: 'photoswipe',
                    exportProfile: 'web',              // ðŸŽ¯ Export optimization profile
                    exportWebP: false,                 // ðŸš€ WebP generation
                    exportSlideshowEnabled: true,      // ðŸ†• Slideshow enabled by default
                    exportSlideshowDuration: 5,        // ðŸ†• 5 seconds per photo
                    exportSmartTVMode: false,          // ðŸ†• Smart TV mode
                    exportMusicFiles: '',              // ðŸ†• Music file paths (newline separated)
                    exporting: false,
                    exportProgress: {
                        show: false,
                        current: 0,
                        total: 0,
                        message: ''
                    },
                    // Projects
                    projects: [],
                    loadingProjects: false,
                    projectError: null,
                    showNewProjectModal: false,
                    newProjectName: '',
                    newProjectMode: 'filter',
                    savingProject: false,
                    currentProject: null,
                    currentProjectId: null,
                    // Quality detection settings
                    qualitySettings: {
                        blur_detection_enabled: true,
                        blur_threshold: 100.0,
                        blur_auto_flag_color: 'red',
                        burst_detection_enabled: true,
                        burst_time_threshold: 3,
                        burst_similarity_threshold: 0.95
                    },
                    blurDetectionStats: null,
                    burstStats: {
                        total: 0,
                        groups: 0
                    },
                    // Workspaces
                    workspaces: [],
                    currentWorkspace: null,
                    workspaceFolders: [],
                    loadingFolders: false,
                    showAddFolderModal: false,
                    showAddWorkspaceModal: false,
                    newFolderPath: '',
                    newWorkspaceName: '',
                    newWorkspacePath: '',
                    // Media Manager
                    mediaFolders: [],
                    loadingMedia: false,
                    mediaError: null,
                    showAddMediaFolderModal: false,
                    newMediaFolderPath: '',
                    newMediaFolderName: '',
                    newMediaFolderCategory: 'internal',
                    newMediaFolderNotes: '',
                    currentScanningFolder: null,
                    scanProgress: null,
                    showConfigModal: false,
                    configInfo: null,
                    // File Browser
                    showFileBrowser: false,
                    browserCurrentPath: '',
                    browserParentPath: null,
                    browserFolders: [],
                    browserIsRoot: false,
                    browserLoading: false,
                    browserCallback: null,
                    // Lightbox
                    showLightbox: false,
                    lightboxPhoto: null,
                    lightboxIndex: 0,
                    // Slideshow
                    showSlideshow: false,
                    slideshowPhotos: [],
                    slideshowIndex: 0,
                    slideshowInterval: null,
                    slideshowPlaying: false,
                    isFullscreen: false,
                    hideControls: false,
                    hideControlsTimeout: null,
                    slideshowSettings: {
                        duration: 5,      // seconds per photo
                        transition: 'fade',
                        loop: true
                    },
                    // Filtering & Sorting
                    filters: {
                        ratings: {
                            0: false,
                            1: false,
                            2: false,
                            3: false,
                            4: false,
                            5: false
                        },
                        colors: {
                            red: false,
                            yellow: false,
                            green: false,
                            blue: false,
                            purple: false,
                            none: false
                        },
                        keywords: [],  // Selected keywords to filter by
                        inBursts: false,
                        blurry: false,
                        sharp: false,
                        reviewBursts: false  // Show only regular photos + burst photos with burst_keep=true
                    },
                    colorFilterMode: 'include',  // 'include' or 'exclude'
                    sortBy: 'date', // name, date, rating, quality
                    sortOrder: 'asc' // asc, desc (asc = oldest first, chronological)
                }
            },
            computed: {
                currentBurstPhoto() {
                    if (!this.selectedBurst) return null;
                    return this.selectedBurst.photos[this.currentBurstPhotoIndex];
                },
                
                filteredPhotos() {
                    let filtered = [...this.photos];
                    
                    // === BURST FILTERING ===
                    // If viewing a specific burst, show only those photos
                    // If Review Bursts filter is active, show ALL photos (filter by burst_keep later)
                    // Otherwise, show only lead photos (collapse bursts into containers)
                    if (this.activeBurstId) {
                        // Show only photos from this burst
                        filtered = filtered.filter(p => p.burst_id === this.activeBurstId);
                    } else if (!this.filters.reviewBursts) {
                        // Normal mode: Show only lead photos (or photos not in bursts)
                        // Skip this if reviewBursts is active (we want to see ALL photos to filter by burst_keep)
                        filtered = filtered.filter(p => !p.burst_id || p.is_burst_lead);
                    }
                    
                    // Apply rating filters
                    const activeRatings = Object.keys(this.filters.ratings)
                        .filter(r => this.filters.ratings[r])
                        .map(r => parseInt(r));
                    
                    if (activeRatings.length > 0) {
                        filtered = filtered.filter(p => activeRatings.includes(p.rating || 0));
                    }
                    
                    // Apply color filters (with include/exclude mode)
                    const activeColors = Object.keys(this.filters.colors)
                        .filter(c => this.filters.colors[c]);
                    
                    if (activeColors.length > 0) {
                        filtered = filtered.filter(p => {
                            const photoColor = p.color || 'none';
                            const hasColor = activeColors.includes(photoColor);
                            
                            // Include mode: show only selected colors
                            // Exclude mode: hide selected colors
                            return this.colorFilterMode === 'include' ? hasColor : !hasColor;
                        });
                    }
                    
                    // Apply keyword filters
                    if (this.filters.keywords.length > 0) {
                        filtered = filtered.filter(p => {
                            const photoKeywords = p.keywords || [];
                            return this.filters.keywords.some(k => photoKeywords.includes(k));
                        });
                    }
                    
                    if (this.filters.inBursts) {
                        // Check if photo is in any burst
                        const burstPhotoIds = new Set();
                        this.bursts.forEach(burst => {
                            burst.photos.forEach(photo => {
                                burstPhotoIds.add(photo.id);
                            });
                        });
                        filtered = filtered.filter(p => burstPhotoIds.has(p.id));
                    }
                    
                    // Apply blur filters (based on threshold)
                    if (this.filters.blurry) {
                        filtered = filtered.filter(p => {
                            const score = this.getPhotoBlurScore(p);
                            return score !== null && score < this.blurThreshold;
                        });
                    }
                    
                    if (this.filters.sharp) {
                        filtered = filtered.filter(p => {
                            const score = this.getPhotoBlurScore(p);
                            return score !== null && score >= this.blurThreshold;
                        });
                    }
                    
                    // Apply Review Bursts filter
                    if (this.filters.reviewBursts) {
                        const beforeCount = filtered.length;
                        filtered = filtered.filter(p => {
                            // Keep all regular photos (not in burst)
                            if (!p.burst_id) return true;
                            
                            // For burst photos: keep only if burst_keep=true
                            const shouldKeep = p.burst_keep === true;
                            if (p.burst_id && shouldKeep) {
                                console.log(`âœ“ Keeping burst photo: ${p.name} (burst_keep: ${p.burst_keep})`);
                            }
                            return shouldKeep;
                        });
                        console.log(`ðŸ“¦ Review Bursts: ${beforeCount} â†’ ${filtered.length} photos (filtered out ${beforeCount - filtered.length} unkept burst photos)`);
                    }
                    
                    // Apply sorting
                    filtered.sort((a, b) => {
                        let result = 0;
                        
                        switch (this.sortBy) {
                            case 'name':
                                result = a.name.localeCompare(b.name);
                                break;
                            case 'rating':
                                result = (b.rating || 0) - (a.rating || 0);
                                break;
                            case 'date':
                                // Sort by capture_time (already sorted by backend, but re-sort if needed)
                                if (a.capture_time && b.capture_time) {
                                    result = a.capture_time.localeCompare(b.capture_time);
                                } else if (a.capture_time) {
                                    result = -1;
                                } else if (b.capture_time) {
                                    result = 1;
                                } else {
                                    result = a.name.localeCompare(b.name);
                                }
                                break;
                            case 'quality':
                                // Would need blur_score field
                                result = 0;
                                break;
                        }
                        
                        return this.sortOrder === 'desc' ? -result : result;
                    });
                    
                    return filtered;
                },
                
                activeFilterCount() {
                    let count = 0;
                    count += Object.values(this.filters.ratings).filter(v => v).length;
                    count += Object.values(this.filters.colors).filter(v => v).length;
                    count += this.filters.keywords.length;
                    if (this.filters.inBursts) count++;
                    if (this.filters.blurry) count++;
                    return count;
                },
                
                keywordSuggestionsFiltered() {
                    if (!this.keywordInput) return [];
                    const input = this.keywordInput.toLowerCase();
                    return this.allKeywords
                        .filter(k => k.name.toLowerCase().includes(input))
                        .slice(0, 10);
                },
                
                totalActivePhotos() {
                    return this.workspaceFolders
                        .filter(f => f.enabled)
                        .reduce((sum, f) => sum + (f.photo_count || 0), 0);
                },
                
                // Project-based computed properties
                enabledFolders() {
                    if (!this.currentProject || !this.currentProject.folders) return [];
                    return this.currentProject.folders.filter(f => f.enabled);
                },
                
                enabledFolderCount() {
                    return this.enabledFolders.length;
                },
                
                enabledMediaCount() {
                    return this.enabledFolders.reduce((sum, f) => {
                        return sum + (f.photo_count || 0) + (f.video_count || 0) + (f.audio_count || 0);
                    }, 0);
                }
            },
            methods: {
                async loadPhotos() {
                    try {
                        this.loading = true;
                        this.error = null;
                        
                        const res = await fetch(`/api/photos?limit=${this.limit}&offset=${this.offset}`);
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Check if there's a message (e.g., no folders enabled)
                        if (data.message && data.total === 0) {
                            this.error = data.message;
                            this.photos = [];
                            this.totalPhotos = 0;
                            return;
                        }
                        
                        this.photos.push(...data.photos);
                        this.totalPhotos = data.total;
                        this.offset += data.photos.length;
                        
                        // Update burst stats
                        this.updateBurstStats();
                        
                    } catch (err) {
                        this.error = err.message;
                        console.error('Error loading photos:', err);
                    } finally {
                        this.loading = false;
                    }
                },
                
                updateBurstStats() {
                    const burstPhotos = this.photos.filter(p => p.burst && p.burst.is_burst);
                    this.burstStats.total = burstPhotos.length;
                    // Group size estimation (approximate)
                    this.burstStats.groups = burstPhotos.length > 0 ? Math.ceil(burstPhotos.length / 3) : 0;
                },
                
                async loadBursts(force = false) {
                    try {
                        this.loadingBursts = true;
                        this.burstError = null;
                        this.burstProgress.show = true;
                        this.burstProgress.message = 'Starting analysis...';
                        
                        // Start progress monitoring if not from cache
                        if (force || this.bursts.length === 0) {
                            this.monitorBurstProgress();
                        }
                        
                        const url = force ? '/api/bursts?force=true' : '/api/bursts';
                        const res = await fetch(url);
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.bursts = data.bursts;
                        this.burstsFromCache = data.cached || false;
                        
                        if (data.cached) {
                            console.log('âœ“ Loaded from cache:', data.computed_at);
                        }
                        
                    } catch (err) {
                        this.burstError = err.message;
                        console.error('Error loading bursts:', err);
                    } finally {
                        this.loadingBursts = false;
                        this.burstProgress.show = false;
                    }
                },
                
                monitorBurstProgress() {
                    // Use EventSource for Server-Sent Events
                    const eventSource = new EventSource('/api/bursts/progress');
                    
                    eventSource.onmessage = (event) => {
                        const progress = JSON.parse(event.data);
                        
                        this.burstProgress.step = progress.step;
                        this.burstProgress.progress = progress.progress;
                        this.burstProgress.total = progress.total;
                        this.burstProgress.message = progress.message;
                        
                        console.log(`Progress: ${progress.message} (${progress.progress}/${progress.total})`);
                        
                        if (progress.status === 'complete' || progress.status === 'error') {
                            eventSource.close();
                        }
                    };
                    
                    eventSource.onerror = () => {
                        eventSource.close();
                    };
                },
                
                async runBlurDetection() {
                    if (this.blurDetectionRunning) return;
                    
                    try {
                        this.blurDetectionRunning = true;
                        this.blurDetectionProgress = {
                            status: 'running',
                            progress: 0,
                            total: 1,  // Start with 1 to show progress bar
                            message: 'Starting blur detection...',
                            current_file: 'Initializing...'
                        };
                        
                        // Start progress monitoring FIRST
                        this.monitorBlurProgress();
                        
                        // Small delay to ensure EventSource is connected
                        await new Promise(resolve => setTimeout(resolve, 100));
                        
                        // Trigger blur detection (calculates and stores scores only)
                        const res = await fetch('/api/quality/detect-blur', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                force: false,  // Don't recalculate if already exists
                                method: this.blurDetectionMethod  // Use selected method
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        console.log(`âœ“ Blur scores calculated: ${data.calculated} new, ${data.skipped} skipped`);
                        
                        // Load blur scores and histogram
                        await this.loadBlurScores();
                        
                        // Store statistics
                        this.blurDetectionStats = {
                            total_analyzed: data.total_analyzed,
                            calculated: data.calculated,
                            skipped: data.skipped
                        };
                        
                        // Enable threshold slider
                        this.blurThresholdEnabled = true;
                        
                        // Update progress to complete
                        this.blurDetectionProgress = {
                            status: 'complete',
                            progress: data.total_analyzed,
                            total: data.total_analyzed,
                            message: `Complete! Calculated ${data.calculated}, skipped ${data.skipped}.`,
                            current_file: ''
                        };
                        
                        alert(`âœ“ Blur scores calculated (${this.blurDetectionMethod.toUpperCase()})!\n\nNew: ${data.calculated}\nSkipped: ${data.skipped}\n\nNow go to Photos tab and adjust the threshold slider to flag blurry photos.`);
                        
                    } catch (err) {
                        console.error('Error running blur detection:', err);
                        this.blurDetectionProgress = {
                            status: 'error',
                            message: 'Error: ' + err.message,
                            progress: 0,
                            total: 1
                        };
                        alert(`Error: ${err.message}`);
                    } finally {
                        this.blurDetectionRunning = false;
                    }
                },
                
                async loadBlurScores() {
                    try {
                        const res = await fetch(`/api/quality/blur-scores?method=${this.blurDetectionMethod}`);
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.blurScores = data.scores || [];
                        this.blurHistogram = data.histogram || null;
                        
                        console.log(`âœ“ Loaded ${this.blurScores.length} blur scores (${this.blurDetectionMethod})`);
                        
                    } catch (err) {
                        console.error('Error loading blur scores:', err);
                    }
                },
                
                async onBlurMethodChange() {
                    // Reload blur scores when method changes
                    await this.loadBlurScores();
                    
                    // Adjust threshold based on method
                    if (this.blurDetectionMethod === 'tenengrad') {
                        // Tenengrad has lower range (0-50)
                        if (this.blurThresholdValue > 50) {
                            this.blurThresholdValue = 25;
                        }
                    }
                    
                    // Update stats immediately
                    this.updateBlurStats();
                    
                    console.log(`âœ“ Switched to ${this.blurDetectionMethod} method`);
                },
                
                async applyBlurThreshold() {
                    if (!this.blurThresholdEnabled || this.applyingThreshold) return;
                    
                    try {
                        this.applyingThreshold = true;
                        
                        const res = await fetch('/api/quality/apply-threshold', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                threshold: this.blurThresholdValue,
                                flag_color: this.qualitySettings.blur_auto_flag_color,
                                method: this.blurDetectionMethod
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        console.log(`âœ“ Threshold applied: ${data.flagged_count} total flagged, ${data.unflagged_count} unflagged, ${data.changed_count} changed`);
                        
                        // Update blur detection stats for header
                        this.blurDetectionStats = {
                            ...this.blurDetectionStats,
                            flagged_count: data.flagged_count
                        };
                        
                        // Reload photos to show updated flags
                        await this.loadProjectMedia();
                        
                        alert(`âœ“ Threshold ${this.blurThresholdValue} applied (${this.blurDetectionMethod.toUpperCase()})!\n\nTotal flagged (blur < ${this.blurThresholdValue}): ${data.flagged_count}\nUnflagged: ${data.unflagged_count}\nChanged: ${data.changed_count}`);
                        
                    } catch (err) {
                        console.error('Error applying threshold:', err);
                        alert(`Error: ${err.message}`);
                    } finally {
                        this.applyingThreshold = false;
                    }
                },
                
                shouldRangeBeBlurred(range) {
                    // Determine if a histogram range should be flagged based on threshold
                    if (!this.blurThresholdEnabled) return false;
                    
                    const threshold = this.blurThresholdValue;
                    
                    // Parse range (e.g., "0-50", "50-100", "200+")
                    if (range === '200+') {
                        return threshold > 200;
                    }
                    
                    const parts = range.split('-');
                    if (parts.length === 2) {
                        const max = parseInt(parts[1]);
                        return max <= threshold;
                    }
                    
                    return false;
                },
                
                getThresholdMax() {
                    // Return max threshold value based on method
                    if (this.blurDetectionMethod === 'tenengrad') {
                        return 50;  // Tenengrad has lower range
                    }
                    return 300;  // Laplacian and ROI
                },
                
                getThresholdStep() {
                    // Return step size based on method
                    if (this.blurDetectionMethod === 'tenengrad') {
                        return 1;  // Finer control for tenengrad
                    }
                    return 5;  // Coarser for larger ranges
                },
                
                async onProjectChange() {
                    if (!this.currentProjectId) {
                        this.currentProject = null;
                        this.photos = [];
                        this.videos = [];
                        this.audio = [];
                        return;
                    }
                    
                    // Use activateProject() to load the project
                    await this.activateProject(this.currentProjectId);
                    
                    // Auto-switch to media tab and load media
                    if (this.currentView !== 'projects') {
                        this.currentView = 'media';
                        await this.loadProjectMedia();
                    }
                },
                
                async saveQualitySettings() {
                    if (!this.currentProjectId) {
                        alert('Please select a project first');
                        return;
                    }
                    
                    try {
                        const res = await fetch(`/api/projects/${this.currentProjectId}/quality-settings`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                quality_settings: this.qualitySettings
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        alert('âœ“ Quality settings saved successfully!');
                        console.log('âœ“ Quality settings saved');
                        
                    } catch (err) {
                        console.error('Error saving quality settings:', err);
                        alert(`Failed to save settings: ${err.message}`);
                    }
                },
                
                monitorBlurProgress() {
                    const eventSource = new EventSource('/api/quality/blur-progress');
                    
                    eventSource.onmessage = (event) => {
                        const progress = JSON.parse(event.data);
                        this.blurDetectionProgress = progress;
                        
                        console.log(`Blur detection: ${progress.message} (${progress.progress}/${progress.total})`);
                        
                        if (progress.status === 'complete' || progress.status === 'error') {
                            eventSource.close();
                        }
                    };
                    
                    eventSource.onerror = () => {
                        eventSource.close();
                    };
                },
                
                async loadStats() {
                    try {
                        const res = await fetch('/api/stats');
                        this.stats = await res.json();
                    } catch (err) {
                        console.error('Error loading stats:', err);
                    }
                },
                
                async loadMore() {
                    await this.loadProjectMedia();
                },
                
                async switchToBursts() {
                    this.currentView = 'bursts';
                    if (this.bursts.length === 0) {
                        await this.loadBursts();
                    }
                },
                
                async switchToProjects() {
                    this.currentView = 'projects';
                    if (this.projects.length === 0) {
                        await this.loadProjects();
                    }
                },
                
                async switchToWorkspaces() {
                    this.currentView = 'workspaces';
                    await this.loadWorkspaces();
                    await this.loadWorkspaceFolders();
                },
                
                async switchToMedia() {
                    this.currentView = 'media';
                    await this.loadMediaFolders();
                },
                
                async loadMediaFolders() {
                    this.loadingMedia = true;
                    this.mediaError = null;
                    
                    try {
                        const res = await fetch('/api/media/folders');
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.mediaFolders = data.folders || [];
                        console.log(`âœ“ Loaded ${this.mediaFolders.length} media folders`);
                    } catch (err) {
                        this.mediaError = `Failed to load media folders: ${err.message}`;
                        console.error('Error loading media folders:', err);
                    } finally {
                        this.loadingMedia = false;
                    }
                },
                
                async addMediaFolder() {
                    if (!this.newMediaFolderPath.trim()) {
                        alert('Please enter a folder path');
                        return;
                    }
                    
                    try {
                        const res = await fetch('/api/media/folders', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                path: this.newMediaFolderPath,
                                name: this.newMediaFolderName || null,
                                category: this.newMediaFolderCategory,
                                notes: this.newMediaFolderNotes || null
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Reset form
                        this.newMediaFolderPath = '';
                        this.newMediaFolderName = '';
                        this.newMediaFolderCategory = 'internal';
                        this.newMediaFolderNotes = '';
                        this.showAddMediaFolderModal = false;
                        
                        // Reload
                        await this.loadMediaFolders();
                        
                        alert('âœ“ Media folder added successfully!');
                    } catch (err) {
                        alert(`Error: ${err.message}`);
                        console.error('Error adding media folder:', err);
                    }
                },
                
                async removeMediaFolder(folderPath) {
                    if (!confirm(`Remove media folder?\n\n${folderPath}\n\nThis will NOT delete any files, only remove from registry.`)) {
                        return;
                    }
                    
                    try {
                        const res = await fetch(`/api/media/folders/${encodeURIComponent(folderPath)}`, {
                            method: 'DELETE'
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        await this.loadMediaFolders();
                        console.log('âœ“ Media folder removed');
                    } catch (err) {
                        alert(`Error: ${err.message}`);
                        console.error('Error removing media folder:', err);
                    }
                },
                
                async showConfigInfo() {
                    try {
                        this.configInfo = null;
                        this.showConfigModal = true;
                        
                        const response = await fetch('/api/system/config-info');
                        if (!response.ok) {
                            throw new Error('Failed to load config info');
                        }
                        
                        this.configInfo = await response.json();
                    } catch (error) {
                        alert(`Error loading config: ${error.message}`);
                        this.showConfigModal = false;
                    }
                },
                
                async scanMediaFolder(folderPath) {
                    try {
                        this.currentScanningFolder = folderPath;
                        
                        // Initialize progress with proper structure
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
                        
                        // Start progress monitoring BEFORE triggering scan
                        this.monitorScanProgress(folderPath);
                        
                        // Small delay to let SSE connection establish
                        await new Promise(resolve => setTimeout(resolve, 100));
                        
                        // IMPORTANT: Always force=true for complete scan!
                        // Burst detection requires analyzing ALL photos together
                        const res = await fetch(`/api/media/folders/${encodeURIComponent(folderPath)}/scan`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                analyzers: ['blur', 'burst'],  // Enable both analyzers
                                force: true,  // ALWAYS force complete scan
                                threads: 4
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        console.log('âœ“ Scan started for', folderPath);
                    } catch (err) {
                        alert(`Error: ${err.message}`);
                        console.error('Error starting scan:', err);
                        this.currentScanningFolder = null;
                        this.scanProgress = null;
                    }
                },
                
                monitorScanProgress(folderPath) {
                    const eventSource = new EventSource(`/api/media/folders/${encodeURIComponent(folderPath)}/scan-progress`);
                    
                    eventSource.onmessage = (event) => {
                        const progress = JSON.parse(event.data);
                        this.scanProgress = progress;
                        
                        console.log(`Scan: ${progress.current_file} (${progress.completed}/${progress.total})`);
                        
                        if (progress.status === 'complete') {
                            eventSource.close();
                            this.currentScanningFolder = null;
                            this.loadMediaFolders();  // Reload to show updated status
                            alert(`âœ“ Scan complete!\n\nAnalyzed ${progress.completed} photos`);
                        } else if (progress.status === 'error') {
                            eventSource.close();
                            this.currentScanningFolder = null;
                            alert(`Error during scan: ${progress.message}`);
                        }
                    };
                    
                    eventSource.onerror = () => {
                        eventSource.close();
                        this.currentScanningFolder = null;
                    };
                },
                
                async checkJsonMetadata(folderPath) {
                    try {
                        const res = await fetch(`/api/media/folders/${encodeURIComponent(folderPath)}/check-json`);
                        const data = await res.json();
                        
                        if (data.error) {
                            alert(`Error: ${data.error}`);
                            return;
                        }
                        
                        // Format report
                        let report = `JSON Sidecar Check: ${folderPath}\n\n`;
                        report += `Total JSON files: ${data.total}\n`;
                        report += `Photos with burst data: ${data.burst_count}\n`;
                        report += `Unique burst groups: ${data.burst_groups}\n\n`;
                        
                        if (data.samples && data.samples.length > 0) {
                            report += `Sample entries:\n`;
                            data.samples.forEach(sample => {
                                report += `\n📄 ${sample.filename}\n`;
                                report += `   burst_id: ${sample.burst_id || 'none'}\n`;
                                report += `   neighbors: ${sample.neighbor_count}\n`;
                            });
                        }
                        
                        alert(report);
                        console.log('JSON Check:', data);
                    } catch (err) {
                        alert(`Error checking JSON: ${err.message}`);
                        console.error('JSON check error:', err);
                    }
                },
                
                async checkDatabaseMetadata(folderPath) {
                    try {
                        const res = await fetch(`/api/media/folders/${encodeURIComponent(folderPath)}/check-db`);
                        const data = await res.json();
                        
                        if (data.error) {
                            alert(`Error: ${data.error}`);
                            return;
                        }
                        
                        // Format report
                        let report = `Database Check: ${folderPath}\n\n`;
                        report += `Total photos in DB: ${data.total}\n`;
                        report += `Photos with burst data: ${data.burst_count}\n`;
                        report += `Unique burst groups: ${data.burst_groups}\n\n`;
                        
                        if (data.samples && data.samples.length > 0) {
                            report += `Sample entries:\n`;
                            data.samples.forEach(sample => {
                                report += `\n🗄️ ${sample.filename}\n`;
                                report += `   burst_id: ${sample.burst_id || 'none'}\n`;
                                report += `   neighbors: ${sample.neighbor_count}\n`;
                            });
                        }
                        
                        alert(report);
                        console.log('DB Check:', data);
                    } catch (err) {
                        alert(`Error checking database: ${err.message}`);
                        console.error('DB check error:', err);
                    }
                },
                
                isFolderAvailable(folder) {
                    // Check if folder path exists (will be checked server-side)
                    // For now, just check offline flag
                    return folder.path && folder.path.length > 0;
                },
                
                isScanningFolder(folderPath) {
                    return this.currentScanningFolder === folderPath;
                },
                
                getCategoryColor(category) {
                    const colors = {
                        internal: 'rgba(74, 222, 128, 0.2)',
                        usb: 'rgba(251, 191, 36, 0.2)',
                        network: 'rgba(59, 130, 246, 0.2)',
                        cloud: 'rgba(168, 85, 247, 0.2)',
                        other: 'rgba(156, 163, 175, 0.2)'
                    };
                    return colors[category] || colors.other;
                },
                
                getCategoryIcon(category) {
                    const icons = {
                        internal: 'ðŸ’¾',
                        usb: 'ðŸ”Œ',
                        network: 'ðŸŒ',
                        cloud: 'â˜ï¸',
                        other: 'ðŸ“‚'
                    };
                    return icons[category] || icons.other;
                },
                
                formatDate(isoString) {
                    if (!isoString) return 'N/A';
                    const date = new Date(isoString);
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                },
                
                async resetAllRatings() {
                    if (!confirm(`Reset ALL star ratings for ${this.filteredPhotos.length} visible photos?\n\nThis cannot be undone!`)) {
                        return;
                    }
                    
                    try {
                        let updated = 0;
                        for (const photo of this.filteredPhotos) {
                            if (photo.rating > 0) {
                                await fetch(`/api/photos/${encodeURIComponent(photo.id)}/rating`, {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ rating: 0 })
                                });
                                photo.rating = 0;
                                updated++;
                            }
                        }
                        
                        await this.loadStats();
                        alert(`âœ“ Reset ${updated} star ratings`);
                    } catch (err) {
                        alert(`Error: ${err.message}`);
                        console.error('Error resetting ratings:', err);
                    }
                },
                
                async resetAllColors() {
                    if (!confirm(`Reset ALL color labels for ${this.filteredPhotos.length} visible photos?\n\nThis cannot be undone!`)) {
                        return;
                    }
                    
                    try {
                        let updated = 0;
                        for (const photo of this.filteredPhotos) {
                            if (photo.color) {
                                await this.setColor(photo, null);
                                updated++;
                            }
                        }
                        
                        alert(`âœ“ Reset ${updated} color labels`);
                    } catch (err) {
                        alert(`Error: ${err.message}`);
                        console.error('Error resetting colors:', err);
                    }
                },
                
                async loadWorkspaces() {
                    try {
                        const res = await fetch('/api/workspaces');
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.workspaces = data.workspaces || [];
                        this.currentWorkspace = data.current;
                    } catch (err) {
                        console.error('Error loading workspaces:', err);
                    }
                },
                
                async loadWorkspaceFolders() {
                    this.loadingFolders = true;
                    
                    try {
                        const res = await fetch('/api/workspace/folders');
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.workspaceFolders = data.folders || [];
                    } catch (err) {
                        console.error('Error loading folders:', err);
                    } finally {
                        this.loadingFolders = false;
                    }
                },
                
                async toggleFolder(folderPath, enabled) {
                    try {
                        const res = await fetch('/api/workspace/folders/toggle', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                path: folderPath,
                                enabled: enabled
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Update local state
                        const folder = this.workspaceFolders.find(f => f.path === folderPath);
                        if (folder) {
                            folder.enabled = enabled;
                        }
                        
                        // Always reset photo list so it reloads when user switches to photos tab
                        this.photos = [];
                        this.offset = 0;
                        
                        // Reload stats to update total count
                        await this.loadStats();
                        
                        // If currently on media tab with project, reload immediately
                        if (this.currentView === 'media' && this.currentProjectId) {
                            await this.loadProjectMedia();
                        }
                        
                    } catch (err) {
                        alert(`Failed to toggle folder: ${err.message}`);
                        console.error('Error toggling folder:', err);
                    }
                },
                
                async addFolder() {
                    if (!this.newFolderPath.trim()) {
                        alert('Please enter a folder path');
                        return;
                    }
                    
                    try {
                        const res = await fetch('/api/workspace/folders/add', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                path: this.newFolderPath
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.newFolderPath = '';
                        this.showAddFolderModal = false;
                        
                        // Reload folders
                        await this.loadWorkspaceFolders();
                        
                        // Reload stats to update total count
                        await this.loadStats();
                        
                        alert('âœ“ Folder added! Go to Projects tab to add it to a project.');
                        
                    } catch (err) {
                        alert(`Failed to add folder: ${err.message}`);
                        console.error('Error adding folder:', err);
                    }
                },
                
                async removeFolder(folderPath) {
                    if (!confirm(`Remove folder from workspace?\n\n${folderPath}\n\nThis will NOT delete any files, only remove from workspace configuration.`)) {
                        return;
                    }
                    
                    try {
                        const res = await fetch('/api/workspace/folders/remove', {
                            method: 'DELETE',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ path: folderPath })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Reload folders
                        await this.loadWorkspaceFolders();
                        
                        // Reset photo list
                        this.photos = [];
                        this.offset = 0;
                        
                        console.log('âœ“ Folder removed from workspace');
                    } catch (err) {
                        alert(`Error: ${err.message}`);
                        console.error('Error removing folder:', err);
                    }
                },
                
                confirmDeleteWorkspace(workspace) {
                    if (workspace.path === this.currentWorkspace) {
                        alert('Cannot delete the currently active workspace.\nPlease switch to another workspace first.');
                        return;
                    }
                    
                    const workspaceName = workspace.name || workspace.path;
                    
                    // First confirmation: Remove from registry?
                    if (!confirm(
                        `Remove Workspace "${workspaceName}"?\n\n` +
                        `Path: ${workspace.path}\n\n` +
                        `This will remove the workspace from the registry.\n` +
                        `Media files will NOT be deleted.\n\n` +
                        `Continue?`
                    )) {
                        return;
                    }
                    
                    // Second confirmation: Delete config.yaml?
                    const deleteConfig = confirm(
                        `Delete config.yaml file?\n\n` +
                        `File: ${workspace.path}/config.yaml\n\n` +
                        `This will permanently delete the workspace configuration.\n` +
                        `Media files will remain untouched.\n\n` +
                        `YES = Delete config.yaml\n` +
                        `NO = Keep config.yaml (only remove from registry)`
                    );
                    
                    this.deleteWorkspace(workspace.path, deleteConfig);
                },
                
                async deleteWorkspace(path, deleteConfig = false) {
                    try {
                        const res = await fetch(`/api/workspaces/${encodeURIComponent(path)}`, {
                            method: 'DELETE',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ delete_config: deleteConfig })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Reload workspaces
                        await this.loadWorkspaces();
                        
                        const msg = deleteConfig 
                            ? `âœ“ Workspace removed and config.yaml deleted`
                            : `âœ“ Workspace removed from registry (config.yaml kept)`;
                        
                        alert(msg);
                    } catch (err) {
                        alert(`Error: ${err.message}`);
                        console.error('Error deleting workspace:', err);
                    }
                },
                
                async switchToWorkspace(path) {
                    try {
                        const res = await fetch('/api/workspaces/switch', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ path: path })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.currentWorkspace = path;
                        
                        // Reload everything
                        await this.loadWorkspaceFolders();
                        await this.loadProjects();
                        await this.loadStats();
                        
                        // Clear current project when switching workspace
                        this.currentProjectId = null;
                        this.currentProject = null;
                        this.photos = [];
                        this.videos = [];
                        this.audio = [];
                        
                        alert(`âœ“ Switched to workspace. Select a project to load media.`);
                        
                    } catch (err) {
                        alert(`Failed to switch workspace: ${err.message}`);
                        console.error('Error switching workspace:', err);
                    }
                },
                
                async addWorkspace() {
                    if (!this.newWorkspaceName.trim() || !this.newWorkspacePath.trim()) {
                        alert('Please enter workspace name and path');
                        return;
                    }
                    
                    try {
                        // Create workspace path: parent_path/workspace_name
                        const parentPath = this.newWorkspacePath;
                        const workspaceName = this.newWorkspaceName.trim();
                        const fullWorkspacePath = parentPath.endsWith('/') || parentPath.endsWith('\\') 
                            ? parentPath + workspaceName 
                            : parentPath + '/' + workspaceName;
                        
                        const res = await fetch('/api/workspaces', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                path: fullWorkspacePath,
                                name: workspaceName
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        const newWorkspacePath = fullWorkspacePath;
                        
                        this.newWorkspaceName = '';
                        this.newWorkspacePath = '';
                        this.showAddWorkspaceModal = false;
                        
                        // Reload workspaces
                        await this.loadWorkspaces();
                        
                        // Switch to the new workspace
                        await this.switchToWorkspace(newWorkspacePath);
                        
                        alert('âœ“ Workspace created and activated!');
                    
                    } catch (err) {
                        alert(`Failed to add workspace: ${err.message}`);
                        console.error('Error adding workspace:', err);
                    }
                },
                
                // ===== FILE BROWSER =====
                
                openFileBrowser(callback) {
                    this.browserCallback = callback;
                    this.browserCurrentPath = '';
                    this.browserFolders = [];
                    this.browserIsRoot = false;
                    this.showFileBrowser = true;
                    this.browseFolders('');
                },
                
                async browseFolders(path) {
                    this.browserLoading = true;
                    try {
                        const res = await fetch(`/api/browse/folders?path=${encodeURIComponent(path || '')}`);
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.browserCurrentPath = data.current_path;
                        this.browserParentPath = data.parent;
                        this.browserFolders = data.folders || [];
                        this.browserIsRoot = data.is_root || false;
                        
                    } catch (err) {
                        alert(`Failed to browse: ${err.message}`);
                        console.error('Browse error:', err);
                    } finally {
                        this.browserLoading = false;
                    }
                },
                
                selectBrowserFolder(folderPath) {
                    if (this.browserCallback) {
                        this.browserCallback(folderPath);
                    }
                    this.closeBrowser();
                },
                
                selectCurrentBrowserPath() {
                    if (this.browserCurrentPath && this.browserCallback) {
                        this.browserCallback(this.browserCurrentPath);
                    }
                    this.closeBrowser();
                },
                
                closeBrowser() {
                    this.showFileBrowser = false;
                    this.browserCallback = null;
                },
                
                openFolderBrowserForAdd() {
                    this.openFileBrowser((path) => {
                        this.newFolderPath = path;
                    });
                },
                
                openFolderBrowserForWorkspace() {
                    this.openFileBrowser((path) => {
                        this.newWorkspacePath = path;
                    });
                },
                
                openFileBrowserForMediaFolder() {
                    this.openFileBrowser((path) => {
                        this.newMediaFolderPath = path;
                    });
                },
                
                // ===== END FILE BROWSER =====
                
                async switchToPhotosView() {
                    this.currentView = 'photos';
                    
                    // If photos list is empty (e.g., after toggling folders), reload
                    if (this.photos.length === 0) {
                        await Promise.all([
                            this.loadPhotos(),
                            this.loadStats()
                        ]);
                    }
                },
                
                async switchWorkspace() {
                    // Called when dropdown changes
                    if (this.currentWorkspace) {
                        await this.switchToWorkspace(this.currentWorkspace);
                    }
                },
                
                async loadProjects() {
                    this.loadingProjects = true;
                    this.projectError = null;
                    
                    try {
                        const res = await fetch('/api/projects');
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.projects = data.projects || [];
                    } catch (err) {
                        this.projectError = `Failed to load projects: ${err.message}`;
                        console.error('Error loading projects:', err);
                    } finally {
                        this.loadingProjects = false;
                    }
                },
                
                async saveNewProject() {
                    if (!this.newProjectName.trim()) {
                        alert('Please enter a project name');
                        return;
                    }
                    
                    this.savingProject = true;
                    
                    try {
                        // Collect current filters
                        const filters = {
                            ratings: Object.keys(this.filters.ratings).filter(r => this.filters.ratings[r]).map(Number),
                            colors: this.filters.colors.length > 0 ? this.filters.colors : null,
                            keywords: this.filters.keywords.length > 0 ? this.filters.keywords : null,
                            in_bursts: this.filters.inBursts || null
                        };
                        
                        // Get photo IDs if explicit mode
                        const photoIds = this.newProjectMode === 'explicit' ? 
                            this.filteredPhotos.map(p => p.id) : null;
                        
                        // Collect export settings
                        const exportSettings = {
                            slideshow_enabled: this.exportSlideshowEnabled,
                            slideshow_duration: this.exportSlideshowDuration,
                            smart_tv_mode: this.exportSmartTVMode,
                            template: this.exportTemplate,
                            music_files: this.exportMusicFiles.split('\n').map(f => f.trim()).filter(f => f)
                        };
                        
                        const res = await fetch('/api/projects', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name: this.newProjectName,
                                selection_mode: this.newProjectMode,
                                filters: this.newProjectMode !== 'explicit' ? filters : null,
                                photo_ids: photoIds,
                                export_settings: exportSettings
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Reset form
                        this.newProjectName = '';
                        this.newProjectMode = 'filter';
                        this.showNewProjectModal = false;
                        
                        // Reload projects
                        await this.loadProjects();
                        
                        alert(`âœ“ Project "${data.project.name}" saved successfully!`);
                        
                    } catch (err) {
                        alert(`Failed to save project: ${err.message}`);
                        console.error('Error saving project:', err);
                    } finally {
                        this.savingProject = false;
                    }
                },
                
                async loadProject(projectId) {
                    // Legacy method - redirect to new workflow
                    await this.activateProject(projectId);
                    
                    // Switch to media view and load media
                    this.currentView = 'media';
                    await this.loadProjectMedia();
                    
                    if (this.photos.length > 0) {
                        alert(`âœ“ Project "${this.currentProject.name}" loaded!\n\n${this.photos.length} photos loaded`);
                    }
                },
                
                async exportProject(projectId) {
                    try {
                        // Load project first
                        await this.loadProject(projectId);
                        
                        // Open export modal
                        this.openExportModal();
                        
                    } catch (err) {
                        alert(`Failed to export project: ${err.message}`);
                        console.error('Error exporting project:', err);
                    }
                },
                
                async editProject(projectId) {
                    alert('Edit project - coming soon!');
                    // TODO: Implement edit functionality
                },
                
                async confirmDeleteProject(projectId) {
                    const project = this.projects.find(p => p.id === projectId);
                    if (!project) return;
                    
                    if (!confirm(`Delete project "${project.name}"?\n\nThis cannot be undone.`)) {
                        return;
                    }
                    
                    try {
                        const res = await fetch(`/api/projects/${projectId}`, {
                            method: 'DELETE'
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Reload projects
                        await this.loadProjects();
                        
                        alert(`âœ“ Project "${project.name}" deleted`);
                        
                    } catch (err) {
                        alert(`Failed to delete project: ${err.message}`);
                        console.error('Error deleting project:', err);
                    }
                },
                
                // ===== NEW PROJECT-BASED MEDIA LOADING METHODS =====
                
                async activateProject(projectId) {
                    try {
                        // 1. Set as current project
                        this.currentProjectId = projectId;
                        
                        // 2. Load full project details
                        const res = await fetch(`/api/projects/${projectId}`);
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        this.currentProject = data.project;
                        
                        // 3. Load quality settings if available
                        if (data.project.quality_settings) {
                            Object.assign(this.qualitySettings, data.project.quality_settings);
                        }
                        
                        console.log(`âœ“ Project "${data.project.name}" activated`);
                        
                    } catch (err) {
                        console.error('Error activating project:', err);
                        alert(`Failed to activate project: ${err.message}`);
                    }
                },
                
                async loadProjectMedia() {
                    if (!this.currentProjectId) {
                        this.error = 'No project selected';
                        this.photos = [];
                        this.videos = [];
                        this.audio = [];
                        return;
                    }
                    
                    try {
                        this.loading = true;
                        this.error = null;
                        
                        const res = await fetch(`/api/projects/${this.currentProjectId}/media?limit=2500&type=all`);
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        if (data.message && data.total === 0) {
                            // No folders enabled
                            this.error = data.message;
                            this.photos = [];
                            this.videos = [];
                            this.audio = [];
                            this.mediaCount = 0;
                            return;
                        }
                        
                        // Separate by type
                        this.photos = (data.media || []).filter(m => m.type === 'photo');
                        this.videos = (data.media || []).filter(m => m.type === 'video');
                        this.audio = (data.media || []).filter(m => m.type === 'audio');
                        this.mediaCount = data.total || 0;
                        
                        console.log(`âœ“ Loaded ${this.photos.length} photos, ${this.videos.length} videos, ${this.audio.length} audio`);
                        
                        // DEBUG: Log burst data
                        const photosWithBurst = this.photos.filter(p => p.burst_id);
                        const burstLeads = this.photos.filter(p => p.is_burst_lead);
                        console.log(`ðŸ“¦ Burst Debug: ${photosWithBurst.length} photos in bursts, ${burstLeads.length} burst leaders`);
                        if (burstLeads.length > 0) {
                            console.log(`   Sample burst leader:`, burstLeads[0].name, {
                                burst_id: burstLeads[0].burst_id,
                                burst_count: burstLeads[0].burst_count,
                                is_burst_lead: burstLeads[0].is_burst_lead,
                                raw_data: burstLeads[0].burst_raw_data
                            });
                        }
                        
                        // Calculate stats from loaded photos
                        this.updateStatsFromPhotos();
                        
                        // Update blur stats
                        this.updateBlurStats();
                        
                        // Auto-load bursts if photos available
                        if (this.photos.length > 0) {
                            await this.loadProjectBursts();
                        }
                        
                    } catch (err) {
                        this.error = err.message;
                        console.error('Error loading project media:', err);
                    } finally {
                        this.loading = false;
                    }
                },
                
                updateStatsFromPhotos() {
                    // Calculate stats from currently loaded photos
                    const total = this.photos.length;
                    const rated = this.photos.filter(p => p.rating > 0).length;
                    const unrated = total - rated;
                    
                    let totalRating = 0;
                    let ratingCount = 0;
                    this.photos.forEach(p => {
                        if (p.rating > 0) {
                            totalRating += p.rating;
                            ratingCount++;
                        }
                    });
                    
                    const avgRating = ratingCount > 0 ? totalRating / ratingCount : 0;
                    
                    this.stats = {
                        total_photos: total,
                        rated_photos: rated,
                        unrated_photos: unrated,
                        avg_rating: avgRating.toFixed(1)
                    };
                    
                    console.log(`âœ“ Stats updated: ${rated}/${total} rated, avg: ${avgRating.toFixed(1)}`);
                },
                
                async loadProjectBursts() {
                    if (!this.currentProjectId) return;
                    
                    try {
                        const res = await fetch(`/api/projects/${this.currentProjectId}/bursts`);
                        const data = await res.json();
                        
                        if (!data.error && data.bursts) {
                            this.bursts = data.bursts;
                            console.log(`âœ“ Loaded ${this.bursts.length} burst groups`);
                        }
                    } catch (err) {
                        console.error('Error loading project bursts:', err);
                    }
                },
                
                async saveProject() {
                    if (!this.currentProject) return;
                    
                    try {
                        this.savingProject = true;
                        
                        const res = await fetch(`/api/projects/${this.currentProject.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.currentProject)
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        console.log('âœ“ Project saved');
                        
                    } catch (err) {
                        alert(`Failed to save project: ${err.message}`);
                        console.error('Error saving project:', err);
                    } finally {
                        this.savingProject = false;
                    }
                },
                
                async saveProjectAndLoadMedia() {
                    await this.saveProject();
                    
                    // Don't switch view if already on media tab
                    if (this.currentView !== 'media') {
                        this.currentView = 'media';
                    }
                    
                    await this.loadProjectMedia();
                    
                    console.log('âœ“ Project saved and media loaded!');
                },
                
                async onFolderToggle() {
                    // Just update UI - changes will be saved when user clicks "Load Media"
                    // Update enabled folder count
                    const enabledCount = this.currentProject.folders.filter(f => f.enabled).length;
                    console.log(`âœ“ ${enabledCount} folder(s) enabled - click "Load Media" to apply`);
                },
                
                async saveProjectName() {
                    // Auto-save when project name is changed
                    if (this.currentProject) {
                        await this.saveProject();
                    }
                },
                
                getProjectMediaCount(project) {
                    if (!project.folders || project.folders.length === 0) {
                        return 0;
                    }
                    return project.folders
                        .filter(f => f.enabled)
                        .reduce((sum, f) => sum + (f.photo_count || 0) + (f.video_count || 0) + (f.audio_count || 0), 0);
                },
                
                // ===== END NEW METHODS =====
                
                formatDate(isoString) {
                    if (!isoString) return '';
                    const date = new Date(isoString);
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                },
                
                formatCaptureTime(timestamp) {
                    if (!timestamp) return '';
                    // Parse "YYYY-MM-DD HH:MM:SS" format
                    const parts = timestamp.split(' ');
                    if (parts.length === 2) {
                        const dateParts = parts[0].split('-');
                        const timeParts = parts[1].split(':');
                        return `${dateParts[2]}.${dateParts[1]}.${dateParts[0]} ${timeParts[0]}:${timeParts[1]}`;
                    }
                    return timestamp;
                },
                
                async rate(photo, rating) {
                    const oldRating = photo.rating;
                    photo.rating = rating;
                    
                    try {
                        // Build URL with project_id if in project context
                        let url = `/api/photos/${encodeURIComponent(photo.id)}/rate`;
                        if (this.currentProjectId) {
                            url += `?project_id=${this.currentProjectId}`;
                        }
                        
                        const res = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ rating })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Mark as project override if applicable
                        if (data.target === 'project') {
                            photo.has_project_override = true;
                            photo.rating_source = 'project';
                        }
                        
                        // Recalculate stats from photos
                        this.updateStatsFromPhotos();
                        
                    } catch (err) {
                        photo.rating = oldRating;
                        this.error = `Failed to rate photo: ${err.message}`;
                        console.error('Error rating photo:', err);
                    }
                },
                
                async rateBurstPhoto(photo, stars) {
                    await this.rate(photo, stars);
                },
                
                async rateAllFiltered(rating) {
                    // Rate all currently visible/filtered photos
                    if (!this.currentProjectId) {
                        alert('Bitte wÃ¤hle zuerst ein Projekt aus');
                        return;
                    }
                    
                    const photosToRate = [...this.filteredPhotos];
                    const count = photosToRate.length;
                    
                    const confirmMsg = rating === 0 
                        ? `âš ï¸ Alle ${count} sichtbaren Fotos auf 0 Sterne (DELETE) setzen?\n\nDies ist gut fÃ¼r den ersten Durchgang, um schlechte Fotos zu markieren.`
                        : `â­ Alle ${count} sichtbaren Fotos mit ${rating} Stern${rating > 1 ? 'en' : ''} bewerten?`;
                    
                    if (!confirm(confirmMsg)) {
                        return;
                    }
                    
                    console.log(`âš¡ Starting Quick Rate All: ${count} photos â†’ ${rating} stars`);
                    
                    let successCount = 0;
                    let errorCount = 0;
                    
                    // Rate photos in batches for better performance
                    for (let i = 0; i < photosToRate.length; i++) {
                        const photo = photosToRate[i];
                        
                        try {
                            await this.rate(photo, rating);
                            successCount++;
                            
                            // Show progress every 10 photos
                            if ((i + 1) % 10 === 0 || i === photosToRate.length - 1) {
                                console.log(`âš¡ Progress: ${i + 1}/${count} (${Math.round((i + 1) / count * 100)}%)`);
                            }
                        } catch (err) {
                            console.error(`Error rating ${photo.name}:`, err);
                            errorCount++;
                        }
                    }
                    
                    // Close menu
                    this.showQuickRateMenu = false;
                    
                    // Show result
                    const resultMsg = errorCount > 0
                        ? `âœ“ Rated ${successCount} photos with ${rating} star${rating !== 1 ? 's' : ''}\nâš ï¸ ${errorCount} errors`
                        : `âœ“ Alle ${successCount} Fotos erfolgreich mit ${rating} Stern${rating !== 1 ? 'en' : ''} bewertet!`;
                    
                    alert(resultMsg);
                    console.log(`âš¡ Quick Rate All completed: ${successCount} success, ${errorCount} errors`);
                },
                
                openBurstViewer(burst) {
                    this.selectedBurst = burst;
                    this.currentBurstPhotoIndex = 0;
                },
                
                nextBurstPhoto() {
                    if (this.currentBurstPhotoIndex < this.selectedBurst.count - 1) {
                        this.currentBurstPhotoIndex++;
                    }
                },
                
                prevBurstPhoto() {
                    if (this.currentBurstPhotoIndex > 0) {
                        this.currentBurstPhotoIndex--;
                    }
                },
                
                getBlurClass(score) {
                    if (!score) return '';
                    if (score >= 150) return 'good';
                    if (score >= 100) return 'warning';
                    return 'bad';
                },
                
                clearFilters() {
                    this.filters = {
                        ratings: {
                            0: false,
                            1: false,
                            2: false,
                            3: false,
                            4: false,
                            5: false
                        },
                        colors: {
                            red: false,
                            yellow: false,
                            green: false,
                            blue: false,
                            purple: false,
                            none: false
                        },
                        keywords: [],
                        inBursts: false,
                        blurry: false
                    };
                },
                
                async setColor(photo, color) {
                    const oldColor = photo.color;
                    photo.color = color;
                    
                    try {
                        // Build URL with project_id if in project context
                        let url = `/api/photos/${encodeURIComponent(photo.id)}/color`;
                        if (this.currentProjectId) {
                            url += `?project_id=${this.currentProjectId}`;
                        }
                        
                        const res = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ color })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Mark as project override if applicable
                        if (data.target === 'project') {
                            photo.has_project_override = true;
                            photo.color_source = 'project';
                        }
                        
                        console.log(`âœ“ Set color ${color} for ${photo.name} (${data.target})`);
                        
                    } catch (err) {
                        photo.color = oldColor;
                        this.error = `Failed to set color: ${err.message}`;
                        console.error('Error setting color:', err);
                    }
                },
                
                handleImageError(event, photo) {
                    console.warn(`Failed to load thumbnail for ${photo.name}`);
                    event.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%23333" width="100" height="100"/><text x="50" y="50" text-anchor="middle" dy=".3em" fill="%23666" font-size="40">ðŸ“·</text></svg>';
                },
                
                getColorHex(color) {
                    const colors = {
                        red: '#ef4444',
                        yellow: '#fbbf24',
                        green: '#4ade80',
                        blue: '#3b82f6',
                        purple: '#a855f7'
                    };
                    return colors[color] || '#888';
                },
                
                getPhotoBlurScore(photo) {
                    // Get blur score for currently selected method
                    if (!photo.blur_scores) return null;
                    return photo.blur_scores[this.blurDetectionMethod];
                },
                
                getBlurScoreTooltip(photo) {
                    if (!photo.blur_scores) return '';
                    
                    const currentScore = photo.blur_scores[this.blurDetectionMethod];
                    const tooltip = [`${this.blurDetectionMethod.toUpperCase()}: ${currentScore ? Math.round(currentScore) : 'N/A'} - ${this.getBlurScoreLabel(currentScore || 0)}`];
                    
                    // Show all available scores
                    if (photo.blur_scores.laplacian && this.blurDetectionMethod !== 'laplacian') {
                        tooltip.push(`LAP: ${Math.round(photo.blur_scores.laplacian)}`);
                    }
                    if (photo.blur_scores.tenengrad && this.blurDetectionMethod !== 'tenengrad') {
                        tooltip.push(`TEN: ${Math.round(photo.blur_scores.tenengrad)}`);
                    }
                    if (photo.blur_scores.roi && this.blurDetectionMethod !== 'roi') {
                        tooltip.push(`ROI: ${Math.round(photo.blur_scores.roi)}`);
                    }
                    
                    return tooltip.join(' | ');
                },
                
                getBlurScoreColor(score) {
                    // Return color based on blur score and threshold
                    if (score < this.blurThreshold) {
                        return '#ef4444';  // Red - Below threshold (blurry!)
                    }
                    if (score < this.blurThreshold + 50) return '#fb923c';     // Orange - Close to threshold
                    if (score < 150) return '#fbbf24';     // Yellow - Acceptable
                    if (score < 200) return '#4ade80';     // Green - Sharp
                    return '#22c55e';                       // Bright Green - Very Sharp
                },
                
                getBlurScoreLabel(score) {
                    // Return label based on blur score
                    if (score < 50) return 'Very Blurry';
                    if (score < 100) return 'Blurry';
                    if (score < 150) return 'Acceptable';
                    if (score < 200) return 'Sharp';
                    return 'Very Sharp';
                },
                
                updateBlurStats() {
                    // Update blur stats locally based on current threshold
                    // No backend call - just recalculate from loaded photos
                    if (!this.photos || this.photos.length === 0) {
                        this.blurDetectionStats = null;
                        return;
                    }
                    
                    let flagged = 0;
                    let sharp = 0;
                    
                    this.photos.forEach(photo => {
                        const score = this.getPhotoBlurScore(photo);
                        if (score !== null) {
                            if (score < this.blurThreshold) {
                                flagged++;
                            } else {
                                sharp++;
                            }
                        }
                    });
                    
                    this.blurDetectionStats = {
                        flagged_count: flagged,
                        sharp_count: sharp,
                        total: flagged + sharp,
                        threshold: this.blurThreshold,
                        method: this.blurDetectionMethod
                    };
                },
                
                async loadKeywords() {
                    try {
                        const res = await fetch('/api/keywords');
                        const data = await res.json();
                        this.allKeywords = data.keywords || [];
                    } catch (err) {
                        console.error('Error loading keywords:', err);
                    }
                },
                
                async addKeyword(photo, keyword) {
                    if (!keyword || !keyword.trim()) return;
                    
                    keyword = keyword.trim().toLowerCase();
                    
                    if (photo.keywords && photo.keywords.includes(keyword)) {
                        return;
                    }
                    
                    try {
                        // Build URL with project_id if in project context
                        let url = `/api/photos/${encodeURIComponent(photo.id)}/keywords`;
                        if (this.currentProjectId) {
                            url += `?project_id=${this.currentProjectId}`;
                        }
                        
                        const res = await fetch(url, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ add: keyword })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        photo.keywords = data.keywords;
                        this.keywordInput = '';
                        this.showKeywordInput = null;
                        
                        await this.loadKeywords();
                        
                    } catch (err) {
                        this.error = `Failed to add keyword: ${err.message}`;
                        console.error('Error adding keyword:', err);
                    }
                },
                
                async removeKeyword(photo, keyword) {
                    try {
                        // Build URL with project_id if in project context
                        let url = `/api/photos/${encodeURIComponent(photo.id)}/keywords`;
                        if (this.currentProjectId) {
                            url += `?project_id=${this.currentProjectId}`;
                        }
                        
                        const res = await fetch(url, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ remove: keyword })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        photo.keywords = data.keywords;
                        
                        await this.loadKeywords();
                        
                    } catch (err) {
                        this.error = `Failed to remove keyword: ${err.message}`;
                        console.error('Error removing keyword:', err);
                    }
                },
                
                toggleKeywordFilter(keyword) {
                    const index = this.filters.keywords.indexOf(keyword);
                    if (index > -1) {
                        this.filters.keywords.splice(index, 1);
                    } else {
                        this.filters.keywords.push(keyword);
                    }
                },
                
                openExportModal() {
                    if (this.filteredPhotos.length === 0) {
                        alert('No photos to export! Apply some filters first.');
                        return;
                    }
                    
                    this.showExportModal = true;
                    this.exportTitle = `Photo Gallery - ${new Date().toISOString().split('T')[0]}`;
                },
                
                updateProfileInfo() {
                    // Auto-enable WebP for web_optimized profile
                    if (this.exportProfile === 'web_optimized') {
                        this.exportWebP = true;
                    }
                },
                
                async exportGallery() {
                    if (!this.exportTitle.trim()) {
                        alert('Please enter a gallery title');
                        return;
                    }
                    
                    this.exporting = true;
                    this.exportProgress.show = true;
                    this.exportProgress.total = this.filteredPhotos.length;
                    this.exportProgress.current = 0;
                    
                    // Monitor progress
                    this.monitorExportProgress();
                    
                    try {
                        const photoIds = this.filteredPhotos.map(p => p.id);
                        const outputName = this.exportTitle
                            .toLowerCase()
                            .replace(/[^a-z0-9]+/g, '-')
                            .replace(/^-|-$/g, '');
                        
                        // Parse music files (newline separated)
                        const musicFiles = this.exportMusicFiles
                            .split('\n')
                            .map(f => f.trim())
                            .filter(f => f.length > 0);
                        
                        const res = await fetch('/api/export/gallery', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                photo_ids: photoIds,
                                title: this.exportTitle,
                                output_name: outputName,
                                template: this.exportTemplate,
                                profile: this.exportProfile,           // ðŸŽ¯ Export profile
                                generate_webp: this.exportWebP,        // ðŸš€ WebP generation
                                // ðŸ†• NEW PARAMETERS
                                slideshow_enabled: this.exportSlideshowEnabled,
                                slideshow_duration: this.exportSlideshowDuration,
                                smart_tv_mode: this.exportSmartTVMode,
                                music_files: musicFiles.length > 0 ? musicFiles : undefined
                            })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        let message = `âœ“ Gallery exported successfully!\n\n`;
                        message += `Photos: ${data.photo_count}\n`;
                        if (data.music_count > 0) {
                            message += `ðŸŽµ Music tracks: ${data.music_count}\n`;
                        }
                        if (this.exportSlideshowEnabled) {
                            message += `ðŸŽ¬ Slideshow: ${this.exportSlideshowDuration}s per photo\n`;
                        }
                        message += `\nLocation: ${data.gallery_path}\n\nOpen: ${data.index_html}`;
                        
                        alert(message);
                        
                        this.showExportModal = false;
                        
                    } catch (err) {
                        alert(`Failed to export gallery: ${err.message}`);
                        console.error('Export error:', err);
                    } finally {
                        this.exporting = false;
                        this.exportProgress.show = false;
                    }
                },
                
                monitorExportProgress() {
                    const eventSource = new EventSource('/api/export/progress');
                    
                    eventSource.onmessage = (event) => {
                        const progress = JSON.parse(event.data);
                        
                        this.exportProgress.current = progress.current;
                        this.exportProgress.total = progress.total;
                        this.exportProgress.message = progress.message;
                        
                        console.log(`Export: ${progress.message} (${progress.current}/${progress.total})`);
                        
                        if (progress.status === 'complete' || progress.status === 'error') {
                            eventSource.close();
                        }
                    };
                    
                    eventSource.onerror = () => {
                        eventSource.close();
                    };
                },
                
                openLightbox(photo, index) {
                    this.lightboxPhoto = photo;
                    this.lightboxIndex = index;
                    this.showLightbox = true;
                    document.addEventListener('keydown', this.handleLightboxKeyboard);
                },
                
                closeLightbox() {
                    this.showLightbox = false;
                    this.lightboxPhoto = null;
                    document.removeEventListener('keydown', this.handleLightboxKeyboard);
                },
                
                nextPhoto() {
                    if (this.lightboxIndex < this.filteredPhotos.length - 1) {
                        this.lightboxIndex++;
                        this.lightboxPhoto = this.filteredPhotos[this.lightboxIndex];
                    }
                },
                
                prevPhoto() {
                    if (this.lightboxIndex > 0) {
                        this.lightboxIndex--;
                        this.lightboxPhoto = this.filteredPhotos[this.lightboxIndex];
                    }
                },
                
                async rateLightboxPhoto(rating) {
                    await this.rate(this.lightboxPhoto, rating);
                },
                
                handleLightboxKeyboard(e) {
                    if (!this.showLightbox) return;
                    
                    switch(e.key) {
                        case 'Escape':
                            this.closeLightbox();
                            break;
                        case 'ArrowLeft':
                            this.prevPhoto();
                            break;
                        case 'ArrowRight':
                            this.nextPhoto();
                            break;
                        case '1':
                        case '2':
                        case '3':
                        case '4':
                        case '5':
                            this.rateLightboxPhoto(parseInt(e.key));
                            break;
                        case 'c':
                        case 'C':
                            // Cycle through colors
                            const colors = ['red', 'yellow', 'green', 'blue', 'purple', null];
                            const currentIndex = colors.indexOf(this.lightboxPhoto.color);
                            const nextColor = colors[(currentIndex + 1) % colors.length];
                            this.setColor(this.lightboxPhoto, nextColor);
                            break;
                        case '0':
                            // Clear rating
                            this.rateLightboxPhoto(0);
                            break;
                    }
                },
                
                // ========================================
                // SLIDESHOW METHODS
                // ========================================
                
                startSlideshow() {
                    if (this.filteredPhotos.length === 0) {
                        alert('No photos to show in slideshow!');
                        return;
                    }
                    
                    this.slideshowPhotos = [...this.filteredPhotos];
                    this.slideshowIndex = 0;
                    this.showSlideshow = true;
                    this.slideshowPlaying = false;
                    this.hideControls = false;
                    
                    // Auto-start playback
                    this.$nextTick(() => {
                        this.playSlideshowAuto();
                        
                        // Add fullscreen change listener
                        document.addEventListener('fullscreenchange', this.handleFullscreenChange);
                        
                        // Start auto-hide timer
                        this.startHideControlsTimer();
                    });
                    
                    // Add keyboard listener
                    document.addEventListener('keydown', this.handleSlideshowKeyboard);
                },
                
                exitSlideshow() {
                    // Exit fullscreen if active
                    if (document.fullscreenElement) {
                        document.exitFullscreen();
                    }
                    
                    this.stopSlideshow();
                    this.stopHideControlsTimer();
                    
                    this.showSlideshow = false;
                    this.slideshowPhotos = [];
                    this.isFullscreen = false;
                    this.hideControls = false;
                    
                    document.removeEventListener('keydown', this.handleSlideshowKeyboard);
                    document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
                },
                
                // === BURST VIEW METHODS ===
                viewBurst(burstId) {
                    // Activate burst filter to show only photos from this burst
                    this.activeBurstId = burstId;
                    
                    // Scroll to top for better UX
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    
                    console.log(`âœ“ Viewing burst: ${burstId}`);
                },
                
                exitBurstView() {
                    // Clear burst filter to show all photos again
                    this.activeBurstId = null;
                    
                    console.log('âœ“ Exited burst view');
                },
                
                // === BURST EXPANSION METHODS (Phase 2) ===
                toggleBurstExpansion(burstId) {
                    if (this.expandedBursts.has(burstId)) {
                        this.expandedBursts.delete(burstId);
                        console.log(`âœ“ Collapsed burst: ${burstId}`);
                    } else {
                        this.expandedBursts.add(burstId);
                        console.log(`âœ“ Expanded burst: ${burstId}`);
                    }
                    
                    // Force reactivity update for Set
                    this.expandedBursts = new Set(this.expandedBursts);
                },
                
                openBurstDebugModal(photo) {
                    // Open debug modal with full burst information
                    this.burstDebugModal = photo;
                    console.log('ðŸ”§ Opened burst debug modal for:', photo.name);
                },
                
                getBurstPhotos(burstId) {
                    // Get all photos belonging to this burst
                    const burstPhotos = this.photos.filter(p => p.burst_id === burstId);
                    
                    // Find the lead photo to check burst_count
                    const leadPhoto = burstPhotos.find(p => p.is_burst_lead);
                    
                    console.log(`ðŸ“¦ getBurstPhotos(${burstId}): Found ${burstPhotos.length} photos`);
                    if (leadPhoto && leadPhoto.burst_count !== burstPhotos.length) {
                        console.warn(`âš ï¸ BURST MISMATCH for ${burstId}:`);
                        console.warn(`   Lead photo: ${leadPhoto.name}`);
                        console.warn(`   burst_count: ${leadPhoto.burst_count}`);
                        console.warn(`   Actual photos found: ${burstPhotos.length}`);
                        console.warn(`   All photos in burst:`, burstPhotos.map(p => p.name));
                        if (leadPhoto.burst_raw_data && leadPhoto.burst_raw_data.burst_neighbors) {
                            console.warn(`   Neighbors in sidecar:`, leadPhoto.burst_raw_data.burst_neighbors.map(n => 
                                typeof n === 'string' ? n.split('\\').pop() : JSON.stringify(n)
                            ));
                        }
                    }
                    
                    return burstPhotos.sort((a, b) => {
                        // Sort by capture time or name
                        if (a.capture_time && b.capture_time) {
                            return a.capture_time.localeCompare(b.capture_time);
                        }
                        return a.name.localeCompare(b.name);
                    });
                },
                
                // === BURST KEEP METHODS ===
                async toggleBurstKeep(photo) {
                    if (!this.currentProjectId) {
                        alert('Please select a project first');
                        return;
                    }
                    
                    try {
                        const newKeepState = !photo.burst_keep;
                        
                        const res = await fetch(`/api/photos/${encodeURIComponent(photo.path)}/burst-keep?project_id=${this.currentProjectId}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ keep: newKeepState })
                        });
                        
                        const data = await res.json();
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        // Update local state
                        photo.burst_keep = newKeepState;
                        
                        console.log(`âœ“ Burst keep toggled for ${photo.name}: ${newKeepState}`);
                    } catch (err) {
                        console.error('Error toggling burst keep:', err);
                        alert(`Error: ${err.message}`);
                    }
                },
                
                async keepAllBurst(burstId) {
                    const burstPhotos = this.getBurstPhotos(burstId);
                    if (burstPhotos.length === 0) return;
                    
                    for (const photo of burstPhotos) {
                        if (!photo.burst_keep) {
                            await this.toggleBurstKeep(photo);
                        }
                    }
                    
                    console.log(`âœ“ Kept all ${burstPhotos.length} photos in burst`);
                },
                
                async unkeepalBurst(burstId) {
                    const burstPhotos = this.getBurstPhotos(burstId);
                    if (burstPhotos.length === 0) return;
                    
                    for (const photo of burstPhotos) {
                        if (photo.burst_keep) {
                            await this.toggleBurstKeep(photo);
                        }
                    }
                    
                    console.log(`âœ“ Unkept all ${burstPhotos.length} photos in burst`);
                },
                
                async markBurstBest(burstId) {
                    // Find the best photo in the burst (highest blur score)
                    const burstPhotos = this.getBurstPhotos(burstId);
                    if (burstPhotos.length === 0) return;
                    
                    // Sort by blur score (highest first)
                    const sortedByQuality = [...burstPhotos].sort((a, b) => {
                        const scoreA = this.getPhotoBlurScore(a) || 0;
                        const scoreB = this.getPhotoBlurScore(b) || 0;
                        return scoreB - scoreA;
                    });
                    
                    const bestPhoto = sortedByQuality[0];
                    
                    // Rate it 5 stars
                    await this.rate(bestPhoto, 5);
                    
                    console.log(`âœ“ Marked ${bestPhoto.name} as best (blur score: ${Math.round(this.getPhotoBlurScore(bestPhoto) || 0)})`);
                    alert(`âœ“ Marked ${bestPhoto.name} as BEST (â­â­â­â­â­)`);
                },
                
                async keepBurstBest(burstId) {
                    // Find best photo by blur score, keep ONLY that one, unkeep all others
                    const burstPhotos = this.getBurstPhotos(burstId);
                    if (burstPhotos.length === 0) return;
                    
                    // Find best by blur score
                    let bestPhoto = burstPhotos[0];
                    let bestScore = this.getPhotoBlurScore(bestPhoto) || 0;
                    
                    for (const photo of burstPhotos) {
                        const score = this.getPhotoBlurScore(photo) || 0;
                        if (score > bestScore) {
                            bestScore = score;
                            bestPhoto = photo;
                        }
                    }
                    
                    // Keep ONLY the best photo
                    for (const photo of burstPhotos) {
                        if (photo.id === bestPhoto.id) {
                            if (!photo.burst_keep) {
                                await this.toggleBurstKeep(photo);
                            }
                        } else {
                            if (photo.burst_keep) {
                                await this.toggleBurstKeep(photo);
                            }
                        }
                    }
                    
                    console.log(`âœ“ Kept ONLY best photo: ${bestPhoto.name} (blur score: ${Math.round(bestScore)})`);
                    alert(`âœ“ Kept ONLY: ${bestPhoto.name}\n(Blur score: ${Math.round(bestScore)})\n\n${burstPhotos.length - 1} other photos unkept`);
                },
                
                async deleteBurstRest(burstId) {
                    // This would require a backend endpoint to actually delete files
                    // For now, just mark them with red color for manual deletion
                    const burstPhotos = this.getBurstPhotos(burstId);
                    if (burstPhotos.length === 0) return;
                    
                    if (!confirm(`âš ï¸ Mark ${burstPhotos.length - 1} photos for deletion?\n\n(They will be tagged RED for manual deletion)`)) {
                        return;
                    }
                    
                    // Find best photo
                    let bestPhoto = burstPhotos[0];
                    let bestScore = this.getPhotoBlurScore(bestPhoto) || 0;
                    
                    for (const photo of burstPhotos) {
                        const score = this.getPhotoBlurScore(photo) || 0;
                        if (score > bestScore) {
                            bestScore = score;
                            bestPhoto = photo;
                        }
                    }
                    
                    // Mark others as red
                    for (const photo of burstPhotos) {
                        if (photo.id !== bestPhoto.id) {
                            await this.setColor(photo, 'red');
                        }
                    }
                    
                    console.log(`âœ“ Marked ${burstPhotos.length - 1} photos as RED for deletion`);
                    alert(`âœ“ ${burstPhotos.length - 1} photos marked RED for deletion\n\nFilter by RED color to review and delete them.`);
                },
                
                playSlideshowAuto() {
                    if (this.slideshowInterval) {
                        clearInterval(this.slideshowInterval);
                    }
                    
                    this.slideshowPlaying = true;
                    this.slideshowInterval = setInterval(() => {
                        this.nextSlide();
                    }, this.slideshowSettings.duration * 1000);
                },
                
                stopSlideshow() {
                    if (this.slideshowInterval) {
                        clearInterval(this.slideshowInterval);
                        this.slideshowInterval = null;
                    }
                    this.slideshowPlaying = false;
                },
                
                toggleSlideshowPlay() {
                    if (this.slideshowPlaying) {
                        this.stopSlideshow();
                    } else {
                        this.playSlideshowAuto();
                    }
                },
                
                nextSlide() {
                    if (this.slideshowIndex < this.slideshowPhotos.length - 1) {
                        this.slideshowIndex++;
                    } else if (this.slideshowSettings.loop) {
                        // Loop back to beginning
                        this.slideshowIndex = 0;
                    } else {
                        // End of slideshow, stop
                        this.stopSlideshow();
                    }
                },
                
                prevSlide() {
                    if (this.slideshowIndex > 0) {
                        this.slideshowIndex--;
                    } else if (this.slideshowSettings.loop) {
                        // Loop to end
                        this.slideshowIndex = this.slideshowPhotos.length - 1;
                    }
                },
                
                restartSlideshowIfPlaying() {
                    if (this.slideshowPlaying) {
                        this.stopSlideshow();
                        this.playSlideshowAuto();
                    }
                },
                
                toggleFullscreen() {
                    if (!document.fullscreenElement) {
                        // Enter fullscreen
                        const slideshowElement = document.querySelector('.slideshow');
                        if (slideshowElement) {
                            slideshowElement.requestFullscreen().catch(err => {
                                console.error('Error entering fullscreen:', err);
                                alert('Fullscreen not supported or denied');
                            });
                        }
                    } else {
                        // Exit fullscreen
                        document.exitFullscreen().catch(err => {
                            console.error('Error exiting fullscreen:', err);
                        });
                    }
                },
                
                handleFullscreenChange() {
                    this.isFullscreen = !!document.fullscreenElement;
                    
                    // If fullscreen was exited externally (ESC key), update state
                    if (!this.isFullscreen && !this.showSlideshow) {
                        // Slideshow was already closed
                        document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
                    }
                },
                
                // ========================================
                // AUTO-HIDE CONTROLS (YouTube-style)
                // ========================================
                
                startHideControlsTimer() {
                    // Clear any existing timer
                    this.stopHideControlsTimer();
                    
                    // Show controls initially
                    this.hideControls = false;
                    
                    // Hide after 3 seconds of inactivity
                    this.hideControlsTimeout = setTimeout(() => {
                        this.hideControls = true;
                    }, 3000);
                },
                
                stopHideControlsTimer() {
                    if (this.hideControlsTimeout) {
                        clearTimeout(this.hideControlsTimeout);
                        this.hideControlsTimeout = null;
                    }
                },
                
                showControlsTemporarily() {
                    // Show controls
                    this.hideControls = false;
                    
                    // Restart hide timer
                    this.startHideControlsTimer();
                },
                
                handleSlideshowKeyboard(e) {
                    if (!this.showSlideshow) return;
                    
                    // Show controls on any keyboard input
                    this.showControlsTemporarily();
                    
                    switch(e.key) {
                        case 'Escape':
                            // ESC exits fullscreen first, then slideshow
                            if (document.fullscreenElement) {
                                document.exitFullscreen();
                            } else {
                                this.exitSlideshow();
                            }
                            break;
                        case ' ':
                        case 'Space':
                            e.preventDefault();
                            this.toggleSlideshowPlay();
                            break;
                        case 'ArrowLeft':
                            this.prevSlide();
                            break;
                        case 'ArrowRight':
                            this.nextSlide();
                            break;
                        case 'ArrowUp':
                            // Increase speed
                            if (this.slideshowSettings.duration < 10) {
                                this.slideshowSettings.duration = Math.min(10, this.slideshowSettings.duration + 1);
                                this.restartSlideshowIfPlaying();
                            }
                            break;
                        case 'ArrowDown':
                            // Decrease speed
                            if (this.slideshowSettings.duration > 2) {
                                this.slideshowSettings.duration = Math.max(2, this.slideshowSettings.duration - 1);
                                this.restartSlideshowIfPlaying();
                            }
                            break;
                        case 'l':
                        case 'L':
                            // Toggle loop
                            this.slideshowSettings.loop = !this.slideshowSettings.loop;
                            break;
                        case 'f':
                        case 'F':
                            // Toggle fullscreen
                            e.preventDefault();
                            this.toggleFullscreen();
                            break;
                    }
                }
            },
            
            async mounted() {
                // Load workspace and project data (no media yet - requires project selection)
                await Promise.all([
                    this.loadWorkspaces(),
                    this.loadProjects(),
                    this.loadKeywords(),
                    this.loadMediaFolders(),      // Load media manager folders
                    this.loadWorkspaceFolders()    // Load workspace folders
                ]);
                
                // Note: Photos/media are loaded when a project is activated
                // Bursts are loaded automatically after media is loaded
                
                // Close Quick Rate menu when clicking outside
                document.addEventListener('click', () => {
                    this.showQuickRateMenu = false;
                });
            }
        }).mount('#app');
