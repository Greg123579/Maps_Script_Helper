"""Quick database verification script. Run from project root."""
import sys
import pathlib
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from backend.database import get_db_session
from backend.models import User, UserScript, LibraryImage

with get_db_session() as db:
    users = db.query(User).all()
    scripts = db.query(UserScript).all()
    images = db.query(LibraryImage).all()
    
    print("=" * 50)
    print("Database Verification")
    print("=" * 50)
    print(f"✓ {len(users)} users")
    print(f"✓ {len(scripts)} user scripts")
    print(f"✓ {len(images)} library images")
    print()
    
    print("Users:")
    for u in users:
        print(f"  - {u.name} (ID: {u.id})")
    
    print()
    print("User Scripts:")
    for s in scripts:
        print(f"  - {s.name} (by user {s.user_id})")
    
    print()
    print("=" * 50)
    print("✓ Database is working correctly!")
    print("=" * 50)
