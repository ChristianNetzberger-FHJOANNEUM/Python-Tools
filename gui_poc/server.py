"""
Flask PoC Server for Photo Tool
Simple web interface to browse and rate photos
"""

from flask import Flask, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from pathlib import Path
import sys
import json
import time
import threading
from datetime import datetime

# Add parent directory to path to import photo_tool
sys.path.insert(0, str(Path(__file__).parent.parent))

from photo_tool.io import scan_multiple_directories, filter_by_type, get_capture_time
from photo_tool.config import load_config, save_config
from photo_tool.workspace import Workspace
from photo_tool.actions.rating import get_rating, get_rating_with_comment
from photo_tool.actions.metadata import (
    get_metadata, 
    set_color_label, 
    get_color_label,
    add_keyword,
    remove_keyword,
    set_keywords,
    get_all_keywords
)
from photo_tool.actions.export import export_gallery, _export_progress
from photo_tool.projects import ProjectManager, ProjectSidecarManager
from photo_tool.workspace.manager import (
    WorkspaceManager, 
    get_workspace_folders,
    toggle_folder,
    get_enabled_folders
)
from photo_tool.util.logging import get_logger

logger = get_logger("gui_server")

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for development

# Workspace manager (global)
workspace_manager = WorkspaceManager()

# Media manager (global)
from photo_tool.media import MediaManager
media_manager = MediaManager()

# Current workspace path (can be changed)
_current_workspace_path = Path("C:/PhotoTool_Test")

# Add current workspace if not already registered
if not any(ws['path'] == str(_current_workspace_path) for ws in workspace_manager.list_workspaces()):
    workspace_manager.add_workspace(_current_workspace_path, "Test Workspace")

def get_current_workspace():
    """Get current workspace path"""
    global _current_workspace_path
    current = workspace_manager.get_current_workspace()
    if current:
        _current_workspace_path = Path(current)
    return _current_workspace_path

# Project manager (initialized per workspace)
def get_project_manager():
    """Get project manager for current workspace"""
    return ProjectManager(get_current_workspace())

# Cache for burst analysis
_burst_cache = {
    'data': None,
    'config_mtime': None,
    'computed_at': None
}

# Progress tracking
_analysis_progress = {
    'status': 'idle',  # idle, running, complete, error
    'step': '',
    'progress': 0,
    'total': 0,
    'message': ''
}


@app.get('/')
def index():
    """Serve main HTML page"""
    return app.send_static_file('index.html')


@app.get('/api/photos')
def get_photos():
    """
    Get list of all photos with metadata
    Query params:
        - limit: Max number of photos (default: 100)
        - offset: Skip N photos (default: 0)
        - load_without_project: If true, load photos even without project (default: true for backward compatibility)
    """
    try:
        # Load workspace and config
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Get query params
        from flask import request
        load_without_project = request.args.get('load_without_project', 'true').lower() == 'true'
        
        # Check if we should load photos (project exists or load_without_project=true)
        if not load_without_project:
            # Check if any project exists
            pm = get_project_manager()
            projects = pm.list_projects()
            
            if not projects:
                # No projects exist - return empty list
                return jsonify({
                    'photos': [],
                    'total': 0,
                    'offset': 0,
                    'limit': 0,
                    'message': 'No projects created yet. Create a project to start working with photos.'
                })
        
        # Get only enabled folders
        enabled_folders = get_enabled_folders(workspace_path)
        if not enabled_folders:
            # No folders enabled - return empty list
            return jsonify({
                'photos': [],
                'total': 0,
                'offset': 0,
                'limit': 0,
                'message': 'No folders enabled in workspace. Add and enable media folders first.'
            })
        
        # Get query params
        from flask import request
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Scan for media (only enabled folders)
        all_media = scan_multiple_directories(
            enabled_folders,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        
        # Filter to photos only
        photos = filter_by_type(all_media, "photo")
        
        # Sort by capture time (newest first)
        from datetime import datetime
        
        # Build a list of (photo, capture_time) tuples for efficient sorting
        photos_with_times = []
        for photo in photos:
            try:
                capture_time = get_capture_time(photo.path, fallback_to_mtime=True)
                if capture_time is None:
                    # Fallback to file modification time
                    capture_time = datetime.fromtimestamp(photo.path.stat().st_mtime)
                photos_with_times.append((photo, capture_time))
            except Exception as e:
                # Ultimate fallback: use current time (will be sorted last)
                print(f"Warning: Could not get time for {photo.path.name}: {e}")
                photos_with_times.append((photo, datetime.now()))
        
        # Sort by capture time (newest first)
        photos_with_times.sort(key=lambda x: x[1], reverse=True)
        
        # Extract sorted photos
        photos = [p[0] for p in photos_with_times]

        
        # Paginate
        photos_page = photos[offset:offset + limit]
        
        # Build response
        result = []
        for photo in photos_page:
            # Try to get all metadata
            metadata = get_metadata(photo.path)
            
            # Find which root folder this photo belongs to and calculate relative path
            relative_path = None
            if enabled_folders:
                for root in enabled_folders:
                    try:
                        relative_path = str(photo.path.relative_to(root))
                        break
                    except ValueError:
                        continue
            
            # Fallback to absolute path if relative path couldn't be determined
            if relative_path is None:
                relative_path = str(photo.path)
            
            # Get capture time for display
            capture_time = get_capture_time(photo.path, fallback_to_mtime=True)
            capture_time_str = capture_time.strftime('%Y-%m-%d %H:%M:%S') if capture_time else None
            
            # Get blur scores for all methods
            blur_scores = {
                'laplacian': metadata.get('blur_score_laplacian'),
                'tenengrad': metadata.get('blur_score_tenengrad'),
                'roi': metadata.get('blur_score_roi')
            }
            
            # Get burst info from sidecar
            from photo_tool.prescan import SidecarManager
            burst_info = None
            try:
                sidecar = SidecarManager(photo.path)
                if sidecar.exists:
                    sidecar.load()
                    burst_data = sidecar.get('analyses.burst', {})
                    if burst_data and burst_data.get('is_burst_candidate'):
                        burst_info = {
                            'is_burst': True,
                            'group_size': burst_data.get('burst_group_size', 1),
                            'neighbor_count': len(burst_data.get('burst_neighbors', []))
                        }
            except:
                pass
            
            result.append({
                'id': str(photo.path),
                'name': photo.path.name,
                'path': relative_path,
                'size': photo.size_bytes,
                'rating': metadata.get('rating', 0),
                'color': metadata.get('color'),
                'comment': metadata.get('comment', ''),
                'keywords': metadata.get('keywords', []),
                'capture_time': capture_time_str,
                'blur_scores': blur_scores,  # All blur scores
                'blur_method': metadata.get('blur_method', 'laplacian'),  # Last used method
                'burst': burst_info,  # Burst information
                'thumbnail': f"/thumbnails/{photo.path.stem}.jpg",
                'full_image': f"/images/{photo.path.stem}{photo.path.suffix}"
            })
        
        return jsonify({
            'photos': result,
            'total': len(photos),
            'limit': limit,
            'offset': offset
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/photos/<path:photo_id>/rate')
def rate_photo(photo_id):
    """
    Rate a photo
    Body: { "rating": 1-5, "comment": "optional" }
    Query Params: { "project_id": "optional-project-id" }
    """
    try:
        from flask import request
        from photo_tool.actions.metadata import set_metadata
        
        data = request.get_json()
        rating = data.get('rating', 0)
        comment = data.get('comment', '')
        
        # Decode photo path
        photo_path = Path(photo_id)
        
        # Check if project context
        project_id = request.args.get('project_id')
        
        if project_id:
            # Save to PROJECT sidecar
            pm = get_project_manager()
            project_dir = pm.projects_dir / project_id
            psm = ProjectSidecarManager(project_dir)
            psm.set_rating(photo_path, rating)
            logger.info(f"Set project rating for {photo_path.name} in project {project_id}: {rating}")
        else:
            # Save to GLOBAL sidecar (legacy/fallback)
            set_metadata(photo_path, {
                'rating': rating,
                'comment': comment if comment else None
            })
            logger.info(f"Set global rating for {photo_path.name}: {rating}")
        
        return jsonify({
            'success': True,
            'rating': rating,
            'comment': comment,
            'target': 'project' if project_id else 'global'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/photos/<path:photo_id>/color')
def set_photo_color(photo_id):
    """
    Set color label for a photo
    Body: { "color": "red" | "yellow" | "green" | "blue" | "purple" | null }
    Query Params: { "project_id": "optional-project-id" }
    """
    try:
        from flask import request
        
        data = request.get_json()
        color = data.get('color')
        
        # Decode photo path
        photo_path = Path(photo_id)
        
        # Check if project context
        project_id = request.args.get('project_id')
        
        if project_id:
            # Save to PROJECT sidecar
            pm = get_project_manager()
            project_dir = pm.projects_dir / project_id
            psm = ProjectSidecarManager(project_dir)
            psm.set_color(photo_path, color)
            logger.info(f"Set project color for {photo_path.name} in project {project_id}: {color}")
        else:
            # Save to GLOBAL sidecar
            set_color_label(photo_path, color)
            logger.info(f"Set global color for {photo_path.name}: {color}")
        
        return jsonify({
            'success': True,
            'color': color,
            'target': 'project' if project_id else 'global'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/photos/<path:photo_id>/burst-keep')
def set_photo_burst_keep(photo_id):
    """
    Toggle burst_keep flag for a photo (project-specific only)
    Body: { "keep": true | false }
    Query Params: { "project_id": "required-project-id" }
    """
    try:
        from flask import request
        
        data = request.get_json()
        keep = data.get('keep', False)
        
        # Project ID is REQUIRED for burst_keep
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required for burst_keep'}), 400
        
        # Decode photo path
        photo_path = Path(photo_id)
        
        # Save to PROJECT sidecar
        pm = get_project_manager()
        project_dir = pm.projects_dir / project_id
        psm = ProjectSidecarManager(project_dir)
        
        # Get or create project sidecar
        sidecar_path = psm.sidecar_dir / f"{photo_path.stem}.sidecar"
        
        if sidecar_path.exists():
            with open(sidecar_path, 'r', encoding='utf-8') as f:
                sidecar_data = json.load(f)
        else:
            sidecar_data = {}
        
        # Set burst_keep flag
        sidecar_data['burst_keep'] = keep
        
        # Save
        with open(sidecar_path, 'w', encoding='utf-8') as f:
            json.dump(sidecar_data, f, indent=2)
        
        logger.info(f"Set burst_keep for {photo_path.name} in project {project_id}: {keep}")
        
        return jsonify({
            'success': True,
            'burst_keep': keep,
            'photo': str(photo_path)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/photos/<path:photo_id>/keywords')
def update_photo_keywords(photo_id):
    """
    Update keywords for a photo
    Body: { "keywords": ["tag1", "tag2"] } or { "add": "tag" } or { "remove": "tag" }
    Query Params: { "project_id": "optional-project-id" }
    """
    try:
        from flask import request
        
        data = request.get_json()
        photo_path = Path(photo_id)
        
        # Check if project context
        project_id = request.args.get('project_id')
        
        if project_id:
            # Use PROJECT sidecar manager
            pm = get_project_manager()
            project_dir = pm.projects_dir / project_id
            psm = ProjectSidecarManager(project_dir)
            
            if 'add' in data:
                psm.add_keyword(photo_path, data['add'])
                logger.info(f"Added project keyword '{data['add']}' to {photo_path.name}")
            elif 'remove' in data:
                psm.remove_keyword(photo_path, data['remove'])
                logger.info(f"Removed project keyword '{data['remove']}' from {photo_path.name}")
            
            # Get merged keywords
            global_meta = get_metadata(photo_path)
            merged_meta = psm.merge_metadata(global_meta, photo_path)
            
            return jsonify({
                'success': True,
                'keywords': merged_meta.get('keywords', []),
                'target': 'project'
            })
        else:
            # Use GLOBAL sidecar (legacy)
            if 'keywords' in data:
                set_keywords(photo_path, data['keywords'])
            elif 'add' in data:
                add_keyword(photo_path, data['add'])
            elif 'remove' in data:
                remove_keyword(photo_path, data['remove'])
            else:
                return jsonify({'error': 'Invalid request'}), 400
            
            metadata = get_metadata(photo_path)
            return jsonify({
                'success': True,
                'keywords': metadata.get('keywords', []),
                'target': 'global'
            })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/keywords')
def get_all_keywords_api():
    """
    Get all unique keywords across workspace with counts
    Query params:
        - min_count: Minimum number of photos (default: 1)
    """
    try:
        from flask import request
        
        workspace_path = Path("C:/PhotoTool_Test")
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        min_count = int(request.args.get('min_count', 1))
        
        # Scan all media
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        
        photos = filter_by_type(all_media, "photo")
        photo_paths = [p.path for p in photos]
        
        # Get all keywords
        keyword_counts = get_all_keywords(photo_paths)
        
        # Filter by min_count
        filtered = {k: v for k, v in keyword_counts.items() if v >= min_count}
        
        # Sort by count (descending)
        sorted_keywords = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
        
        return jsonify({
            'keywords': [{'name': k, 'count': v} for k, v in sorted_keywords],
            'total': len(sorted_keywords)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/export/gallery')
def export_gallery_api():
    """
    Export filtered photos as web gallery
    Body: {
        "photo_ids": ["path1", "path2"],
        "title": "Gallery Title",
        "output_name": "gallery-name",
        "template": "photoswipe" or "simple",
        "music_files": ["path/to/music1.mp3", "path/to/music2.mp3"],  // optional
        "slideshow_enabled": true,  // optional, default true
        "slideshow_duration": 5,  // optional, seconds per photo
        "smart_tv_mode": false  // optional, optimize for TV
    }
    """
    try:
        from flask import request
        import threading
        
        data = request.get_json()
        photo_ids = data.get('photo_ids', [])
        title = data.get('title', 'Photo Gallery')
        output_name = data.get('output_name', 'gallery')
        template = data.get('template', 'photoswipe')
        music_files = data.get('music_files', [])
        slideshow_enabled = data.get('slideshow_enabled', True)
        slideshow_duration = data.get('slideshow_duration', 5)
        smart_tv_mode = data.get('smart_tv_mode', False)
        
        if not photo_ids:
            return jsonify({'error': 'No photos selected'}), 400
        
        # Convert IDs to Path objects
        photo_paths = [Path(photo_id) for photo_id in photo_ids]
        music_paths = [Path(mf) for mf in music_files if Path(mf).exists()] if music_files else None
        
        # Export gallery in background thread
        workspace_path = Path("C:/PhotoTool_Test")
        output_dir = workspace_path / "exports" / output_name
        
        result = {'gallery_dir': None, 'error': None}
        
        def do_export():
            try:
                result['gallery_dir'] = export_gallery(
                    photo_paths=photo_paths,
                    output_dir=output_dir,
                    title=title,
                    template=template,
                    max_image_size=2000,
                    thumbnail_size=400,
                    include_metadata=True,
                    music_files=music_paths,
                    slideshow_enabled=slideshow_enabled,
                    slideshow_duration=slideshow_duration,
                    smart_tv_mode=smart_tv_mode
                )
            except Exception as e:
                result['error'] = str(e)
        
        # Start export in thread
        thread = threading.Thread(target=do_export)
        thread.start()
        thread.join()  # Wait for completion
        
        if result['error']:
            return jsonify({'error': result['error']}), 500
        
        gallery_dir = result['gallery_dir']
        
        return jsonify({
            'success': True,
            'gallery_path': str(gallery_dir),
            'index_html': str(gallery_dir / 'index.html'),
            'photo_count': len(photo_ids),
            'music_count': len(music_paths) if music_paths else 0
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/export/progress')
def get_export_progress():
    """Get export progress (SSE)"""
    def generate():
        from photo_tool.actions.export import _export_progress
        
        last_current = -1
        while True:
            current = _export_progress.copy()
            
            if current['current'] != last_current or current['status'] == 'complete':
                data = json.dumps(current)
                yield f"data: {data}\n\n"
                last_current = current['current']
            
            if current['status'] in ['complete', 'error', 'idle']:
                break
            
            time.sleep(0.3)
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.get('/thumbnails/<path:filename>')
def get_thumbnail(filename):
    """Serve thumbnail images"""
    try:
        workspace_path = get_current_workspace()
        thumb_dir = workspace_path / "cache" / "thumbnails"
        
        # Try to find thumbnail (case-insensitive)
        thumb_path = thumb_dir / filename
        if not thumb_path.exists():
            # Try with different extensions
            for ext in ['.jpg', '.jpeg', '.JPG', '.JPEG']:
                alt_path = thumb_dir / f"{thumb_path.stem}{ext}"
                if alt_path.exists():
                    thumb_path = alt_path
                    break
        
        if thumb_path.exists():
            return send_from_directory(thumb_dir, thumb_path.name)
        else:
            # FALLBACK: Generate thumbnail on-the-fly from original image
            # Get workspace folders
            ws = Workspace(workspace_path)
            config = load_config(ws.config_file)
            
            # Get all folders (both old and new structure)
            folders_to_search = []
            if config.folders:
                folders_to_search = [Path(f['path']) for f in config.folders]
            elif hasattr(config, 'scan') and hasattr(config.scan, 'roots'):
                folders_to_search = [Path(root) for root in config.scan.roots]
            
            # Search for original file in all folders (recursively)
            base_name = Path(filename).stem
            for folder in folders_to_search:
                if not folder.exists():
                    continue
                
                # Try different cases and extensions
                for ext in ['.JPG', '.jpg', '.JPEG', '.jpeg', '.PNG', '.png']:
                    # Search recursively for the file
                    for original in folder.rglob(f"{base_name}{ext}"):
                        if original.exists():
                            # Generate thumbnail on-the-fly using Pillow
                            from PIL import Image
                            from io import BytesIO
                            from flask import send_file
                            
                            img = Image.open(original)
                            
                            # Apply EXIF orientation
                            try:
                                exif = img.getexif()
                                if exif:
                                    orientation = exif.get(0x0112)  # Orientation tag
                                    if orientation:
                                        if orientation == 3:
                                            img = img.rotate(180, expand=True)
                                        elif orientation == 6:
                                            img = img.rotate(270, expand=True)
                                        elif orientation == 8:
                                            img = img.rotate(90, expand=True)
                            except:
                                pass
                            
                            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                            
                            # Convert to JPEG
                            if img.mode in ('RGBA', 'LA', 'P'):
                                img = img.convert('RGB')
                            
                            # Save to BytesIO
                            img_io = BytesIO()
                            img.save(img_io, 'JPEG', quality=85)
                            img_io.seek(0)
                            
                            return send_file(img_io, mimetype='image/jpeg')
            
            return jsonify({'error': 'Thumbnail not found'}), 404
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/images/<path:filename>')
def get_full_image(filename):
    """Serve full-size images for lightbox"""
    try:
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Get all folders (both old and new structure)
        folders_to_search = []
        if config.folders:
            folders_to_search = [Path(f['path']) for f in config.folders]
        elif hasattr(config, 'scan') and hasattr(config.scan, 'roots'):
            folders_to_search = [Path(root) for root in config.scan.roots]
        
        # Search in all folders recursively
        base_name = Path(filename).stem
        file_ext = Path(filename).suffix
        
        for root_path in folders_to_search:
            if not root_path.exists():
                continue
            # Try different cases and search recursively
            for ext in ['.JPG', '.jpg', '.JPEG', '.jpeg', '.PNG', '.png']:
                for image_path in root_path.rglob(f"{base_name}{ext}"):
                    if image_path.exists():
                        # Serve with optimized size (max 2500px)
                        from PIL import Image
                        from io import BytesIO
                        from flask import send_file
                        
                        img = Image.open(image_path)
                        
                        # Apply EXIF orientation (fix Samsung rotation issue)
                        try:
                            exif = img.getexif()
                            if exif:
                                orientation = exif.get(0x0112)  # Orientation tag
                                if orientation:
                                    if orientation == 3:
                                        img = img.rotate(180, expand=True)
                                    elif orientation == 6:
                                        img = img.rotate(270, expand=True)
                                    elif orientation == 8:
                                        img = img.rotate(90, expand=True)
                        except:
                            pass
                        
                        # Resize if too large
                        max_size = 2500
                        if img.width > max_size or img.height > max_size:
                            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        
                        # Convert to JPEG
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Save to BytesIO
                        img_io = BytesIO()
                        img.save(img_io, 'JPEG', quality=92)
                        img_io.seek(0)
                        
                        return send_file(img_io, mimetype='image/jpeg')
        
        return jsonify({'error': 'Image not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.get('/api/stats')
def get_stats():
    """Get workspace statistics"""
    try:
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Get only enabled folders
        enabled_folders = get_enabled_folders(workspace_path)
        if not enabled_folders:
            # Fallback to all folders if none enabled
            enabled_folders = config.scan.roots
        
        # Scan all media (only enabled folders)
        all_media = scan_multiple_directories(
            enabled_folders,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        
        photos = filter_by_type(all_media, "photo")
        videos = filter_by_type(all_media, "video")
        audio = filter_by_type(all_media, "audio")
        
        # Count rated photos
        rated = 0
        for photo in photos:
            rating = get_rating(photo.path)
            if rating and rating > 0:
                rated += 1
        
        return jsonify({
            'total_photos': len(photos),
            'total_videos': len(videos),
            'total_audio': len(audio),
            'rated_photos': rated,
            'unrated_photos': len(photos) - rated
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _compute_bursts_cached(workspace_path, force=False):
    """Compute bursts with caching"""
    global _burst_cache, _analysis_progress
    
    ws = Workspace(workspace_path)
    config_file = ws.config_file
    
    # Check if config changed
    config_mtime = config_file.stat().st_mtime if config_file.exists() else 0
    
    # Use cache if valid
    if not force and _burst_cache['data'] is not None and _burst_cache['config_mtime'] == config_mtime:
        print(f"Using cached burst data (computed at {_burst_cache['computed_at']})")
        return _burst_cache['data']
    
    print("Computing bursts (config changed or cache empty)...")
    
    # Update progress
    _analysis_progress['status'] = 'running'
    _analysis_progress['progress'] = 0
    _analysis_progress['message'] = 'Loading configuration...'
    
    try:
        config = load_config(config_file)
        
        # Import analysis functions
        from photo_tool.analysis import group_by_time, cluster_similar_photos
        from photo_tool.analysis.similarity import detect_blur, HashMethod
        from photo_tool.io import get_capture_time
        
        # Step 1: Scan photos
        _analysis_progress['step'] = 'scanning'
        _analysis_progress['message'] = 'Scanning photos...'
        
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        
        photos = filter_by_type(all_media, "photo")
        _analysis_progress['total'] = len(photos)
        _analysis_progress['progress'] = len(photos)
        
        if not photos:
            result = {'bursts': [], 'total': 0}
            _burst_cache['data'] = result
            _analysis_progress['status'] = 'complete'
            return result
        
        # Step 2: Get capture times
        _analysis_progress['step'] = 'metadata'
        _analysis_progress['message'] = f'Reading metadata ({len(photos)} photos)...'
        
        capture_times = []
        photo_paths = []
        
        for i, photo in enumerate(photos):
            capture_time = get_capture_time(photo.path)
            if capture_time:
                capture_times.append(capture_time)
                photo_paths.append(photo.path)
            if i % 50 == 0:
                _analysis_progress['progress'] = i
        
        # Step 3: Time grouping
        _analysis_progress['step'] = 'grouping'
        _analysis_progress['message'] = 'Grouping by time...'
        
        time_groups = group_by_time(
            photo_paths,
            capture_times,
            config.grouping.time_window_seconds,
            config.grouping.max_group_gap_seconds
        )
        
        # Step 4: Blur detection
        _analysis_progress['step'] = 'quality'
        _analysis_progress['message'] = 'Computing quality scores...'
        
        blur_scores = {}
        total_to_score = sum(len(g.photos) for g in time_groups)
        scored = 0
        
        for group in time_groups:
            for photo in group.photos:
                try:
                    blur_scores[photo] = detect_blur(photo)
                except:
                    pass
                scored += 1
                if scored % 10 == 0:
                    _analysis_progress['progress'] = scored
                    _analysis_progress['total'] = total_to_score
        
        # Step 5: Clustering
        _analysis_progress['step'] = 'clustering'
        _analysis_progress['message'] = 'Clustering similar photos...'
        
        hash_method = HashMethod(config.similarity.method)
        clusters = cluster_similar_photos(
            time_groups,
            hash_method=hash_method,
            similarity_threshold=config.similarity.phash_threshold,
            blur_scores=blur_scores,
            show_progress=False
        )
        
        # Step 6: Build response
        _analysis_progress['step'] = 'finalizing'
        _analysis_progress['message'] = f'Found {len(clusters)} burst groups...'
        
        bursts = []
        for i, cluster in enumerate(clusters):
            burst_photos = []
            for j, photo_path in enumerate(cluster.photos):
                rating = get_rating(photo_path)
                burst_photos.append({
                    'id': str(photo_path),
                    'name': photo_path.name,
                    'blur_score': cluster.blur_scores[j],
                    'is_best': j == cluster.best_photo_idx,
                    'rating': rating or 0,
                    'thumbnail': f"/thumbnails/{photo_path.stem}.jpg"
                })
            
            bursts.append({
                'id': f"burst_{i}",
                'name': cluster.photos[0].stem,
                'count': cluster.count,
                'best_photo_idx': cluster.best_photo_idx,
                'photos': burst_photos
            })
        
        result = {
            'bursts': bursts,
            'total': len(bursts),
            'cached': False,
            'computed_at': datetime.now().isoformat()
        }
        
        # Cache result
        _burst_cache['data'] = result
        _burst_cache['config_mtime'] = config_mtime
        _burst_cache['computed_at'] = datetime.now().isoformat()
        
        _analysis_progress['status'] = 'complete'
        _analysis_progress['progress'] = 100
        _analysis_progress['message'] = 'Complete!'
        
        print(f"Burst analysis complete: {len(bursts)} groups found")
        
        return result
        
    except Exception as e:
        _analysis_progress['status'] = 'error'
        _analysis_progress['message'] = str(e)
        raise


@app.get('/api/bursts')
def get_bursts():
    """
    Get burst photo groups (cached)
    Query params:
        - force: Force recompute (ignore cache)
    """
    try:
        from flask import request
        force = request.args.get('force', 'false').lower() == 'true'
        
        workspace_path = Path("C:/PhotoTool_Test")
        result = _compute_bursts_cached(workspace_path, force=force)
        
        # Add cache info
        result['cached'] = not force and _burst_cache['data'] is not None
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/bursts/progress')
def get_burst_progress():
    """Get current burst analysis progress (SSE)"""
    def generate():
        last_progress = -1
        while True:
            # Send progress update
            current = _analysis_progress.copy()
            
            # Only send if changed
            if current['progress'] != last_progress or current['status'] == 'complete':
                data = json.dumps(current)
                yield f"data: {data}\n\n"
                last_progress = current['progress']
            
            # Stop if complete or error
            if current['status'] in ['complete', 'error', 'idle']:
                break
            
            time.sleep(0.5)  # Update every 500ms
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.get('/api/bursts/<burst_id>')
def get_burst_detail(burst_id):
    """Get detailed information about a specific burst"""
    try:
        # For now, just redirect to /api/bursts and filter
        # (In production, we'd cache burst data)
        all_bursts_response = get_bursts()
        all_bursts = all_bursts_response.get_json()
        
        for burst in all_bursts['bursts']:
            if burst['id'] == burst_id:
                return jsonify(burst)
        
        return jsonify({'error': 'Burst not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# BLUR DETECTION ENDPOINTS
# =============================================================================

# Blur detection progress tracking
_blur_progress = {
    'status': 'idle',  # idle, running, complete, error
    'progress': 0,
    'total': 0,
    'current_file': '',
    'message': '',
    'flagged_count': 0
}

@app.post('/api/quality/detect-blur')
def detect_blur_photos():
    """
    Run blur detection on all photos - CALCULATES and STORES blur scores only
    Does NOT flag photos automatically. Use /api/quality/apply-threshold to flag.
    
    Body: {
        "force": false,  # Optional: force re-calculation even if scores exist
        "method": "laplacian"  # Optional: laplacian, tenengrad, or roi
    }
    """
    global _blur_progress
    
    try:
        from flask import request
        from photo_tool.analysis.similarity.blur import detect_blur, BlurMethod
        from photo_tool.actions.metadata import set_metadata, get_metadata
        
        data = request.get_json() or {}
        force = data.get('force', False)
        method_str = data.get('method', 'laplacian').lower()
        
        # Convert string to enum
        method_map = {
            'laplacian': BlurMethod.LAPLACIAN,
            'tenengrad': BlurMethod.TENENGRAD,
            'roi': BlurMethod.ROI,
            'variance': BlurMethod.VARIANCE
        }
        method = method_map.get(method_str, BlurMethod.LAPLACIAN)
        
        # Load workspace and current project
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Get enabled folders
        enabled_folders = get_enabled_folders(workspace_path)
        if not enabled_folders:
            enabled_folders = config.scan.roots
        
        # Get all photos
        all_media = scan_multiple_directories(
            enabled_folders,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        photos = filter_by_type(all_media, "photo")
        
        # Initialize progress
        _blur_progress = {
            'status': 'running',
            'progress': 0,
            'total': len(photos),
            'current_file': '',
            'message': 'Starting blur detection...',
            'flagged_count': 0
        }
        
        # Process photos - calculate and store scores
        results = []
        calculated_count = 0
        skipped_count = 0
        
        for i, photo in enumerate(photos):
            try:
                _blur_progress['current_file'] = photo.path.name
                _blur_progress['progress'] = i + 1
                _blur_progress['message'] = f'Analyzing {photo.path.name}...'
                
                # Check if blur score already exists for this method
                existing_meta = get_metadata(photo.path)
                score_key = f'blur_score_{method_str}'  # Method-specific key
                has_blur_score = score_key in existing_meta and existing_meta[score_key] is not None
                
                if has_blur_score and not force:
                    # Skip - already has score for this method
                    blur_score = existing_meta[score_key]
                    skipped_count += 1
                else:
                    # Calculate blur score with selected method
                    blur_score = detect_blur(photo.path, method=method)
                    
                    # Store in metadata with method-specific key
                    set_metadata(photo.path, {
                        score_key: float(blur_score),
                        'blur_method': method_str  # Store which method was used
                    })
                    calculated_count += 1
                
                results.append({
                    'path': str(photo.path),
                    'name': photo.path.name,
                    'blur_score': blur_score
                })
                
            except Exception as e:
                print(f"Error processing {photo.path.name}: {e}")
                results.append({
                    'path': str(photo.path),
                    'name': photo.path.name,
                    'error': str(e),
                    'blur_score': None
                })
        
        # Mark complete
        _blur_progress['status'] = 'complete'
        _blur_progress['message'] = f'Complete! Calculated {calculated_count}, skipped {skipped_count}.'
        _blur_progress['progress'] = len(photos)
        
        return jsonify({
            'success': True,
            'total_analyzed': len(photos),
            'calculated': calculated_count,
            'skipped': skipped_count,
            'method': method_str,
            'results': results
        })
    
    except Exception as e:
        _blur_progress['status'] = 'error'
        _blur_progress['message'] = str(e)
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/quality/blur-progress')
def get_blur_progress():
    """Get current blur detection progress (SSE)"""
    def generate():
        last_progress = -1
        while True:
            # Send progress update
            current = _blur_progress.copy()
            
            # Only send if changed
            if current['progress'] != last_progress or current['status'] in ['complete', 'error']:
                data = json.dumps(current)
                yield f"data: {data}\n\n"
                last_progress = current['progress']
            
            # Stop if complete or error
            if current['status'] in ['complete', 'error', 'idle']:
                break
            
            time.sleep(0.5)  # Update every 500ms
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.get('/api/quality/blur-scores')
def get_blur_scores():
    """
    Get blur scores for all photos in current workspace
    Query params:
        - method: laplacian, tenengrad, or roi (default: laplacian)
    Returns: {
        "scores": [{"path": "...", "blur_score": 123.45, "name": "..."}],
        "histogram": {"0-50": 10, "50-100": 20, ...}
    }
    """
    try:
        from flask import request
        from photo_tool.actions.metadata import get_metadata
        
        method = request.args.get('method', 'laplacian').lower()
        score_key = f'blur_score_{method}'
        
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Get enabled folders
        enabled_folders = get_enabled_folders(workspace_path)
        if not enabled_folders:
            enabled_folders = config.scan.roots
        
        # Get all photos
        all_media = scan_multiple_directories(
            enabled_folders,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        photos = filter_by_type(all_media, "photo")
        
        # Collect blur scores
        scores = []
        histogram = {
            '0-50': 0,
            '50-100': 0,
            '100-150': 0,
            '150-200': 0,
            '200+': 0
        }
        
        for photo in photos:
            metadata = get_metadata(photo.path)
            blur_score = metadata.get(score_key)
            
            if blur_score is not None:
                scores.append({
                    'path': str(photo.path),
                    'name': photo.path.name,
                    'blur_score': blur_score
                })
                
                # Update histogram
                if blur_score < 50:
                    histogram['0-50'] += 1
                elif blur_score < 100:
                    histogram['50-100'] += 1
                elif blur_score < 150:
                    histogram['100-150'] += 1
                elif blur_score < 200:
                    histogram['150-200'] += 1
                else:
                    histogram['200+'] += 1
        
        return jsonify({
            'success': True,
            'scores': scores,
            'histogram': histogram,
            'total_with_scores': len(scores),
            'total_photos': len(photos),
            'method': method
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/quality/apply-threshold')
def apply_blur_threshold():
    """
    Apply blur threshold to flag photos based on their stored blur scores
    Body: {
        "threshold": 100.0,
        "flag_color": "red",
        "method": "laplacian"  # Optional: which method's scores to use
    }
    """
    try:
        from flask import request
        from photo_tool.actions.metadata import get_metadata, set_color_label
        
        data = request.get_json()
        threshold = float(data.get('threshold', 100.0))
        flag_color = data.get('flag_color', 'red')
        method = data.get('method', 'laplacian').lower()
        score_key = f'blur_score_{method}'
        
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Get enabled folders
        enabled_folders = get_enabled_folders(workspace_path)
        if not enabled_folders:
            enabled_folders = config.scan.roots
        
        # Get all photos
        all_media = scan_multiple_directories(
            enabled_folders,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        photos = filter_by_type(all_media, "photo")
        
        # Apply threshold
        flagged_count = 0
        unflagged_count = 0
        changed_count = 0
        
        for photo in photos:
            metadata = get_metadata(photo.path)
            blur_score = metadata.get('blur_score')
            current_color = metadata.get('color')
            
            if blur_score is not None:
                should_be_flagged = blur_score < threshold
                is_flagged = current_color == flag_color
                
                if should_be_flagged:
                    flagged_count += 1
                    if not is_flagged:
                        # Need to flag it
                        set_color_label(photo.path, flag_color)
                        changed_count += 1
                else:
                    # Should NOT be flagged
                    if is_flagged:
                        # Remove flag
                        set_color_label(photo.path, None)
                        unflagged_count += 1
                        changed_count += 1
        
        return jsonify({
            'success': True,
            'threshold': threshold,
            'flag_color': flag_color,
            'method': method,
            'flagged_count': flagged_count,
            'unflagged_count': unflagged_count,
            'changed_count': changed_count
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# MEDIA MANAGER ENDPOINTS
# =============================================================================

# Scanner progress tracking
_scan_progress = {
    'status': 'idle',
    'total': 0,
    'completed': 0,
    'current_file': '',
    'current_analyzer': '',
    'elapsed_seconds': 0,
    'estimated_remaining_seconds': 0,
    'photos_per_second': 0,
    'error_count': 0
}

@app.get('/api/media/folders')
def get_media_folders():
    """Get all registered media folders"""
    try:
        folders = media_manager.list_folders()
        available = media_manager.get_available_folders()
        unavailable = media_manager.get_unavailable_folders()
        
        return jsonify({
            'success': True,
            'folders': folders,
            'available_count': len(available),
            'unavailable_count': len(unavailable)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/media/folders')
def add_media_folder():
    """
    Add a media folder to the registry
    Body: {
        "path": "C:/Photos/2024/",
        "name": "Optional Name",
        "category": "internal|usb|network|cloud",
        "notes": "Optional notes"
    }
    """
    try:
        from flask import request
        
        data = request.get_json()
        path = Path(data.get('path'))
        name = data.get('name')
        category = data.get('category')
        notes = data.get('notes')
        
        success = media_manager.add_folder(path, name, category, notes)
        
        if success:
            return jsonify({
                'success': True,
                'folder': media_manager.get_folder(str(path)).to_dict()
            })
        else:
            return jsonify({'error': 'Failed to add media folder (may already exist)'}), 400
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.delete('/api/media/folders/<path:folder_path>')
def remove_media_folder(folder_path):
    """Remove a media folder from registry"""
    try:
        success = media_manager.remove_folder(folder_path)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Folder not found'}), 404
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/media/folders/<path:folder_path>/status')
def get_folder_scan_status(folder_path):
    """Get scan status for a media folder"""
    try:
        folder = media_manager.get_folder(folder_path)
        
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
        
        return jsonify({
            'success': True,
            'is_scanned': folder.is_scanned,
            'scan_date': folder.scan_date,
            'scan_coverage': folder.scan_coverage or {},
            'is_available': Path(folder.path).exists()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/media/folders/<path:folder_path>/scan')
def scan_media_folder(folder_path):
    """
    Trigger pre-scan of a media folder
    Body: {
        "analyzers": ["blur", "burst"],  # Optional
        "force": false,                   # Force rescan
        "threads": 4                      # Parallel threads
    }
    """
    global _scan_progress
    
    try:
        from flask import request
        # Lazy import to avoid circular dependencies
        import sys
        import importlib
        
        # Import scanner module
        scanner_module = importlib.import_module('photo_tool.prescan.scanner')
        FolderScanner = scanner_module.FolderScanner
        
        data = request.get_json() or {}
        analyzers = data.get('analyzers', ['blur'])
        force = data.get('force', False)
        threads = data.get('threads', 4)
        
        folder = media_manager.get_folder(folder_path)
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
        
        # Initialize progress
        _scan_progress = {
            'status': 'running',
            'total': 0,
            'completed': 0,
            'current_file': 'Initializing...',
            'current_analyzer': '',
            'elapsed_seconds': 0,
            'estimated_remaining_seconds': 0,
            'photos_per_second': 0,
            'error_count': 0
        }
        
        def progress_callback(progress):
            global _scan_progress
            _scan_progress = progress
        
        # Run scan in background thread
        def run_scan():
            try:
                scanner = FolderScanner(
                    Path(folder.path),
                    analyzers=analyzers,
                    threads=threads,
                    skip_existing=not force,
                    progress_callback=progress_callback
                )
                
                results = scanner.scan()
                
                # Update media manager
                coverage = {}
                for analyzer in analyzers:
                    coverage[analyzer] = 100.0  # 100% if scan completed
                
                media_manager.update_scan_status(
                    folder.path,
                    is_scanned=True,
                    scan_coverage=coverage,
                    stats={'photos': results['total']}
                )
                
                _scan_progress['status'] = 'complete'
                _scan_progress['message'] = f"Complete! Scanned {results['scanned']}, skipped {results['skipped']}"
            
            except Exception as e:
                logger.error(f"Scan error: {e}")
                _scan_progress['status'] = 'error'
                _scan_progress['message'] = str(e)
        
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Scan started',
            'folder': folder.path
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/media/folders/<path:folder_path>/scan-progress')
def get_scan_progress(folder_path):
    """Get scan progress (SSE)"""
    def generate():
        last_progress = -1
        while True:
            current = _scan_progress.copy()
            
            # Send if changed
            if current['completed'] != last_progress or current['status'] in ['complete', 'error']:
                data = json.dumps(current)
                yield f"data: {data}\n\n"
                last_progress = current['completed']
            
            # Stop if complete
            if current['status'] in ['complete', 'error', 'idle']:
                break
            
            time.sleep(0.5)
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# =============================================================================
# WORKSPACE MANAGEMENT ENDPOINTS
# =============================================================================

@app.delete('/api/workspaces/<path:workspace_path>')
def delete_workspace(workspace_path):
    """Delete a workspace from registry and optionally delete config files"""
    try:
        from flask import request
        
        # Check if we should also delete config files
        data = request.get_json() if request.is_json else {}
        delete_config = data.get('delete_config', False)
        
        success = workspace_manager.remove_workspace(workspace_path, delete_config=delete_config)
        
        if success:
            return jsonify({
                'success': True,
                'message': f"Workspace removed{'and config deleted' if delete_config else ''}"
            })
        else:
            return jsonify({'error': 'Workspace not found or could not be deleted'}), 404
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.get('/api/workspaces')
def get_workspaces_list():
    """Get list of all registered workspaces"""
    try:
        workspaces = workspace_manager.list_workspaces()
        current = workspace_manager.get_current_workspace()
        
        return jsonify({
            'success': True,
            'workspaces': workspaces,
            'current': current
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/workspaces')
def add_workspace():
    """
    Add a new workspace
    Body: {
        "path": "C:/Path/To/Workspace",
        "name": "Optional Name"
    }
    """
    try:
        from flask import request
        
        data = request.get_json()
        path = Path(data.get('path'))
        name = data.get('name')
        
        success = workspace_manager.add_workspace(path, name)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to add workspace'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/workspaces/switch')
def switch_workspace():
    """
    Switch to a different workspace
    Body: { "path": "C:/Path/To/Workspace" }
    """
    try:
        from flask import request
        global _current_workspace_path
        
        data = request.get_json()
        path = data.get('path')
        
        success = workspace_manager.switch_workspace(path)
        
        if success:
            _current_workspace_path = Path(path)
            return jsonify({'success': True, 'current': path})
        else:
            return jsonify({'error': 'Failed to switch workspace'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.get('/api/workspace/folders')
def get_workspace_folders_api():
    """Get folders for current workspace with enabled status"""
    try:
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Auto-migrate old structure to new if needed
        if config.folders is None or (isinstance(config.folders, list) and len(config.folders) == 0):
            if hasattr(config, 'scan') and hasattr(config.scan, 'roots') and config.scan.roots:
                logger.info("Migrating old config structure to new folders format")
                migrated_folders = []
                for root in config.scan.roots:
                    migrated_folders.append({
                        'path': str(root),
                        'enabled': True,  # Enable all existing folders by default
                        'photo_count': 0,
                        'video_count': 0,
                        'audio_count': 0
                    })
                config.folders = migrated_folders
                save_config(config, ws.config_file)
                logger.info(f"Migrated {len(config.folders)} folders to new structure")
        
        # Build folder list from new structure
        folders = []
        if hasattr(config, 'folders') and config.folders:
            for folder_config in config.folders:
                folder_path = folder_config.get('path')
                if not folder_path:
                    continue
                
                # Check media manager for scan status
                photo_count = 0
                is_scanned = False
                media_folder = media_manager.get_folder(folder_path)
                if media_folder:
                    photo_count = media_folder.total_photos
                    is_scanned = media_folder.is_scanned
                else:
                    # Fallback: count sidecar files
                    try:
                        from photo_tool.prescan.sidecar import SidecarManager
                        root_path = Path(folder_path)
                        if root_path.exists():
                            sidecar_count = len(list(root_path.rglob(f"*{SidecarManager.SIDECAR_SUFFIX}")))
                            photo_count = sidecar_count
                            is_scanned = sidecar_count > 0
                    except:
                        pass
                
                folders.append({
                    'path': folder_path,
                    'enabled': folder_config.get('enabled', True),
                    'exists': Path(folder_path).exists(),
                    'photo_count': photo_count,
                    'is_scanned': is_scanned
                })
        
        return jsonify({
            'success': True,
            'folders': folders,
            'workspace': str(workspace_path)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/workspace/folders/toggle')
def toggle_folder_api():
    """
    Toggle folder enabled status
    Body: {
        "path": "D:/Photos/2018-2020",
        "enabled": true/false
    }
    """
    try:
        from flask import request
        
        data = request.get_json()
        folder_path = data.get('path')
        enabled = data.get('enabled', True)
        
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Update enabled status in config
        if config.folders:
            found = False
            for folder in config.folders:
                if isinstance(folder, dict) and folder.get('path') == folder_path:
                    folder['enabled'] = enabled
                    found = True
                    break
            
            if found:
                save_config(config, ws.config_file)
                logger.info(f"Toggled folder {folder_path}: enabled={enabled}")
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Folder not found in workspace'}), 404
        else:
            return jsonify({'error': 'No folders configured'}), 400
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/browse/folders')
def browse_folders():
    """
    Browse filesystem directories
    Query params:
        - path: Directory path to browse (defaults to user's home or drives on Windows)
    Returns: { "current_path": "...", "parent": "...", "folders": [...] }
    """
    try:
        from flask import request
        import os
        
        requested_path = request.args.get('path', '')
        
        # If no path specified, list drives on Windows or home on Unix
        if not requested_path:
            if os.name == 'nt':  # Windows
                import string
                from ctypes import windll
                
                # Get available drives
                drives = []
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive_path = f"{letter}:\\"
                        if Path(drive_path).exists():
                            drives.append({
                                'name': f"{letter}:",
                                'path': drive_path,
                                'is_accessible': True
                            })
                    bitmask >>= 1
                
                return jsonify({
                    'current_path': '',
                    'parent': None,
                    'folders': drives,
                    'is_root': True
                })
            else:  # Unix-like
                requested_path = str(Path.home())
        
        current_path = Path(requested_path).resolve()
        
        # Security check: ensure path exists and is accessible
        if not current_path.exists():
            return jsonify({'error': 'Path does not exist'}), 400
        
        if not current_path.is_dir():
            return jsonify({'error': 'Path is not a directory'}), 400
        
        # Get parent path
        parent = str(current_path.parent) if current_path.parent != current_path else None
        
        # List subdirectories
        folders = []
        try:
            for item in sorted(current_path.iterdir()):
                if item.is_dir():
                    try:
                        # Check if directory is accessible
                        list(item.iterdir())
                        is_accessible = True
                    except PermissionError:
                        is_accessible = False
                    
                    folders.append({
                        'name': item.name,
                        'path': str(item),
                        'is_accessible': is_accessible
                    })
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403
        
        return jsonify({
            'current_path': str(current_path),
            'parent': parent,
            'folders': folders,
            'is_root': False
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.delete('/api/workspace/folders/remove')
def remove_folder_from_workspace():
    """
    Remove a folder from current workspace
    Body: { "path": "E:/Photos/" }
    """
    try:
        from flask import request
        
        data = request.get_json()
        folder_path = data.get('path')
        
        if not folder_path:
            return jsonify({'error': 'Missing folder path'}), 400
        
        ws = Workspace(_current_workspace_path)
        
        # Load config
        config = load_config(ws.config_file)
        
        # Normalize path
        normalized_path = str(Path(folder_path).resolve())
        
        # Remove from folders list
        if hasattr(config, 'folders'):
            config.folders = [f for f in config.folders if f.get('path') != normalized_path]
        
        # Save updated config
        save_config(config, ws.config_file)
        
        # Also remove from enabled folders (legacy support)
        enabled_folders_file = _current_workspace_path / "enabled_folders.json"
        if enabled_folders_file.exists():
            try:
                with open(enabled_folders_file, 'r', encoding='utf-8') as f:
                    enabled = json.load(f)
                
                enabled = [f for f in enabled if f != normalized_path]
                
                with open(enabled_folders_file, 'w', encoding='utf-8') as f:
                    json.dump(enabled, f, indent=2)
            except Exception as e:
                logger.warning(f"Could not update enabled_folders.json: {e}")
        
        logger.info(f"Removed folder from workspace: {folder_path}")
        
        return jsonify({
            'success': True,
            'message': 'Folder removed from workspace'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/workspace/folders/add')
def add_folder_to_workspace():
    """
    Add a new folder to current workspace
    Body: { "path": "D:/Photos/NewFolder" }
    """
    try:
        from flask import request
        
        data = request.get_json()
        folder_path = Path(data.get('path'))
        
        if not folder_path.exists():
            return jsonify({'error': 'Folder does not exist'}), 400
        
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Initialize folders list if not exists
        if config.folders is None:
            config.folders = []
        
        # Check if folder already exists
        folder_path_str = str(folder_path.resolve())
        existing_paths = [f.get('path') for f in config.folders if isinstance(f, dict)]
        
        if folder_path_str in existing_paths:
            return jsonify({'error': 'Folder already exists in workspace'}), 400
        
        # Add to folders list
        config.folders.append({
            'path': folder_path_str,
            'enabled': True,  # Enable by default
            'photo_count': 0,
            'video_count': 0,
            'audio_count': 0
        })
        
        save_config(config, ws.config_file)
        
        logger.info(f"Added folder to workspace: {folder_path}")
        
        return jsonify({
            'success': True,
            'message': 'Folder added to workspace'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# PROJECT MANAGEMENT ENDPOINTS
# =============================================================================

@app.get('/api/projects')
def get_projects():
    """Get all projects for current workspace"""
    try:
        pm = get_project_manager()
        projects = pm.list_projects()
        
        return jsonify({
            'success': True,
            'projects': projects,
            'total': len(projects)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.get('/api/projects/<project_id>')
def get_project(project_id):
    """Get a specific project"""
    try:
        pm = get_project_manager()
        project = pm.get_project(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/projects')
def create_project():
    """
    Create a new project
    Body: {
        "name": "Project Name",
        "selection_mode": "filter" | "explicit" | "hybrid",
        "filters": {...},
        "photo_ids": [...],
        "export_settings": {...}
    }
    """
    try:
        from flask import request
        
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Project name is required'}), 400
        
        # Get workspace folders to create project template
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Build folder list from workspace
        workspace_folders = []
        for folder in config.folders:
            workspace_folders.append({
                'path': folder.get('path'),
                'photo_count': 0,  # Will be updated when enabled
                'video_count': 0,
                'audio_count': 0
            })
        
        pm = get_project_manager()
        
        project = pm.create_project(
            name=data['name'],
            selection_mode=data.get('selection_mode', 'filter'),
            workspace_folders=workspace_folders,
            filters=data.get('filters'),
            photo_ids=data.get('photo_ids'),
            export_settings=data.get('export_settings'),
            quality_settings=data.get('quality_settings')
        )
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.put('/api/projects/<project_id>')
def update_project(project_id):
    """Update an existing project"""
    try:
        from flask import request
        
        pm = get_project_manager()
        project = pm.get_project(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            project.name = data['name']
        if 'selection_mode' in data:
            project.selection_mode = data['selection_mode']
        if 'folders' in data:
            project.folders = data['folders']  # Save folder selection
        if 'filters' in data:
            from photo_tool.projects.manager import ProjectFilters
            project.filters = ProjectFilters(**data['filters']) if data['filters'] else None
        if 'photo_ids' in data:
            project.photo_ids = data['photo_ids']
        if 'manual_additions' in data:
            project.manual_additions = data['manual_additions']
        if 'manual_exclusions' in data:
            project.manual_exclusions = data['manual_exclusions']
        if 'export_settings' in data:
            from photo_tool.projects.manager import ExportSettings
            project.export_settings = ExportSettings(**data['export_settings']) if data['export_settings'] else None
        if 'quality_settings' in data:
            from photo_tool.projects.manager import QualityDetectionSettings
            project.quality_settings = QualityDetectionSettings(**data['quality_settings']) if data['quality_settings'] else None
        
        # Save
        pm.save_project(project)
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.put('/api/projects/<project_id>/quality-settings')
def update_project_quality_settings(project_id):
    """Update quality detection settings for a project"""
    try:
        from flask import request
        from photo_tool.projects.manager import QualityDetectionSettings
        
        pm = get_project_manager()
        project = pm.get_project(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        data = request.get_json()
        
        # Update quality settings
        if 'quality_settings' in data:
            project.quality_settings = QualityDetectionSettings(**data['quality_settings'])
        
        # Save
        pm.save_project(project)
        
        return jsonify({
            'success': True,
            'quality_settings': project.quality_settings.__dict__ if project.quality_settings else None
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.delete('/api/projects/<project_id>')
def delete_project(project_id):
    """Delete a project"""
    try:
        pm = get_project_manager()
        success = pm.delete_project(project_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to delete project'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.get('/api/projects/<project_id>/media')
def get_project_media(project_id):
    """
    Get all media for a specific project (only enabled folders)
    Query params:
        - limit: Max number of items (default: 2500)
        - offset: Skip N items (default: 0)
        - type: Filter by type (photo, video, audio, or 'all')
    """
    try:
        from flask import request
        from photo_tool.prescan import SidecarManager
        import hashlib
        
        pm = get_project_manager()
        project = pm.get_project(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get query params
        limit = int(request.args.get('limit', 2500))
        offset = int(request.args.get('offset', 0))
        media_type = request.args.get('type', 'all')
        
        # Get enabled folders from project
        enabled_folders = []
        if project.folders:
            enabled_folders = [Path(f['path']) for f in project.folders if f.get('enabled', False)]
        
        if not enabled_folders:
            return jsonify({
                'photos': [],
                'videos': [],
                'audio': [],
                'total': 0,
                'message': 'No folders enabled in project. Enable folders in Project tab.'
            })
        
        # Load workspace config for scan settings
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Scan enabled folders
        all_media = scan_multiple_directories(
            enabled_folders,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        
        # Separate by type
        photos = filter_by_type(all_media, 'photo')
        videos = filter_by_type(all_media, 'video')
        audio = filter_by_type(all_media, 'audio')
        
        # Sort photos by capture time (newest first)
        from datetime import datetime
        photos_with_times = []
        for photo in photos:
            try:
                capture_time = get_capture_time(photo.path, fallback_to_mtime=True)
                if capture_time is None:
                    capture_time = datetime.fromtimestamp(photo.path.stat().st_mtime)
                photos_with_times.append((photo, capture_time))
            except Exception as e:
                photos_with_times.append((photo, datetime.now()))
        
        photos_with_times.sort(key=lambda x: x[1], reverse=True)
        photos = [p[0] for p in photos_with_times]
        
        # Apply filters based on type
        if media_type == 'photo':
            result_media = photos
        elif media_type == 'video':
            result_media = videos
        elif media_type == 'audio':
            result_media = audio
        else:
            result_media = photos + videos + audio
        
        # Paginate
        result_page = result_media[offset:offset + limit]
        
        # Initialize project sidecar manager
        project_dir = pm.projects_dir / project_id
        psm = ProjectSidecarManager(project_dir)
        
        # Build response
        result = []
        for item in result_page:
            # 1. Get global metadata
            global_metadata = get_metadata(item.path)
            
            # 2. Merge with project-specific overrides
            metadata = psm.merge_metadata(global_metadata, item.path)
            
            # 3. Get burst_keep flag from project sidecar
            burst_keep = False
            sidecar_path = psm.sidecar_dir / f"{item.path.stem}.sidecar"
            if sidecar_path.exists():
                try:
                    with open(sidecar_path, 'r', encoding='utf-8') as f:
                        project_sidecar = json.load(f)
                        burst_keep = project_sidecar.get('burst_keep', False)
                except Exception as e:
                    logger.debug(f"Failed to load burst_keep for {item.path.name}: {e}")
            
            # Get relative path
            relative_path = None
            for root in enabled_folders:
                try:
                    relative_path = str(item.path.relative_to(root))
                    break
                except ValueError:
                    continue
            
            if relative_path is None:
                relative_path = str(item.path)
            
            # Get capture time
            capture_time = get_capture_time(item.path, fallback_to_mtime=True)
            capture_time_str = capture_time.strftime('%Y-%m-%d %H:%M:%S') if capture_time else None
            
            # Get blur scores from sidecar analyses
            blur_scores = {
                'laplacian': None,
                'tenengrad': None,
                'roi': None
            }
            try:
                sidecar = SidecarManager(item.path)
                if sidecar.exists:
                    sidecar.load()
                    blur_data = sidecar.get('analyses.blur')
                    if blur_data:
                        for method in ['laplacian', 'tenengrad', 'roi']:
                            if method in blur_data and isinstance(blur_data[method], dict):
                                blur_scores[method] = blur_data[method].get('score')
            except Exception as e:
                logger.warning(f"Failed to load blur scores from sidecar: {e}")
            
            result.append({
                'id': str(item.path),
                'name': item.path.name,
                'path': str(item.path),
                'relative_path': relative_path,
                'type': item.media_type,  # MediaFile uses media_type, not type
                'size': item.path.stat().st_size,
                'capture_time': capture_time_str,
                'rating': metadata.get('rating', 0),
                'color': metadata.get('color'),
                'keywords': metadata.get('keywords', []),
                'blur_scores': blur_scores,
                'burst_keep': burst_keep,  # Burst keep flag (project-specific)
                'thumbnail': f"/thumbnails/{item.path.stem}.jpg",
                'full_image': f"/images/{item.path.stem}{item.path.suffix}",
                # Metadata source indicators
                'has_project_override': metadata.get('_has_project_override', False),
                'rating_source': metadata.get('_rating_source', 'global'),
                'color_source': metadata.get('_color_source', 'global')
            })
        
        # === BURST GROUPING ===
        # Analyze burst relationships and add burst metadata to photos
        burst_groups = {}  # burst_id -> list of photo paths
        photo_to_burst = {}  # photo_path -> burst_id
        burst_raw_data = {}  # photo_path -> raw sidecar burst data (for debugging)
        path_by_filename = {}  # filename -> actual path in result (for fixing old sidecar paths)
        
        # Build filename lookup for current photos
        for item_dict in result:
            if item_dict['type'] == 'photo':
                filename = Path(item_dict['path']).name
                path_by_filename[filename] = item_dict['path']
        
        for item_dict in result:
            if item_dict['type'] != 'photo':
                continue
            
            try:
                sidecar = SidecarManager(Path(item_dict['path']))
                if sidecar.exists:
                    sidecar.load()
                    burst_data = sidecar.get('analyses.burst')
                    
                    # Store raw burst data for debugging
                    if burst_data:
                        burst_raw_data[item_dict['path']] = burst_data
                        logger.debug(f"Burst data for {Path(item_dict['path']).name}: is_burst_candidate={burst_data.get('is_burst_candidate')}, neighbors={len(burst_data.get('burst_neighbors', []))}")
                    
                    if burst_data and burst_data.get('is_burst_candidate'):
                        # Collect all photos in this burst group
                        neighbors = burst_data.get('burst_neighbors', [])
                        
                        # FIX: Replace neighbor paths with current paths (fixes moved folders)
                        all_paths = [item_dict['path']]
                        fixed_neighbors = []
                        for n in neighbors:
                            neighbor_path = n['path']
                            neighbor_filename = Path(neighbor_path).name
                            
                            # Try to find the actual current path by filename
                            if neighbor_filename in path_by_filename:
                                actual_path = path_by_filename[neighbor_filename]
                                all_paths.append(actual_path)
                                fixed_neighbors.append(actual_path)
                            elif neighbor_path in path_by_filename.values():
                                # Path is already correct
                                all_paths.append(neighbor_path)
                                fixed_neighbors.append(neighbor_path)
                        
                        # DEBUG: Log first burst in detail
                        if len(burst_groups) == 0:
                            print(f"\n=== FIRST BURST DEBUG ===")
                            print(f"  Current photo: {item_dict['path']}")
                            print(f"  Neighbors from sidecar: {[n['path'] for n in neighbors]}")
                            print(f"  Fixed neighbor paths: {fixed_neighbors}")
                            print(f"  All paths in group: {all_paths}")
                            print("=" * 50)
                        
                        # Sort to get consistent burst_id
                        all_paths_sorted = sorted(all_paths)
                        
                        # Generate burst_id from first photo path
                        burst_id = hashlib.md5(all_paths_sorted[0].encode()).hexdigest()[:12]
                        
                        # Store mapping for THIS photo
                        photo_to_burst[item_dict['path']] = burst_id
                        
                        # ALSO store mapping for ALL neighbors (so they get the same burst_id)
                        for neighbor_path in all_paths:
                            if neighbor_path not in photo_to_burst:
                                photo_to_burst[neighbor_path] = burst_id
                        
                        if burst_id not in burst_groups:
                            burst_groups[burst_id] = {
                                'photos': all_paths_sorted,  # Store ALL paths, not just discovered ones
                                'lead_path': all_paths_sorted[0],  # First photo is lead
                                'count': len(all_paths)
                            }
            except Exception as e:
                logger.warning(f"Error processing burst for {item_dict['path']}: {e}")
                import traceback
                traceback.print_exc()
        
        # Add burst metadata to result items
        burst_metadata_assigned = 0
        for item_dict in result:
            if item_dict['path'] in photo_to_burst:
                burst_id = photo_to_burst[item_dict['path']]
                burst_group = burst_groups[burst_id]
                
                item_dict['burst_id'] = burst_id
                item_dict['burst_count'] = burst_group['count']
                item_dict['is_burst_lead'] = (item_dict['path'] == burst_group['lead_path'])
                
                # Add raw burst data for debugging
                item_dict['burst_raw_data'] = burst_raw_data.get(item_dict['path'], {})
                burst_metadata_assigned += 1
            else:
                item_dict['burst_id'] = None
                item_dict['burst_count'] = 0
                item_dict['is_burst_lead'] = False
                item_dict['burst_raw_data'] = burst_raw_data.get(item_dict['path'], {})
        
        print(f"\n=== BURST GROUPING RESULTS ===")
        print(f"Assigned burst metadata to {burst_metadata_assigned} photos out of {len(result)} total")
        
        total_burst_photos = sum(g['count'] for g in burst_groups.values())
        print(f"Burst grouping: {len(burst_groups)} groups found with {total_burst_photos} photos in bursts")
        print(f"photo_to_burst mapping has {len(photo_to_burst)} entries")
        
        if len(burst_groups) > 0:
            print(f"\nSample burst groups: {list(burst_groups.keys())[:3]}")
            for burst_id in list(burst_groups.keys())[:3]:
                group = burst_groups[burst_id]
                print(f"  Burst {burst_id}: {group['count']} photos, lead: {Path(group['lead_path']).name}")
                print(f"    All photos: {[Path(p).name for p in group['photos'][:5]]}")
        print("=" * 50 + "\n")
        
        return jsonify({
            'media': result,
            'total': len(result_media),
            'offset': offset,
            'limit': limit,
            'project_id': project_id,
            'counts': {
                'photos': len(photos),
                'videos': len(videos),
                'audio': len(audio)
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/projects/<project_id>/bursts')
def get_project_bursts(project_id):
    """Get burst groups for a specific project (only enabled folders)"""
    try:
        pm = get_project_manager()
        project = pm.get_project(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get enabled folders
        enabled_folders = []
        if project.folders:
            enabled_folders = [Path(f['path']) for f in project.folders if f.get('enabled', False)]
        
        if not enabled_folders:
            return jsonify({
                'bursts': [],
                'stats': {'total': 0, 'groups': 0}
            })
        
        # Load all photos from enabled folders
        workspace_path = get_current_workspace()
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        all_media = scan_multiple_directories(
            enabled_folders,
            config.scan.extensions,
            recursive=config.scan.recurse,
            show_progress=False
        )
        
        photos = filter_by_type(all_media, 'photo')
        
        # Get burst info from sidecars
        from photo_tool.prescan import SidecarManager
        burst_groups = {}
        
        for photo in photos:
            try:
                sidecar = SidecarManager(photo.path)
                if sidecar.exists:
                    sidecar.load()
                    burst_data = sidecar.get('analyses.burst')
                    if burst_data and burst_data.get('is_burst'):
                        group_id = burst_data.get('group_id')
                        if group_id:
                            if group_id not in burst_groups:
                                burst_groups[group_id] = []
                            
                            metadata = get_metadata(photo.path)
                            burst_groups[group_id].append({
                                'path': str(photo.path),
                                'name': photo.path.name,
                                'rating': metadata.get('rating', 0),
                                'thumbnail': f"/thumbnails/{photo.path.stem}.jpg",
                                'position': burst_data.get('position', 0),
                                'is_best': burst_data.get('is_best', False)
                            })
            except Exception as e:
                logger.warning(f"Failed to load burst info for {photo.path}: {e}")
        
        # Convert to list format
        bursts = []
        for group_id, photos_in_burst in burst_groups.items():
            # Sort by position
            photos_in_burst.sort(key=lambda x: x['position'])
            
            bursts.append({
                'id': group_id,
                'photos': photos_in_burst,
                'count': len(photos_in_burst)
            })
        
        # Sort by count (largest first)
        bursts.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'bursts': bursts,
            'stats': {
                'total': sum(b['count'] for b in bursts),
                'groups': len(bursts)
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.get('/api/projects/<project_id>/sidecar-stats')
def get_project_sidecar_stats(project_id):
    """Get statistics about project-specific metadata overrides"""
    try:
        pm = get_project_manager()
        project = pm.get_project(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Initialize project sidecar manager
        project_dir = pm.projects_dir / project_id
        psm = ProjectSidecarManager(project_dir)
        
        # Get stats
        stats = psm.get_stats()
        overrides = psm.list_overrides()
        
        return jsonify({
            'stats': stats,
            'photos_with_overrides': overrides
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.post('/api/projects/<project_id>/export')
def add_project_export_record(project_id):
    """Add export record to project"""
    try:
        from flask import request
        
        pm = get_project_manager()
        data = request.get_json()
        
        success = pm.add_export_record(project_id, data)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to add export record'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.get('/api/system/config-info')
def get_config_info():
    """Get configuration file locations and structure"""
    try:
        from pathlib import Path
        import os
        
        home = Path.home()
        config_root = home / ".photo_tool"
        
        # Get file sizes
        def get_size(path: Path) -> int:
            return path.stat().st_size if path.exists() else 0
        
        def format_size(size_bytes: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        
        # Count sidecar files
        def count_sidecars(folder_path: str) -> int:
            try:
                path = Path(folder_path)
                if not path.exists():
                    return 0
                # Match both naming conventions:
                # - New: .PHOTONAME.phototool.json (with leading dot)
                # - Current: PHOTONAME.JPG.phototool.json (no leading dot)
                sidecars = list(path.rglob('*.phototool.json'))
                return len(sidecars)
            except:
                return 0
        
        # Build config structure
        config_info = {
            'global_config': {
                'root': str(config_root),
                'exists': config_root.exists(),
                'files': []
            },
            'media_manager': {
                'config_file': str(media_manager.config_file),
                'exists': media_manager.config_file.exists(),
                'size': format_size(get_size(media_manager.config_file)),
                'folder_count': len(media_manager.folders)
            },
            'workspace_registry': {
                'config_file': str(workspace_manager.workspaces_file),
                'exists': workspace_manager.workspaces_file.exists(),
                'size': format_size(get_size(workspace_manager.workspaces_file)),
                'workspace_count': len(workspace_manager.workspaces)
            },
            'current_workspace': None,
            'sidecars': []
        }
        
        # Current workspace info
        if workspace_manager.current_workspace:
            ws_path = Path(workspace_manager.current_workspace)
            config_path = ws_path / "config.yaml"
            
            config_info['current_workspace'] = {
                'path': str(ws_path),
                'config_file': str(config_path),
                'exists': config_path.exists(),
                'size': format_size(get_size(config_path))
            }
            
            # Get folders ONLY from current workspace and count their sidecars
            config = load_config(config_path) if config_path.exists() else None
            if config and hasattr(config, 'folders'):
                for folder in config.folders:
                    folder_path = folder.get('path', '')
                    if folder_path:
                        sidecar_count = count_sidecars(folder_path)
                        
                        # Get additional info from media manager if available
                        media_folder = next((mf for mf in media_manager.folders if mf.path == folder_path), None)
                        
                        config_info['sidecars'].append({
                            'folder': folder_path,
                            'sidecar_count': sidecar_count,
                            'enabled': folder.get('enabled', True),
                            'name': media_folder.name if media_folder else None,
                            'category': media_folder.category if media_folder else None
                        })
        
        return jsonify(config_info)
        
    except Exception as e:
        logger.error(f"Error getting config info: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import socket
    
    # Get local IP for Smart TV access
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "localhost"
    
    print("\n" + "="*60)
    print("Photo Tool Web GUI - Server Starting")
    print("="*60)
    print(f"PC Browser:       http://localhost:8000")
    print(f"Smart TV/Mobile:  http://{local_ip}:8000")
    print("="*60)
    print("\nFor Smart TV access:")
    print("   1. Make sure Windows Firewall allows port 8000")
    print("   2. Open Smart TV browser")
    print(f"   3. Navigate to: http://{local_ip}:8000")
    print("\nTo enable firewall (run as Administrator):")
    print('   netsh advfirewall firewall add rule name="Photo Tool Web GUI" dir=in action=allow protocol=TCP localport=8000')
    print("\nPress Ctrl+C to stop\n")
    
    # Bind to all interfaces (0.0.0.0) for network access
    app.run(debug=True, port=8000, host='0.0.0.0')
