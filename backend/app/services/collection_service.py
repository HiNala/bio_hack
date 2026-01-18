"""
Collection Service

Manages paper collections and workspaces.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.models.workspace import Workspace
from app.models.collection import Collection, CollectionPaper
from app.models.paper import Paper
from app.schemas.user import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    CollectionCreate, CollectionUpdate, CollectionResponse,
    CollectionPaperAdd, CollectionPaperUpdate, CollectionPaperResponse,
)


class CollectionService:
    """Manage workspaces and paper collections."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== Workspace Methods ====================
    
    async def create_workspace(
        self,
        user_id: str,
        data: WorkspaceCreate
    ) -> WorkspaceResponse:
        """Create a new workspace for a user."""
        workspace = Workspace(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
        )
        
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        
        return WorkspaceResponse.model_validate(workspace)
    
    async def get_workspace(self, workspace_id: str) -> Optional[WorkspaceResponse]:
        """Get a workspace by ID."""
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
        )
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            return None
        
        return WorkspaceResponse.model_validate(workspace)
    
    async def get_user_workspaces(self, user_id: str) -> List[WorkspaceResponse]:
        """Get all workspaces for a user."""
        result = await self.db.execute(
            select(Workspace)
            .where(Workspace.user_id == uuid.UUID(user_id))
            .where(Workspace.archived_at.is_(None))
            .order_by(Workspace.updated_at.desc())
        )
        workspaces = result.scalars().all()
        
        return [WorkspaceResponse.model_validate(w) for w in workspaces]
    
    async def update_workspace(
        self,
        workspace_id: str,
        data: WorkspaceUpdate
    ) -> Optional[WorkspaceResponse]:
        """Update a workspace."""
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
        )
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            return None
        
        if data.name is not None:
            workspace.name = data.name
        if data.description is not None:
            workspace.description = data.description
        if data.color is not None:
            workspace.color = data.color
        if data.icon is not None:
            workspace.icon = data.icon
        
        workspace.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(workspace)
        
        return WorkspaceResponse.model_validate(workspace)
    
    async def archive_workspace(self, workspace_id: str) -> bool:
        """Archive a workspace (soft delete)."""
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
        )
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            return False
        
        workspace.archived_at = datetime.utcnow()
        await self.db.commit()
        
        return True
    
    async def get_or_create_default_workspace(self, user_id: str) -> WorkspaceResponse:
        """Get or create a default workspace for the user."""
        workspaces = await self.get_user_workspaces(user_id)
        
        if workspaces:
            return workspaces[0]
        
        # Create default workspace
        return await self.create_workspace(
            user_id,
            WorkspaceCreate(
                name="My Research",
                description="Default research workspace",
                color="#3B82F6",
                icon="flask"
            )
        )
    
    # ==================== Collection Methods ====================
    
    async def create_collection(
        self,
        workspace_id: str,
        data: CollectionCreate
    ) -> CollectionResponse:
        """Create a new collection in a workspace."""
        collection = Collection(
            id=uuid.uuid4(),
            workspace_id=uuid.UUID(workspace_id),
            name=data.name,
            description=data.description,
            color=data.color,
            type=data.type,
            smart_rules=data.smart_rules,
        )
        
        self.db.add(collection)
        await self.db.commit()
        await self.db.refresh(collection)
        
        return CollectionResponse(
            id=collection.id,
            workspace_id=collection.workspace_id,
            name=collection.name,
            description=collection.description,
            color=collection.color,
            type=collection.type,
            smart_rules=collection.smart_rules,
            paper_count=0,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )
    
    async def get_collection(self, collection_id: str) -> Optional[CollectionResponse]:
        """Get a collection by ID with paper count."""
        result = await self.db.execute(
            select(Collection).where(Collection.id == uuid.UUID(collection_id))
        )
        collection = result.scalar_one_or_none()
        
        if not collection:
            return None
        
        # Get paper count
        count_result = await self.db.execute(
            select(func.count(CollectionPaper.id))
            .where(CollectionPaper.collection_id == collection.id)
        )
        paper_count = count_result.scalar() or 0
        
        return CollectionResponse(
            id=collection.id,
            workspace_id=collection.workspace_id,
            name=collection.name,
            description=collection.description,
            color=collection.color,
            type=collection.type,
            smart_rules=collection.smart_rules,
            paper_count=paper_count,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )
    
    async def get_workspace_collections(self, workspace_id: str) -> List[CollectionResponse]:
        """Get all collections in a workspace."""
        result = await self.db.execute(
            select(Collection)
            .where(Collection.workspace_id == uuid.UUID(workspace_id))
            .order_by(Collection.updated_at.desc())
        )
        collections = result.scalars().all()
        
        responses = []
        for collection in collections:
            # Get paper count for each collection
            count_result = await self.db.execute(
                select(func.count(CollectionPaper.id))
                .where(CollectionPaper.collection_id == collection.id)
            )
            paper_count = count_result.scalar() or 0
            
            responses.append(CollectionResponse(
                id=collection.id,
                workspace_id=collection.workspace_id,
                name=collection.name,
                description=collection.description,
                color=collection.color,
                type=collection.type,
                smart_rules=collection.smart_rules,
                paper_count=paper_count,
                created_at=collection.created_at,
                updated_at=collection.updated_at,
            ))
        
        return responses
    
    async def update_collection(
        self,
        collection_id: str,
        data: CollectionUpdate
    ) -> Optional[CollectionResponse]:
        """Update a collection."""
        result = await self.db.execute(
            select(Collection).where(Collection.id == uuid.UUID(collection_id))
        )
        collection = result.scalar_one_or_none()
        
        if not collection:
            return None
        
        if data.name is not None:
            collection.name = data.name
        if data.description is not None:
            collection.description = data.description
        if data.color is not None:
            collection.color = data.color
        if data.smart_rules is not None:
            collection.smart_rules = data.smart_rules
        
        collection.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(collection)
        
        return await self.get_collection(collection_id)
    
    async def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection."""
        result = await self.db.execute(
            select(Collection).where(Collection.id == uuid.UUID(collection_id))
        )
        collection = result.scalar_one_or_none()
        
        if not collection:
            return False
        
        await self.db.delete(collection)
        await self.db.commit()
        
        return True
    
    # ==================== Collection Paper Methods ====================
    
    async def add_paper_to_collection(
        self,
        collection_id: str,
        data: CollectionPaperAdd
    ) -> CollectionPaperResponse:
        """Add a paper to a collection."""
        # Check if already exists
        existing = await self.db.execute(
            select(CollectionPaper)
            .where(CollectionPaper.collection_id == uuid.UUID(collection_id))
            .where(CollectionPaper.paper_id == data.paper_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Paper already in collection")
        
        cp = CollectionPaper(
            id=uuid.uuid4(),
            collection_id=uuid.UUID(collection_id),
            paper_id=data.paper_id,
            user_notes=data.notes,
            user_tags=data.tags or [],
            read_status="unread",
            added_by="user",
        )
        
        self.db.add(cp)
        
        # Update collection timestamp
        await self.db.execute(
            select(Collection).where(Collection.id == uuid.UUID(collection_id))
        )
        
        await self.db.commit()
        await self.db.refresh(cp)
        
        # Get paper details
        paper_result = await self.db.execute(
            select(Paper).where(Paper.id == data.paper_id)
        )
        paper = paper_result.scalar_one_or_none()
        
        return CollectionPaperResponse(
            id=cp.id,
            collection_id=cp.collection_id,
            paper_id=cp.paper_id,
            user_notes=cp.user_notes,
            user_tags=cp.user_tags or [],
            user_rating=cp.user_rating,
            read_status=cp.read_status,
            added_at=cp.added_at,
            added_by=cp.added_by,
            paper_title=paper.title if paper else None,
            paper_authors=paper.authors if paper else None,
            paper_year=paper.year if paper else None,
            paper_venue=paper.venue if paper else None,
            citation_count=paper.citation_count if paper else None,
        )
    
    async def get_collection_papers(
        self,
        collection_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[CollectionPaperResponse]:
        """Get all papers in a collection with metadata."""
        result = await self.db.execute(
            select(CollectionPaper, Paper)
            .join(Paper, CollectionPaper.paper_id == Paper.id)
            .where(CollectionPaper.collection_id == uuid.UUID(collection_id))
            .order_by(CollectionPaper.added_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()
        
        return [
            CollectionPaperResponse(
                id=cp.id,
                collection_id=cp.collection_id,
                paper_id=cp.paper_id,
                user_notes=cp.user_notes,
                user_tags=cp.user_tags or [],
                user_rating=cp.user_rating,
                read_status=cp.read_status,
                added_at=cp.added_at,
                added_by=cp.added_by,
                paper_title=paper.title,
                paper_authors=paper.authors,
                paper_year=paper.year,
                paper_venue=paper.venue,
                citation_count=paper.citation_count,
            )
            for cp, paper in rows
        ]
    
    async def update_collection_paper(
        self,
        collection_id: str,
        paper_id: str,
        data: CollectionPaperUpdate
    ) -> Optional[CollectionPaperResponse]:
        """Update a paper's metadata in a collection."""
        result = await self.db.execute(
            select(CollectionPaper)
            .where(CollectionPaper.collection_id == uuid.UUID(collection_id))
            .where(CollectionPaper.paper_id == uuid.UUID(paper_id))
        )
        cp = result.scalar_one_or_none()
        
        if not cp:
            return None
        
        if data.notes is not None:
            cp.user_notes = data.notes
        if data.tags is not None:
            cp.user_tags = data.tags
        if data.rating is not None:
            cp.user_rating = data.rating
        if data.read_status is not None:
            cp.read_status = data.read_status
        
        await self.db.commit()
        await self.db.refresh(cp)
        
        # Get paper details
        paper_result = await self.db.execute(
            select(Paper).where(Paper.id == uuid.UUID(paper_id))
        )
        paper = paper_result.scalar_one_or_none()
        
        return CollectionPaperResponse(
            id=cp.id,
            collection_id=cp.collection_id,
            paper_id=cp.paper_id,
            user_notes=cp.user_notes,
            user_tags=cp.user_tags or [],
            user_rating=cp.user_rating,
            read_status=cp.read_status,
            added_at=cp.added_at,
            added_by=cp.added_by,
            paper_title=paper.title if paper else None,
            paper_authors=paper.authors if paper else None,
            paper_year=paper.year if paper else None,
            paper_venue=paper.venue if paper else None,
            citation_count=paper.citation_count if paper else None,
        )
    
    async def remove_paper_from_collection(
        self,
        collection_id: str,
        paper_id: str
    ) -> bool:
        """Remove a paper from a collection."""
        result = await self.db.execute(
            delete(CollectionPaper)
            .where(CollectionPaper.collection_id == uuid.UUID(collection_id))
            .where(CollectionPaper.paper_id == uuid.UUID(paper_id))
        )
        
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_collection_paper_ids(self, collection_id: str) -> List[uuid.UUID]:
        """Get all paper IDs in a collection."""
        result = await self.db.execute(
            select(CollectionPaper.paper_id)
            .where(CollectionPaper.collection_id == uuid.UUID(collection_id))
        )
        return [row[0] for row in result.all()]
