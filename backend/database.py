"""
Database connection and session management for Maps Python Script Helper
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os
import shutil
import pathlib

try:
    from backend.models import Base
except ImportError:
    from models import Base

# Database configuration
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
# Allow DATABASE_PATH to be configured via environment variable (e.g., for PVC storage on AWS)
# Defaults to project root (maps_helper.db) for local/Docker Desktop development
DATABASE_PATH = pathlib.Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "maps_helper.db")))

# Path to the bundled (pre-populated) database baked into the Docker image
# This is the DB committed to the repo at backend/maps_helper.db,
# which the Dockerfile moves to /app/maps_helper.db
BUNDLED_DB_PATH = BASE_DIR / "maps_helper.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine with SQLite-specific optimizations
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multiple threads (FastAPI)
        "timeout": 30  # 30 second timeout for locks
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize the database, creating all tables"""
    print(f"[Database] Initializing database at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    print("[Database] ✓ Database initialized successfully")


def migrate_add_password_hash():
    """Add password_hash column to users table if missing (one-way migration)."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            conn.commit()
        print("[Database] ✓ Added password_hash column to users")
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "already exists" in msg:
            pass  # Column already there
        else:
            print(f"[Database] Note: migrate_add_password_hash: {e}")


def migrate_add_community_fields():
    """Add community sharing columns to user_scripts table if missing."""
    from sqlalchemy import text
    columns = [
        ("is_community", "BOOLEAN DEFAULT 0"),
        ("community_image_id", "VARCHAR(36)"),
        ("community_image_url", "VARCHAR(500)"),
        ("community_image_name", "VARCHAR(255)"),
    ]
    for col_name, col_type in columns:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE user_scripts ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            print(f"[Database] ✓ Added {col_name} column to user_scripts")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate" in msg or "already exists" in msg:
                pass
            else:
                print(f"[Database] Note: migrate_add_community_fields ({col_name}): {e}")


def migrate_add_global_image_field():
    """Add is_global column to user_images table if missing."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE user_images ADD COLUMN is_global BOOLEAN DEFAULT 0"))
            conn.commit()
        print("[Database] ✓ Added is_global column to user_images")
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "already exists" in msg:
            pass
        else:
            print(f"[Database] Note: migrate_add_global_image_field: {e}")


def migrate_add_user_email_display_name():
    """Add email column to users table if missing."""
    from sqlalchemy import text
    for col_name, col_type in [("email", "VARCHAR(255)")]:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            print(f"[Database] ✓ Added {col_name} column to users")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate" in msg or "already exists" in msg:
                pass
            else:
                print(f"[Database] Note: migrate_add_user_email_display_name ({col_name}): {e}")


def migrate_create_password_reset_tokens():
    """Create password_reset_tokens table if it doesn't exist."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id VARCHAR(36) PRIMARY KEY,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at DATETIME NOT NULL,
                    used_at DATETIME
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_token ON password_reset_tokens (token)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens (user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_expires_at ON password_reset_tokens (expires_at)"))
            conn.commit()
        print("[Database] ✓ Ensured password_reset_tokens table exists")
    except Exception as e:
        print(f"[Database] Note: migrate_create_password_reset_tokens: {e}")


def migrate_create_script_ratings():
    """Create script_ratings table if it doesn't exist."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS script_ratings (
                    id VARCHAR(36) PRIMARY KEY,
                    script_id VARCHAR(36) NOT NULL REFERENCES user_scripts(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    rating INTEGER NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_script_ratings_user_script
                ON script_ratings (script_id, user_id)
            """))
            conn.commit()
        print("[Database] ✓ Ensured script_ratings table exists")
    except Exception as e:
        print(f"[Database] Note: migrate_create_script_ratings: {e}")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints to get database session.
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database session.
    Usage:
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """Drop all tables and recreate them (for testing/development)"""
    print("[Database] WARNING: Resetting database (dropping all tables)")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[Database] ✓ Database reset complete")


def ensure_database():
    """
    Ensure the database file exists at DATABASE_PATH.
    
    Strategy:
    1. If DATABASE_PATH already exists → use it (PVC already has data)
    2. If DATABASE_PATH doesn't exist but BUNDLED_DB_PATH does → copy bundled DB
       (first deploy to PVC: copy the pre-populated DB from the Docker image)
    3. If neither exists → create a fresh empty database
       (auto_seed in app.py will populate it from seed_library_scripts.py)
    """
    if DATABASE_PATH.exists():
        print(f"[Database] Using existing database at: {DATABASE_PATH}")
    else:
        # Ensure the parent directory exists (e.g., /deploy/)
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Check if we have a bundled DB to copy (only when DATABASE_PATH != BUNDLED_DB_PATH)
        if DATABASE_PATH != BUNDLED_DB_PATH and BUNDLED_DB_PATH.exists():
            print(f"[Database] Copying bundled database from {BUNDLED_DB_PATH} to {DATABASE_PATH}")
            shutil.copy2(str(BUNDLED_DB_PATH), str(DATABASE_PATH))
            print("[Database] ✓ Bundled database copied to PVC successfully")
        else:
            print("[Database] No existing database found, creating new database")
            init_database()
    # Always run schema migrations for existing databases
    migrate_add_password_hash()
    migrate_add_community_fields()
    migrate_add_global_image_field()
    migrate_create_script_ratings()
    migrate_add_user_email_display_name()
    migrate_create_password_reset_tokens()


# Initialize database on import
ensure_database()
