"""
Database connection and session management for Maps Python Script Helper
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os
import pathlib

try:
    from backend.models import Base
except ImportError:
    from models import Base

# Database configuration
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "maps_helper.db"
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


# Initialize database on import
if not DATABASE_PATH.exists():
    print("[Database] Database file not found, creating new database")
    init_database()
else:
    print(f"[Database] Using existing database at: {DATABASE_PATH}")
