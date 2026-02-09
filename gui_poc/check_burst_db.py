"""Check burst data in database"""
import sqlite3
from pathlib import Path
import json

db_path = Path(__file__).parent / 'db' / 'workspace_media.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n=== BURST DATA DIAGNOSIS ===\n")

# Count photos with burst data
cursor.execute("""
    SELECT 
        COUNT(*) as total_photos,
        SUM(CASE WHEN pm.burst_id IS NOT NULL THEN 1 ELSE 0 END) as photos_with_burst_id,
        COUNT(DISTINCT pm.burst_id) as unique_burst_ids
    FROM media m
    LEFT JOIN photo_metadata pm ON m.id = pm.media_id
    WHERE m.media_type = 'photo' AND m.folder LIKE '%101_PANA%'
""")

row = cursor.fetchone()
print(f"Folder 101_PANA:")
print(f"  Total photos: {row['total_photos']}")
print(f"  Photos with burst_id: {row['photos_with_burst_id']}")
print(f"  Unique burst_ids: {row['unique_burst_ids']}")
print(f"  Expected ratio: photos > unique_burst_ids")
print(f"  Actual ratio: {row['photos_with_burst_id'] / max(row['unique_burst_ids'], 1):.2f} photos per burst\n")

if row['photos_with_burst_id'] == row['unique_burst_ids']:
    print("❌ PROBLEM: Every photo has a UNIQUE burst_id (should share IDs in groups!)\n")
else:
    print("✅ GOOD: Photos are sharing burst_ids\n")

# Sample a few burst_ids to see the data
cursor.execute("""
    SELECT 
        m.filename,
        pm.burst_id,
        pm.burst_neighbors,
        pm.is_burst_candidate
    FROM media m
    JOIN photo_metadata pm ON m.id = pm.media_id
    WHERE m.folder LIKE '%101_PANA%' AND pm.burst_id IS NOT NULL
    LIMIT 5
""")

print("Sample burst data from database:")
for row in cursor.fetchall():
    neighbors = json.loads(row['burst_neighbors']) if row['burst_neighbors'] else []
    print(f"\n  {row['filename']}")
    print(f"    burst_id: {row['burst_id']}")
    print(f"    is_burst_candidate: {row['is_burst_candidate']}")
    print(f"    neighbors count: {len(neighbors)}")
    if neighbors:
        print(f"    neighbors: {neighbors[:2]}...")  # Show first 2

conn.close()
