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
        return
    
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


# Initialize database on import
ensure_database()
