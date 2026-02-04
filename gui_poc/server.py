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

from photo_tool.io import scan_multiple_directories, filter_by_type
from photo_tool.config import load_config
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

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for development

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
    """
    try:
        # Load workspace and config
        workspace_path = Path("C:/PhotoTool_Test")
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Get query params
        from flask import request
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Scan for media
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
            show_progress=False
        )
        
        # Filter to photos only
        photos = filter_by_type(all_media, "photo")
        
        # Paginate
        photos_page = photos[offset:offset + limit]
        
        # Build response
        result = []
        for photo in photos_page:
            # Try to get all metadata
            metadata = get_metadata(photo.path)
            
            result.append({
                'id': str(photo.path),
                'name': photo.path.name,
                'path': str(photo.path.relative_to(config.scan.roots[0]) if config.scan.roots else photo.path),
                'size': photo.size_bytes,
                'rating': metadata.get('rating', 0),
                'color': metadata.get('color'),
                'comment': metadata.get('comment', ''),
                'keywords': metadata.get('keywords', []),
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
    """
    try:
        from flask import request
        from photo_tool.actions.metadata import set_metadata
        
        data = request.get_json()
        rating = data.get('rating', 0)
        comment = data.get('comment', '')
        
        # Decode photo path
        photo_path = Path(photo_id)
        
        # Set rating (now via metadata system)
        set_metadata(photo_path, {
            'rating': rating,
            'comment': comment if comment else None
        })
        
        return jsonify({
            'success': True,
            'rating': rating,
            'comment': comment
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/photos/<path:photo_id>/color')
def set_photo_color(photo_id):
    """
    Set color label for a photo
    Body: { "color": "red" | "yellow" | "green" | "blue" | "purple" | null }
    """
    try:
        from flask import request
        
        data = request.get_json()
        color = data.get('color')
        
        # Decode photo path
        photo_path = Path(photo_id)
        
        # Set color
        set_color_label(photo_path, color)
        
        return jsonify({
            'success': True,
            'color': color
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/photos/<path:photo_id>/keywords')
def update_photo_keywords(photo_id):
    """
    Update keywords for a photo
    Body: { "keywords": ["tag1", "tag2"] } or { "add": "tag" } or { "remove": "tag" }
    """
    try:
        from flask import request
        
        data = request.get_json()
        photo_path = Path(photo_id)
        
        if 'keywords' in data:
            # Set complete keyword list
            set_keywords(photo_path, data['keywords'])
            metadata = get_metadata(photo_path)
            return jsonify({
                'success': True,
                'keywords': metadata.get('keywords', [])
            })
        
        elif 'add' in data:
            # Add single keyword
            add_keyword(photo_path, data['add'])
            metadata = get_metadata(photo_path)
            return jsonify({
                'success': True,
                'keywords': metadata.get('keywords', [])
            })
        
        elif 'remove' in data:
            # Remove single keyword
            remove_keyword(photo_path, data['remove'])
            metadata = get_metadata(photo_path)
            return jsonify({
                'success': True,
                'keywords': metadata.get('keywords', [])
            })
        
        else:
            return jsonify({'error': 'Invalid request'}), 400
    
    except Exception as e:
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
            config.scan.recurse,
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
        "template": "photoswipe" or "simple"
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
        
        if not photo_ids:
            return jsonify({'error': 'No photos selected'}), 400
        
        # Convert IDs to Path objects
        photo_paths = [Path(photo_id) for photo_id in photo_ids]
        
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
                    include_metadata=True
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
            'photo_count': len(photo_ids)
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
        workspace_path = Path("C:/PhotoTool_Test")
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
            # FALLBACK: Try to find and serve original image
            # Search in scan roots
            config = load_config(workspace_path / "config.yaml")
            for root in config.scan.roots:
                root_path = Path(root)
                # Try different cases
                for ext in ['.JPG', '.jpg', '.JPEG', '.jpeg']:
                    original = root_path / f"{Path(filename).stem}{ext}"
                    if original.exists():
                        # Generate thumbnail on-the-fly using Pillow
                        from PIL import Image
                        from io import BytesIO
                        from flask import send_file
                        
                        img = Image.open(original)
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
        return jsonify({'error': str(e)}), 500


@app.get('/images/<path:filename>')
def get_full_image(filename):
    """Serve full-size images for lightbox"""
    try:
        workspace_path = Path("C:/PhotoTool_Test")
        config = load_config(workspace_path / "config.yaml")
        
        # Search in scan roots
        for root in config.scan.roots:
            root_path = Path(root)
            # Try different cases
            for ext in ['.JPG', '.jpg', '.JPEG', '.jpeg', '.PNG', '.png']:
                image_path = root_path / f"{Path(filename).stem}{ext}"
                if image_path.exists():
                    # Serve with optimized size (max 2500px)
                    from PIL import Image
                    from io import BytesIO
                    from flask import send_file
                    
                    img = Image.open(image_path)
                    
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
        workspace_path = Path("C:/PhotoTool_Test")
        ws = Workspace(workspace_path)
        config = load_config(ws.config_file)
        
        # Scan all media
        all_media = scan_multiple_directories(
            config.scan.roots,
            config.scan.extensions,
            config.scan.recurse,
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
        print(f"✓ Using cached burst data (computed at {_burst_cache['computed_at']})")
        return _burst_cache['data']
    
    print("⚡ Computing bursts (config changed or cache empty)...")
    
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
            config.scan.recurse,
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
        
        print(f"✓ Burst analysis complete: {len(bursts)} groups found")
        
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


if __name__ == '__main__':
    print("🚀 Starting Photo Tool PoC Server...")
    print("📸 Open browser: http://localhost:8000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=8000, host='0.0.0.0')
