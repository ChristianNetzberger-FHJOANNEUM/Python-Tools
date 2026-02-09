"""
Pre-generate thumbnails for all scanned photos.
Run this once to create thumbnail cache - makes browsing instant!
"""
import sys
from pathlib import Path

if __name__ != '__main__':
    exit(0)

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import time

# Import workspace manager
from photo_tool.workspace.manager import WorkspaceManager

def generate_thumbnail(photo_data, workspace_path):
    """Generate one thumbnail"""
    photo_path = Path(photo_data['path'])
    filename = photo_data['filename']
    
    # Output path (use workspace directory!)
    cache_dir = workspace_path / "cache" / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = cache_dir / f"{photo_path.stem}.jpg"
    
    # Skip if already exists
    if thumb_path.exists():
        return {'status': 'exists', 'file': filename}
    
    try:
        # Check if original exists
        if not photo_path.exists():
            return {'status': 'missing', 'file': filename}
        
        # Open and process
        img = Image.open(photo_path)
        
        # Apply EXIF orientation
        try:
            exif = img.getexif()
            if exif:
                orientation = exif.get(0x0112)
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except:
            pass
        
        # Resize
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Save
        img.save(thumb_path, 'JPEG', quality=85, optimize=True)
        
        return {'status': 'created', 'file': filename}
    
    except Exception as e:
        return {'status': 'error', 'file': filename, 'error': str(e)}

def main():
    """Generate all thumbnails"""
    print("\n" + "="*60)
    print("THUMBNAIL GENERATION UTILITY")
    print("="*60)
    
    # Get workspace
    ws_manager = WorkspaceManager()
    workspace_path_str = ws_manager.get_current_workspace()
    if not workspace_path_str:
        print("ERROR: No workspace selected. Select workspace in GUI first!")
        return
    
    workspace_path = Path(workspace_path_str)
    print(f"Workspace: {workspace_path}")
    
    # Get database (from gui_poc/db/)
    db_path = Path(__file__).parent / 'db' / 'workspace_media.db'
    if not db_path.exists():
        print("ERROR: Database not found. Run migration first!")
        return
    print(f"Database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all photos
    cursor.execute("""
        SELECT m.path, m.filename, m.folder
        FROM media m
        WHERE m.media_type = 'photo'
        ORDER BY m.folder, m.filename
    """)
    
    photos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    print(f"Found {len(photos)} photos in database")
    print("="*60)
    
    response = input("\nGenerate thumbnails for all photos? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Create cache directory (in workspace!)
    cache_dir = workspace_path / "cache" / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nCache directory: {cache_dir}")
    
    # Generate thumbnails in parallel
    print(f"\nGenerating thumbnails (8 parallel workers)...")
    start_time = time.time()
    
    results = {'created': 0, 'exists': 0, 'missing': 0, 'error': 0}
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(generate_thumbnail, photo, workspace_path) for photo in photos]
        
        for i, future in enumerate(futures, 1):
            result = future.result()
            results[result['status']] += 1
            
            # Progress update every 100 photos
            if i % 100 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                remaining = (len(photos) - i) / rate
                print(f"  Progress: {i}/{len(photos)} ({i*100//len(photos)}%) - {rate:.1f} thumbs/sec - ETA: {remaining:.0f}s")
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print("THUMBNAIL GENERATION COMPLETE!")
    print("="*60)
    print(f"Created:  {results['created']} new thumbnails")
    print(f"Existed:  {results['exists']} already cached")
    print(f"Missing:  {results['missing']} original files not found")
    print(f"Errors:   {results['error']} generation errors")
    print(f"\nTotal time: {elapsed:.1f}s ({len(photos)/elapsed:.1f} thumbs/sec)")
    print("\nRestart the server and enjoy instant thumbnail loading!")

if __name__ == '__main__':
    main()
