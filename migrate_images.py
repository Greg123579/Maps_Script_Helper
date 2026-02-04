"""Migrate images from metadata.json to database"""
import json
import sys
import pathlib
from PIL import Image as PILImage

sys.path.insert(0, str(pathlib.Path(__file__).parent / "backend"))

from backend.database import get_db_session
from backend.models import LibraryImage, UserImage
from datetime import datetime

LIBRARY_IMAGES_DIR = pathlib.Path(__file__).parent / "library" / "images"
METADATA_FILE = pathlib.Path(__file__).parent / "library" / "metadata.json"

def migrate_images():
    print("=" * 60)
    print("Migrating Images to Database")
    print("=" * 60)
    print()
    
    # Load metadata
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    print(f"Found {len(metadata)} images in metadata.json\n")
    
    with get_db_session() as db:
        library_count = 0
        user_count = 0
        
        for image_id, image_data in metadata.items():
            filename = image_data.get("filename", "")
            image_path = LIBRARY_IMAGES_DIR / filename
            
            # Get image dimensions if file exists
            width, height, file_size = None, None, None
            if image_path.exists():
                try:
                    with PILImage.open(image_path) as img:
                        width, height = img.size
                    file_size = image_path.stat().st_size
                except:
                    pass
            else:
                print(f"  ⚠ Image file not found: {filename}")
            
            user_id = image_data.get("user_id")
            
            if user_id:
                # Check if exists
                existing = db.query(UserImage).filter(UserImage.id == image_id).first()
                if existing:
                    print(f"  ⤳ Skipping user image (exists): {image_data.get('name')}")
                    continue
                
                # Create UserImage
                uploaded_at = datetime.fromtimestamp(float(image_data.get("uploaded_at", 0)))
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
                    uploaded_at=uploaded_at
                )
                db.add(new_image)
                user_count += 1
                print(f"  ✓ User image: {new_image.name} (user: {user_id[:8]}...)")
            else:
                # Check if exists
                existing = db.query(LibraryImage).filter(LibraryImage.id == image_id).first()
                if existing:
                    print(f"  ⤳ Skipping library image (exists): {image_data.get('name')}")
                    continue
                
                # Create LibraryImage
                created_at = None
                if "uploaded_at" in image_data:
                    created_at = datetime.fromtimestamp(float(image_data.get("uploaded_at")))
                
                new_image = LibraryImage(
                    id=image_id,
                    name=image_data.get("name", filename),
                    filename=filename,
                    description=image_data.get("description", ""),
                    image_type=image_data.get("type", "SEM"),
                    category=image_data.get("type", "default"),
                    width=width,
                    height=height,
                    file_size=file_size,
                    created_at=created_at or datetime.utcnow()
                )
                db.add(new_image)
                library_count += 1
                print(f"  ✓ Library image: {new_image.name}")
        
        db.commit()
        
        print()
        print("=" * 60)
        print(f"✓ Migrated {library_count} library images + {user_count} user images")
        print("=" * 60)

if __name__ == "__main__":
    migrate_images()
