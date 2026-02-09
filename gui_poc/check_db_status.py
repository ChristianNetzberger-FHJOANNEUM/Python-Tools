"""Quick check of database migration status"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'db' / 'workspace_media.db'

if not db_path.exists():
    print("❌ Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Count total items
cursor.execute("SELECT COUNT(*) as count FROM media")
total = cursor.fetchone()['count']

# Count by folder
cursor.execute("""
    SELECT 
        folder,
        COUNT(*) as count,
        SUM(CASE WHEN media_type = 'photo' THEN 1 ELSE 0 END) as photos
    FROM media
    GROUP BY folder
    ORDER BY folder
""")

print("\n" + "="*60)
print("DATABASE STATUS")
print("="*60)
print(f"Total items in database: {total}\n")

if total > 0:
    print("Items by folder:")
    for row in cursor.fetchall():
        print(f"  {row['folder']}")
        print(f"    Total: {row['count']}, Photos: {row['photos']}")
else:
    print("⚠️ Database is empty")

conn.close()

print("\n" + "="*60)
if total > 1000:
    print("✅ Migration is working! Database has data.")
    print("   Restart server to enable SQLite fast path.")
else:
    print("⚠️ Migration still in progress or incomplete.")
