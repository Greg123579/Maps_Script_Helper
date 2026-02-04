"""
Migration script to import existing JSON data into SQLite database

Run this script to migrate:
- users.json → users table
- user_scripts/*.json → user_scripts table
- library/metadata.json → library_images table
"""
import json
import pathlib
import sys
from datetime import datetime
from PIL import Image

# Add backend to path
sys.path.insert(0, str(pathlib.Path(__file__).parent / "backend"))

from backend.database import get_db_session, init_database
from backend.models import User, UserScript, LibraryImage, UserImage

BASE_DIR = pathlib.Path(__file__).parent
USERS_FILE = BASE_DIR / "users.json"
USER_SCRIPTS_DIR = BASE_DIR / "user_scripts"
LIBRARY_METADATA_FILE = BASE_DIR / "library" / "metadata.json"
LIBRARY_IMAGES_DIR = BASE_DIR / "library" / "images"


def parse_datetime(dt_str):
    """Parse datetime string with multiple formats"""
    if not dt_str:
        return datetime.utcnow()
    
    # Try ISO format first
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        pass
    
    # Try common formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except:
            continue
    
    # Default to current time if parsing fails
    return datetime.utcnow()


def migrate_users():
    """Migrate users from users.json to database"""
    if not USERS_FILE.exists():
        print("⚠ No users.json found, skipping user migration")
        return {}
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
    except Exception as e:
        print(f"✗ Error reading users.json: {e}")
        return {}
    
    user_id_map = {}  # Map old ID to new ID
    
    with get_db_session() as db:
        migrated_count = 0
        for user_id, user_data in users_data.items():
            try:
                # Check if user already exists by name
                existing = db.query(User).filter(User.name == user_data.get("name")).first()
                if existing:
                    print(f"  ⤳ User '{user_data.get('name')}' already exists, using existing ID")
                    user_id_map[user_id] = existing.id
                    continue
                
                new_user = User(
                    id=user_id,  # Preserve original ID
                    name=user_data.get("name", "Unknown"),
                    created_at=parse_datetime(user_data.get("created_at")),
                    settings=user_data.get("settings", {})
                )
                db.add(new_user)
                user_id_map[user_id] = new_user.id
                migrated_count += 1
                print(f"  ✓ Migrated user: {new_user.name}")
            except Exception as e:
                print(f"  ✗ Error migrating user {user_id}: {e}")
        
        db.commit()
        print(f"✓ Migrated {migrated_count} users")
    
    return user_id_map


def migrate_user_scripts(user_id_map):
    """Migrate user scripts from user_scripts/*.json to database"""
    if not USER_SCRIPTS_DIR.exists():
        print("⚠ No user_scripts directory found, skipping script migration")
        return
    
    with get_db_session() as db:
        migrated_count = 0
        skipped_count = 0
        
        for script_file in USER_SCRIPTS_DIR.glob("*.json"):
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
                
                script_id = script_data.get("id")
                user_id = script_data.get("user_id")
                
                # Skip if no user_id or user doesn't exist
                if not user_id:
                    print(f"  ⤳ Skipping script without user_id: {script_data.get('name')}")
                    skipped_count += 1
                    continue
                
                # Map to new user ID if needed
                mapped_user_id = user_id_map.get(user_id, user_id)
                
                # Verify user exists
                user_exists = db.query(User).filter(User.id == mapped_user_id).first()
                if not user_exists:
                    print(f"  ⤳ Skipping script for non-existent user: {script_data.get('name')}")
                    skipped_count += 1
                    continue
                
                # Check if script already exists
                existing = db.query(UserScript).filter(UserScript.id == script_id).first()
                if existing:
                    print(f"  ⤳ Script already exists: {script_data.get('name')}")
                    continue
                
                new_script = UserScript(
                    id=script_id,  # Preserve original ID
                    user_id=mapped_user_id,
                    name=script_data.get("name", "Untitled"),
                    description=script_data.get("description", ""),
                    code=script_data.get("code", ""),
                    created_at=parse_datetime(script_data.get("created_at")),
                    updated_at=parse_datetime(script_data.get("updated_at")),
                    is_favorite=script_data.get("is_favorite", False),
                    is_user_created=script_data.get("is_user_created", True)
                )
                db.add(new_script)
                migrated_count += 1
                print(f"  ✓ Migrated script: {new_script.name}")
            except Exception as e:
                print(f"  ✗ Error migrating script {script_file}: {e}")
        
        db.commit()
        print(f"✓ Migrated {migrated_count} user scripts ({skipped_count} skipped)")


def migrate_library_images():
    """Migrate images from library/metadata.json to database
    - Images without user_id -> LibraryImage (shared)
    - Images with user_id -> UserImage (per-user)
    """
    if not LIBRARY_METADATA_FILE.exists():
        print("⚠ No library metadata.json found, skipping image migration")
        return
    
    try:
        with open(LIBRARY_METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"✗ Error reading library metadata.json: {e}")
        return
    
    with get_db_session() as db:
        library_count = 0
        user_count = 0
        
        for image_id, image_data in metadata.items():
            try:
                filename = image_data.get("filename", "")
                image_path = LIBRARY_IMAGES_DIR / filename
                
                # Get image dimensions if file exists
                width, height, file_size = None, None, None
                if image_path.exists():
                    try:
                        with Image.open(image_path) as img:
                            width, height = img.size
                        file_size = image_path.stat().st_size
                    except:
                        pass
                
                user_id = image_data.get("user_id")
                
                if user_id:
                    # User-uploaded image - check if already exists
                    existing = db.query(UserImage).filter(UserImage.id == image_id).first()
                    if existing:
                        continue
                    
                    new_image = UserImage(
                        id=image_id,
                        user_id=user_id,
                        name=image_data.get("name", filename),
                        filename=filename,
                        description=image_data.get("description", ""),
                        image_type=image_data.get("type", "SEM"),
                        width=width,
                        height=height,
                        file_size=file_size,
                        uploaded_at=parse_datetime(image_data.get("uploaded_at"))
                    )
                    db.add(new_image)
                    user_count += 1
                    print(f"  ✓ Migrated user image: {new_image.name} (user: {user_id[:8]}...)")
                else:
                    # Shared library image - check if already exists
                    existing = db.query(LibraryImage).filter(LibraryImage.id == image_id).first()
                    if existing:
                        continue
                    
                    new_image = LibraryImage(
                        id=image_id,
                        name=image_data.get("name", filename),
                        filename=filename,
                        description=image_data.get("description", ""),
                        category=image_data.get("type", "default"),
                        width=width,
                        height=height,
                        file_size=file_size,
                        created_at=parse_datetime(image_data.get("created_at") or image_data.get("uploaded_at")),
                        tags=image_data.get("tags", [])
                    )
                    db.add(new_image)
                    library_count += 1
                    print(f"  ✓ Migrated library image: {new_image.name}")
            except Exception as e:
                print(f"  ✗ Error migrating image {image_id}: {e}")
        
        db.commit()
        print(f"✓ Migrated {library_count} library images + {user_count} user images")


def main():
    """Run the migration"""
    print("=" * 70)
    print("  Maps Python Script Helper - Data Migration to SQLite")
    print("=" * 70)
    print()
    
    # Initialize database (creates tables if they don't exist)
    print("Initializing database...")
    init_database()
    print()
    
    # Migrate users first (needed for foreign key relationships)
    print("Migrating users...")
    user_id_map = migrate_users()
    print()
    
    # Migrate user scripts
    print("Migrating user scripts...")
    migrate_user_scripts(user_id_map)
    print()
    
    # Migrate library images
    print("Migrating library images...")
    migrate_library_images()
    print()
    
    print("=" * 70)
    print("  Migration Complete!")
    print("=" * 70)
    print()
    print("✓ Your data has been migrated to SQLite database")
    print(f"✓ Database location: {BASE_DIR / 'maps_helper.db'}")
    print()
    print("Next steps:")
    print("  1. Test the application to ensure everything works")
    print("  2. Backup the original JSON files if migration successful")
    print("  3. Consider removing old JSON files after verification")
    print()


if __name__ == "__main__":
    main()
