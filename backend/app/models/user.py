"""
User Model

User accounts for ScienceRAG workspaces and personalization.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identity
    email = Column(String(255), unique=True, nullable=True)
    name = Column(String(255), nullable=True)
    
    # Authentication (simple for hackathon - can be extended)
    auth_provider = Column(String(50), default="anonymous")  # 'anonymous', 'email', 'google'
    auth_id = Column(String(255), nullable=True)  # External auth ID
    
    # Profile
    institution = Column(String(255), nullable=True)
    role = Column(String(100), nullable=True)  # 'researcher', 'student', 'professional'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspaces = relationship("Workspace", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email or self.id}>"
