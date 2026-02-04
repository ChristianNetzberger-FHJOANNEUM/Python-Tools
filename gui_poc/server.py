"""
Flask PoC Server for Photo Tool
Simple web interface to browse and rate photos
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import sys
import json

# Add parent directory to path to import photo_tool
sys.path.insert(0, str(Path(__file__).parent.parent))

from photo_tool.io import scan_multiple_directories, filter_by_type
from photo_tool.config import load_config
from photo_tool.workspace import Workspace
from photo_tool.actions.rating import get_rating

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for development


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
            # Try to get rating from sidecar
            rating_data = get_rating(photo.path)
            rating = rating_data.get('stars', 0) if rating_data else 0
            comment = rating_data.get('comment', '') if rating_data else ''
            
            result.append({
                'id': str(photo.path),
                'name': photo.path.name,
                'path': str(photo.path.relative_to(config.scan.roots[0]) if config.scan.roots else photo.path),
                'size': photo.size,
                'rating': rating,
                'comment': comment,
                'thumbnail': f"/thumbnails/{photo.path.stem}.jpg"
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
    Body: { "stars": 1-5, "comment": "optional" }
    """
    try:
        from flask import request
        from photo_tool.actions.rating import set_rating
        
        data = request.get_json()
        stars = data.get('stars', 0)
        comment = data.get('comment', '')
        
        # Decode photo path
        photo_path = Path(photo_id)
        
        # Set rating
        set_rating(photo_path, stars, comment)
        
        return jsonify({
            'success': True,
            'stars': stars,
            'comment': comment
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
            return jsonify({'error': 'Thumbnail not found'}), 404
    
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
            rating_data = get_rating(photo.path)
            if rating_data and rating_data.get('stars', 0) > 0:
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


if __name__ == '__main__':
    print("🚀 Starting Photo Tool PoC Server...")
    print("📸 Open browser: http://localhost:8000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=8000, host='0.0.0.0')
