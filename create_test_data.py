"""Create test data directly in database"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent / "backend"))

from backend.database import get_db_session
from backend.models import User

def create_test_users():
    print("Creating test users...")
    
    with get_db_session() as db:
        # Check if users already exist
        existing_count = db.query(User).count()
        if existing_count > 0:
            print(f"✓ Database already has {existing_count} users")
            return
        
        # Create test users
        users = [
            User(name="Greg"),
            User(name="Todd"),
            User(name="Test User")
        ]
        
        for user in users:
            db.add(user)
            print(f"  ✓ Created user: {user.name}")
        
        db.commit()
        print(f"✓ Created {len(users)} test users")

if __name__ == "__main__":
    create_test_users()
