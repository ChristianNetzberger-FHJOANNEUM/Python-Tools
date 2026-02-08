import sqlite3
from pathlib import Path

db_path = Path("db/workspace_media.db")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("DATABASE CHECK - Direct Query")
print("=" * 80)

# Test the EXACT query from server.py
folder = "E:\\Lumix-2026-01\\101_PANA"
query = f"""
    SELECT 
        m.id, m.path, m.filename, m.folder, m.media_type,
        m.file_size, m.file_mtime, m.is_available,
        m.rating, m.color, m.keywords, m.comment,
        m.created_at, m.updated_at,
        pm.capture_time, pm.width, pm.height,
        pm.camera_make, pm.camera_model, pm.lens_model,
        pm.iso, pm.aperture, pm.shutter_speed, pm.focal_length,
        pm.blur_laplacian, pm.blur_tenengrad, pm.blur_roi,
        pm.burst_id, pm.is_burst_candidate, pm.burst_neighbors
    FROM media m
    LEFT JOIN photo_metadata pm ON m.id = pm.media_id
    WHERE (m.folder LIKE ?)
      AND m.is_available = 1
    ORDER BY m.filename
    LIMIT 10
"""

cursor.execute(query, (f"{folder}%",))
rows = cursor.fetchall()

print(f"\nFound {len(rows)} rows\n")

for i, row in enumerate(rows[:5]):
    r = dict(row)
    print(f"{i+1}. {r['filename']}")
    print(f"   m.rating: {r['rating']}")
    print(f"   m.color:  {r['color']}")
    print(f"   pm.blur:  {r['blur_laplacian']}")
    print()

# Check if ANY photos have rating/color
cursor.execute("SELECT COUNT(*) as count FROM media WHERE rating > 0")
rated_count = cursor.fetchone()['count']

cursor.execute("SELECT COUNT(*) as count FROM media WHERE color IS NOT NULL")
colored_count = cursor.fetchone()['count']

print(f"Total in DB:")
print(f"  With rating: {rated_count}")
print(f"  With color:  {colored_count}")

if colored_count > 0:
    cursor.execute("SELECT filename, rating, color FROM media WHERE color IS NOT NULL LIMIT 5")
    print(f"\nSample colored photos:")
    for row in cursor.fetchall():
        print(f"  - {row['filename']}: rating={row['rating']}, color={row['color']}")

conn.close()
