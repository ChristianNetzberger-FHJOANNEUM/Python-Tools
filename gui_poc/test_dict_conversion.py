import sqlite3
from pathlib import Path

db_path = Path("db/workspace_media.db")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row  # ← IMPORTANT!
cursor = conn.cursor()

folder = "E:\\Lumix-2026-01\\101_PANA"
query = f"""
    SELECT 
        m.id, m.path, m.filename, m.rating, m.color,
        pm.blur_laplacian
    FROM media m
    LEFT JOIN photo_metadata pm ON m.id = pm.media_id
    WHERE m.folder LIKE ?
      AND m.color IS NOT NULL
    LIMIT 5
"""

cursor.execute(query, (f"{folder}%",))

print("=" * 80)
print("COLORED PHOTOS - Dict Conversion Test")
print("=" * 80)

for row in cursor.fetchall():
    media_dict = dict(row)
    print(f"\nFilename: {media_dict['filename']}")
    print(f"  Dict keys: {list(media_dict.keys())}")
    print(f"  rating: {media_dict.get('rating', 'KEY MISSING!')}")
    print(f"  color:  {media_dict.get('color', 'KEY MISSING!')}")
    print(f"  blur:   {media_dict.get('blur_laplacian', 'KEY MISSING!')}")

conn.close()
