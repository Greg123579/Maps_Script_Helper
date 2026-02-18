"""
Database models for Maps Python Script Helper
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())


class User(Base):
    """User model. Passwords are stored only as one-way hashes (never plain text)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)  # Used as username for login
    email = Column(String(255), nullable=True, index=True)  # For password reset; optional for legacy
    password_hash = Column(String(255), nullable=True)  # bcrypt hash; null only for legacy accounts
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    settings = Column(JSON, default=dict)  # For future user preferences

    # Relationships
    scripts = relationship("UserScript", back_populates="user", cascade="all, delete-orphan")
    images = relationship("UserImage", back_populates="user", cascade="all, delete-orphan")
    executions = relationship("ExecutionSession", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        d = {
            "id": self.id,
            "name": self.name,
            "email": self.email,  # Optional; used for password reset
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "settings": self.settings or {}
        }
        # Never expose password_hash
        return d


class PasswordResetToken(Base):
    """Token for password reset. Expires after use or timeout."""
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    token = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)

    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at and datetime.utcnow() < self.expires_at


class UserScript(Base):
    """User-created script model"""
    __tablename__ = "user_scripts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, default="")
    code = Column(Text, nullable=False)
    script_parameters = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_favorite = Column(Boolean, default=False)
    is_user_created = Column(Boolean, default=True)
    
    # Community sharing fields
    is_community = Column(Boolean, default=False, index=True)
    community_image_id = Column(String(36), nullable=True)   # ID of the linked image (library or user-uploaded)
    community_image_url = Column(String(500), nullable=True)  # Cached URL for quick access
    community_image_name = Column(String(255), nullable=True) # Cached image name for display
    
    # Relationships
    user = relationship("User", back_populates="scripts")
    executions = relationship("ExecutionSession", back_populates="script")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description or "",
            "code": self.code,
            "script_parameters": self.script_parameters or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_favorite": self.is_favorite,
            "is_user_created": self.is_user_created,
            "is_community": self.is_community or False,
            "community_image_id": self.community_image_id,
            "community_image_url": self.community_image_url,
            "community_image_thumbnail_url": f"{self.community_image_url}?thumbnail=true" if self.community_image_url else None,
            "community_image_name": self.community_image_name,
        }


class LibraryScript(Base):
    """Library/example script model"""
    __tablename__ = "library_scripts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)  # For reference/display
    description = Column(Text, default="")
    code = Column(Text, nullable=False)  # Actual script code
    category = Column(String(100), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tags = Column(JSON, default=list)  # For searchability
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "filename": self.filename,
            "description": self.description or "",
            "code": self.code,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags or []
        }


class LibraryImage(Base):
    """Shared library/example image model (no user ownership)"""
    __tablename__ = "library_images"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)  # Points to library/images/{filename}
    description = Column(Text, default="")
    image_type = Column(String(50), index=True)  # SEM, SDB, TEM, OPTICAL
    category = Column(String(100), index=True)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)  # In bytes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tags = Column(JSON, default=list)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "filename": self.filename,
            "description": self.description or "",
            "type": self.image_type,
            "category": self.category,
            "url": f"/library/images/{self.filename}",
            "thumbnail_url": f"/library/images/{self.filename}?thumbnail=true",
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags or []
        }


class UserImage(Base):
    """User-uploaded image model"""
    __tablename__ = "user_images"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)  # Points to assets/uploads/{filename}
    description = Column(Text, default="")
    image_type = Column(String(50), index=True)  # SEM, SDB, TEM, OPTICAL
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)  # In bytes
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_global = Column(Boolean, default=False, index=True)  # Shared with all users
    
    # Relationships
    user = relationship("User", back_populates="images")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "filename": self.filename,
            "description": self.description or "",
            "type": self.image_type,
            "url": f"/uploads/images/{self.filename}",
            "thumbnail_url": f"/uploads/images/{self.filename}?thumbnail=true",
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "is_global": self.is_global or False
        }


class ScriptRating(Base):
    """Rating for a community script (1-5 stars, one per user per script)"""
    __tablename__ = "script_ratings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(36), ForeignKey("user_scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "script_id": self.script_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ExecutionSession(Base):
    """Script execution session model for analytics"""
    __tablename__ = "execution_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    script_id = Column(String(36), ForeignKey("user_scripts.id", ondelete="SET NULL"), nullable=True, index=True)
    script_name = Column(String(255))  # Store name in case script is deleted
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    status = Column(String(50), index=True)  # success, error, timeout, running
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="executions")
    script = relationship("UserScript", back_populates="executions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "script_id": self.script_id,
            "script_name": self.script_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error_message": self.error_message
        }
