import json
import sqlite3

conn = sqlite3.connect('maps_helper.db')
metadata = json.load(open('library/metadata.json'))
cur = conn.cursor()

updated = 0
for image_id, data in metadata.items():
    if not data.get('user_id'):
        img_type = data.get('type', 'SEM')
        cur.execute('UPDATE library_images SET image_type = ? WHERE id = ?', (img_type, image_id))
        updated += 1
        print(f'Updated {data.get("name")}: {img_type}')

conn.commit()
print(f'\n✓ Updated {updated} library images with image_type')
