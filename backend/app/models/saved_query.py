"""
Saved Query Model

Saved search queries for reuse and history.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class SavedQuery(Base):
    """Saved search query within a workspace."""
    
    __tablename__ = "saved_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    
    # Query details
    name = Column(String(255), nullable=True)
    raw_query = Column(Text, nullable=False)
    parsed_query = Column(JSONB, nullable=True)  # Structured query data
    
    # Settings used
    settings_snapshot = Column(JSONB, nullable=True)  # Settings at time of query
    
    # Results reference
    result_count = Column(Integer, nullable=True)
    papers_found = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Array of paper IDs
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="saved_queries")
    
    def __repr__(self):
        return f"<SavedQuery {self.name or self.raw_query[:30]}>"
