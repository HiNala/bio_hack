"""
Collection Model

Paper collections for organizing research materials.
"""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class Collection(Base):
    """Collection of papers within a workspace."""
    
    __tablename__ = "collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    
    # Identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    
    # Type
    type = Column(String(50), default="manual")  # 'manual', 'smart', 'auto'
    
    # Smart collection rules (for auto-updating collections)
    smart_rules = Column(JSONB, nullable=True)  # e.g., {"min_citations": 10, "year_from": 2020}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="collections")
    papers = relationship("CollectionPaper", back_populates="collection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Collection {self.name}>"


class CollectionPaper(Base):
    """Junction table for collection-paper relationships with metadata."""
    
    __tablename__ = "collection_papers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    
    # User additions
    user_notes = Column(Text, nullable=True)
    user_tags = Column(ARRAY(String), default=[])
    user_rating = Column(Integer, nullable=True)
    read_status = Column(String(20), default="unread")  # 'unread', 'reading', 'read'
    
    # Metadata
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(String(50), default="user")  # 'user', 'query', 'recommendation'
    
    # Constraints
    __table_args__ = (
        CheckConstraint('user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)', name='check_rating_range'),
    )
    
    # Relationships
    collection = relationship("Collection", back_populates="papers")
    paper = relationship("Paper")
    
    def __repr__(self):
        return f"<CollectionPaper {self.collection_id}:{self.paper_id}>"
