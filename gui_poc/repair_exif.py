"""
Repair missing EXIF data for specific folders.
Re-extracts EXIF from original photos and updates the database.
"""
import sys
from pathlib import Path

# IMPORTANT: Windows multiprocessing guard
if __name__ != '__main__':
    exit(0)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

# =============================================================================
# CONFIGURE FOLDER TO REPAIR
# =============================================================================
FOLDER_TO_REPAIR = r"E:\Lumix-2026-01\101_PANA"

def extract_exif_capture_time(photo_path):
    """Extract capture time from EXIF data"""
    try:
        img = Image.open(photo_path)
        exif = img.getexif()
        
        if exif:
            # Try different EXIF tags for date/time
            for tag_id in [36867, 36868, 306]:  # DateTimeOriginal, DateTimeDigitized, DateTime
                if tag_id in exif:
                    date_str = exif[tag_id]
                    # Parse EXIF date format: "2025:12:03 20:27:26"
                    try:
                        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        return dt.strftime("%Y:%m:%d %H:%M:%S")
                    except:
                        pass
        
        return None
    except Exception as e:
        print(f"  ❌ Error reading EXIF for {photo_path.name}: {e}")
        return None

def main():
    """Repair EXIF data for folder"""
    print("\n" + "="*60)
    print("EXIF REPAIR UTILITY")
    print("="*60)
    print(f"Will repair EXIF data for: {FOLDER_TO_REPAIR}")
    print("="*60)
    
    folder_path = Path(FOLDER_TO_REPAIR)
    if not folder_path.exists():
        print(f"❌ Folder does not exist: {FOLDER_TO_REPAIR}")
        return
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Connect to database
    workspace_root = Path(__file__).parent.parent
    db_path = workspace_root / "gui_poc" / "db" / "workspace_media.db"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find all photos in this folder with NULL capture_time
    cursor.execute("""
        SELECT m.id, m.path, m.filename
        FROM media m
        LEFT JOIN photo_metadata pm ON m.id = pm.media_id
        WHERE m.folder = ? 
          AND m.media_type = 'photo'
          AND (pm.capture_time IS NULL OR pm.capture_time = '')
    """, (str(folder_path),))
    
    photos_to_repair = cursor.fetchall()
    
    print(f"\n📷 Found {len(photos_to_repair)} photos with missing EXIF data")
    
    if len(photos_to_repair) == 0:
        print("✅ No photos need repair!")
        conn.close()
        return
    
    # Repair each photo
    repaired = 0
    failed = 0
    
    print(f"\n🔧 Repairing EXIF data...")
    for i, photo in enumerate(photos_to_repair, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(photos_to_repair)}")
        
        photo_path = Path(photo['path'])
        if not photo_path.exists():
            failed += 1
            continue
        
        # Extract EXIF
        capture_time = extract_exif_capture_time(photo_path)
        
        if capture_time:
            # Update database
            cursor.execute("""
                UPDATE photo_metadata 
                SET capture_time = ?
                WHERE media_id = ?
            """, (capture_time, photo['id']))
            repaired += 1
        else:
            failed += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ EXIF REPAIR COMPLETE!")
    print("="*60)
    print(f"Repaired: {repaired} photos")
    print(f"Failed: {failed} photos")
    print(f"\nRestart the server to see the updated timestamps.")

if __name__ == '__main__':
    main()
