"""
Workspace and Collection API Routes

Endpoints for managing workspaces, collections, and collection papers.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    CollectionCreate, CollectionUpdate, CollectionResponse,
    CollectionPaperAdd, CollectionPaperUpdate, CollectionPaperResponse,
)
from app.services.collection_service import CollectionService
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> Optional[str]:
    """Get user ID from header."""
    return x_user_id


async def ensure_user(
    user_id: Optional[str],
    db: AsyncSession
) -> str:
    """Ensure user exists and return user ID."""
    service = SettingsService(db)
    if not user_id:
        user = await service.get_or_create_user()
        return str(user.id)
    return user_id


# ==================== Workspace Endpoints ====================

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all workspaces for the current user."""
    user_id = await ensure_user(user_id, db)
    service = CollectionService(db)
    return await service.get_user_workspaces(user_id)


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workspace."""
    user_id = await ensure_user(user_id, db)
    service = CollectionService(db)
    return await service.create_workspace(user_id, data)


@router.get("/default", response_model=WorkspaceResponse)
async def get_default_workspace(
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get or create the default workspace for the user."""
    user_id = await ensure_user(user_id, db)
    service = CollectionService(db)
    return await service.get_or_create_default_workspace(user_id)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a workspace by ID."""
    service = CollectionService(db)
    workspace = await service.get_workspace(str(workspace_id))
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a workspace."""
    service = CollectionService(db)
    workspace = await service.update_workspace(str(workspace_id), data)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.delete("/{workspace_id}", status_code=204)
async def archive_workspace(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Archive a workspace (soft delete)."""
    service = CollectionService(db)
    success = await service.archive_workspace(str(workspace_id))
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")


# ==================== Collection Endpoints ====================

@router.get("/{workspace_id}/collections", response_model=List[CollectionResponse])
async def list_collections(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all collections in a workspace."""
    service = CollectionService(db)
    return await service.get_workspace_collections(str(workspace_id))


@router.post("/{workspace_id}/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(
    workspace_id: UUID,
    data: CollectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new collection in a workspace."""
    service = CollectionService(db)
    return await service.create_collection(str(workspace_id), data)


@router.get("/{workspace_id}/collections/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    workspace_id: UUID,
    collection_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a collection by ID."""
    service = CollectionService(db)
    collection = await service.get_collection(str(collection_id))
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.patch("/{workspace_id}/collections/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    workspace_id: UUID,
    collection_id: UUID,
    data: CollectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a collection."""
    service = CollectionService(db)
    collection = await service.update_collection(str(collection_id), data)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.delete("/{workspace_id}/collections/{collection_id}", status_code=204)
async def delete_collection(
    workspace_id: UUID,
    collection_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a collection."""
    service = CollectionService(db)
    success = await service.delete_collection(str(collection_id))
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")


# ==================== Collection Paper Endpoints ====================

@router.get(
    "/{workspace_id}/collections/{collection_id}/papers",
    response_model=List[CollectionPaperResponse]
)
async def list_collection_papers(
    workspace_id: UUID,
    collection_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all papers in a collection."""
    service = CollectionService(db)
    return await service.get_collection_papers(str(collection_id), limit, offset)


@router.post(
    "/{workspace_id}/collections/{collection_id}/papers",
    response_model=CollectionPaperResponse,
    status_code=201
)
async def add_paper_to_collection(
    workspace_id: UUID,
    collection_id: UUID,
    data: CollectionPaperAdd,
    db: AsyncSession = Depends(get_db)
):
    """Add a paper to a collection."""
    service = CollectionService(db)
    try:
        return await service.add_paper_to_collection(str(collection_id), data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{workspace_id}/collections/{collection_id}/papers/{paper_id}",
    response_model=CollectionPaperResponse
)
async def update_collection_paper(
    workspace_id: UUID,
    collection_id: UUID,
    paper_id: UUID,
    data: CollectionPaperUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a paper's metadata in a collection."""
    service = CollectionService(db)
    paper = await service.update_collection_paper(
        str(collection_id), str(paper_id), data
    )
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in collection")
    return paper


@router.delete(
    "/{workspace_id}/collections/{collection_id}/papers/{paper_id}",
    status_code=204
)
async def remove_paper_from_collection(
    workspace_id: UUID,
    collection_id: UUID,
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Remove a paper from a collection."""
    service = CollectionService(db)
    success = await service.remove_paper_from_collection(
        str(collection_id), str(paper_id)
    )
    if not success:
        raise HTTPException(status_code=404, detail="Paper not found in collection")
