import sqlite3
conn = sqlite3.connect('db/workspace_media.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT id, path, rating, color, keywords FROM media LIMIT 5')
for row in cursor.fetchall():
    print(dict(row))
conn.close()
