"""
Workspace Model

User workspaces for organizing research projects.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Workspace(Base):
    """Workspace model for organizing research projects."""
    
    __tablename__ = "workspaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color for UI
    icon = Column(String(50), nullable=True)  # Icon identifier
    
    # Settings (workspace-level overrides)
    settings = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete
    archived_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="workspaces")
    collections = relationship("Collection", back_populates="workspace", cascade="all, delete-orphan")
    saved_queries = relationship("SavedQuery", back_populates="workspace", cascade="all, delete-orphan")
    synthesis_results = relationship("SynthesisResult", back_populates="workspace", cascade="all, delete-orphan")
    research_sessions = relationship("ResearchSession", back_populates="workspace", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workspace {self.name}>"
