import sqlite3
conn = sqlite3.connect('db/workspace_media.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check metadata including burst info
cursor.execute('''
    SELECT m.filename, m.rating, m.color, m.keywords, 
           pm.blur_laplacian, pm.burst_id, pm.is_burst_candidate, pm.burst_neighbors
    FROM media m
    LEFT JOIN photo_metadata pm ON m.id = pm.media_id
    WHERE m.media_type = 'photo'
    LIMIT 10
''')

print("Sample photos with metadata:")
print("-" * 120)
for row in cursor.fetchall():
    r = dict(row)
    color = r['color'] if r['color'] else 'None'
    blur = f"{r['blur_laplacian']:.2f}" if r['blur_laplacian'] else 'None'
    burst_id = r['burst_id'] if r['burst_id'] else 'None'
    burst_cand = 'YES' if r['is_burst_candidate'] else 'NO'
    burst_neighbors = r['burst_neighbors'] if r['burst_neighbors'] else 'None'
    print(f"{r['filename']:20} | Rating: {r['rating']} | Color: {color:8} | Blur: {blur:8} | Burst: {burst_id:15} | Cand: {burst_cand} | Neighbors: {burst_neighbors[:40] if burst_neighbors != 'None' else 'None'}")

# Stats
cursor.execute("SELECT COUNT(*) as rated FROM media WHERE rating > 0")
rated = cursor.fetchone()['rated']

cursor.execute("SELECT COUNT(*) as colored FROM media WHERE color IS NOT NULL")
colored = cursor.fetchone()['colored']

cursor.execute("SELECT COUNT(*) as total FROM media WHERE media_type = 'photo'")
total = cursor.fetchone()['total']

cursor.execute("SELECT COUNT(*) as burst FROM photo_metadata WHERE burst_id IS NOT NULL")
burst = cursor.fetchone()['burst']

cursor.execute("SELECT COUNT(*) as burst_cand FROM photo_metadata WHERE is_burst_candidate = 1")
burst_cand = cursor.fetchone()['burst_cand']

print("\n" + "=" * 120)
print(f"Total photos:        {total}")
print(f"With rating:         {rated}")
print(f"With color:          {colored}")
print(f"With burst_id:       {burst}")
print(f"Burst candidates:    {burst_cand}")

conn.close()
