"""
User Schemas

Pydantic schemas for user-related API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema."""
    email: Optional[str] = None
    name: Optional[str] = None
    institution: Optional[str] = None
    role: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    auth_provider: str = "anonymous"
    created_at: datetime
    last_active_at: datetime
    
    class Config:
        from_attributes = True


class WorkspaceBase(BaseModel):
    """Base workspace schema."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a workspace."""
    pass


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceResponse(WorkspaceBase):
    """Schema for workspace response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CollectionBase(BaseModel):
    """Base collection schema."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


class CollectionCreate(CollectionBase):
    """Schema for creating a collection."""
    type: str = "manual"
    smart_rules: Optional[dict] = None


class CollectionUpdate(BaseModel):
    """Schema for updating a collection."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    smart_rules: Optional[dict] = None


class CollectionResponse(CollectionBase):
    """Schema for collection response."""
    id: UUID
    workspace_id: UUID
    type: str
    smart_rules: Optional[dict] = None
    paper_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CollectionPaperAdd(BaseModel):
    """Schema for adding a paper to a collection."""
    paper_id: UUID
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CollectionPaperUpdate(BaseModel):
    """Schema for updating a paper in a collection."""
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    read_status: Optional[str] = None


class CollectionPaperResponse(BaseModel):
    """Schema for collection paper response."""
    id: UUID
    collection_id: UUID
    paper_id: UUID
    user_notes: Optional[str] = None
    user_tags: List[str] = []
    user_rating: Optional[int] = None
    read_status: str = "unread"
    added_at: datetime
    added_by: str = "user"
    
    # Paper details
    paper_title: Optional[str] = None
    paper_authors: Optional[List[str]] = None
    paper_year: Optional[int] = None
    paper_venue: Optional[str] = None
    citation_count: Optional[int] = None
    
    class Config:
        from_attributes = True
