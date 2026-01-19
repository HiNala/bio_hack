"""
Synthesis API Routes

Endpoints for AI-powered research synthesis.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.synthesis import (
    SynthesisRequest, SynthesisResponse, SynthesisFeedback
)
from app.services.synthesis import SynthesisService
from app.services.settings_service import SettingsService
from app.services.collection_service import CollectionService
from app.services.intelligence.enhanced_synthesis import EnhancedSynthesisService
from app.services.embedding.service import EmbeddingService

router = APIRouter(prefix="/synthesis", tags=["synthesis"])


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


@router.post("", response_model=SynthesisResponse)
async def create_synthesis(
    request: SynthesisRequest,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new synthesis for a research query.
    
    **Modes:**
    - `synthesize`: Summarize findings across multiple papers
    - `compare`: Side-by-side analysis of approaches
    - `plan`: Identify research gaps and next steps
    - `explore`: Deep dive into specific aspects
    
    **Optional Parameters:**
    - `workspace_id`: Save the synthesis to a workspace
    - `collection_ids`: Restrict search to specific collections
    - `settings_override`: Override user settings for this query
    """
    user_id = await ensure_user(user_id, db)
    
    # Get user settings
    settings_service = SettingsService(db)
    user_settings = await settings_service.get_user_settings(user_id)
    
    # Apply overrides if provided
    if request.settings_override:
        # Merge overrides with user settings
        settings_dict = user_settings.model_dump()
        settings_dict.update(request.settings_override)
        from app.schemas.settings import SettingsResponse
        user_settings = SettingsResponse(**settings_dict)
    
    # If workspace not provided, get default workspace
    if not request.workspace_id:
        collection_service = CollectionService(db)
        workspace = await collection_service.get_or_create_default_workspace(user_id)
        request.workspace_id = workspace.id

    # Generate enhanced synthesis with intelligence features
    embedding_service = EmbeddingService(db)
    synthesis_service = EnhancedSynthesisService(
        db=db,
        embedding_service=embedding_service
    )

    return await synthesis_service.synthesize_with_intelligence(
        user_id=user_id,
        workspace_id=str(request.workspace_id),
        query=request.query,
        mode=request.mode,
        settings_override=request.settings_override
    )


@router.get("/{synthesis_id}", response_model=SynthesisResponse)
async def get_synthesis(
    synthesis_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a saved synthesis by ID."""
    service = SynthesisService(db)
    synthesis = await service.get_synthesis(str(synthesis_id))
    
    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    
    return synthesis


@router.get("/workspace/{workspace_id}", response_model=List[SynthesisResponse])
async def list_workspace_syntheses(
    workspace_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List recent syntheses for a workspace."""
    service = SynthesisService(db)
    return await service.get_workspace_syntheses(str(workspace_id), limit)


@router.post("/{synthesis_id}/feedback")
async def add_synthesis_feedback(
    synthesis_id: UUID,
    feedback: SynthesisFeedback,
    db: AsyncSession = Depends(get_db)
):
    """Add user feedback to a synthesis."""
    service = SynthesisService(db)
    success = await service.add_feedback(
        str(synthesis_id),
        feedback.rating,
        feedback.feedback
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    
    return {"status": "ok", "message": "Feedback recorded"}


@router.post("/quick", response_model=SynthesisResponse)
async def quick_synthesis(
    query: str = Query(..., min_length=5, max_length=500),
    mode: str = Query("synthesize", regex="^(synthesize|compare|plan|explore)$"),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick synthesis endpoint - simpler API for common use cases.
    
    Uses default settings and doesn't require a workspace.
    """
    user_id = await ensure_user(user_id, db)
    
    # Get user settings
    settings_service = SettingsService(db)
    user_settings = await settings_service.get_user_settings(user_id)
    
    # Get default workspace
    collection_service = CollectionService(db)
    workspace = await collection_service.get_or_create_default_workspace(user_id)
    
    # Build request
    request = SynthesisRequest(
        query=query,
        mode=mode,
        workspace_id=workspace.id
    )
    
    # Generate synthesis
    synthesis_service = SynthesisService(db)
    
    return await synthesis_service.synthesize(
        request=request,
        user_id=user_id,
        user_settings=user_settings
    )


# Mode-specific convenience endpoints

@router.post("/summarize", response_model=SynthesisResponse)
async def summarize_topic(
    query: str = Query(..., min_length=5, max_length=500, description="Research topic to summarize"),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a synthesis summary for a research topic.
    
    Convenience endpoint for the 'synthesize' mode.
    """
    return await quick_synthesis(query, "synthesize", user_id, db)


@router.post("/compare", response_model=SynthesisResponse)
async def compare_approaches(
    query: str = Query(..., min_length=5, max_length=500, description="Approaches to compare"),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare different research approaches.
    
    Example: "Compare CRISPR vs traditional gene therapy"
    """
    return await quick_synthesis(query, "compare", user_id, db)


@router.post("/plan", response_model=SynthesisResponse)
async def plan_research(
    query: str = Query(..., min_length=5, max_length=500, description="Research area to analyze"),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Identify research gaps and plan next steps.
    
    Example: "What are the open questions in quantum error correction?"
    """
    return await quick_synthesis(query, "plan", user_id, db)


@router.post("/explore", response_model=SynthesisResponse)
async def explore_topic(
    query: str = Query(..., min_length=5, max_length=500, description="Topic to explore in depth"),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Deep dive exploration of a specific topic.
    
    Example: "Tell me more about the autophagy mechanism"
    """
    return await quick_synthesis(query, "explore", user_id, db)
