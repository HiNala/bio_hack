"""
Embedding Endpoints

API endpoints for vector embedding operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.embedding import EmbeddingService
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class EmbedResponse(BaseModel):
    """Response from embedding operation."""
    chunks_processed: int
    chunks_embedded: int
    papers_updated: int
    errors: list[dict] = []


class EmbedStatsResponse(BaseModel):
    """Embedding statistics."""
    total_chunks: int
    embedded_chunks: int
    unembedded_chunks: int
    embedded_papers: int
    embedding_model: str
    dimensions: int


class EmbedQueryRequest(BaseModel):
    """Request to embed a query."""
    query: str


class EmbedQueryResponse(BaseModel):
    """Response with query embedding."""
    query: str
    embedding: list[float]
    dimensions: int


@router.post("/embed/all", response_model=EmbedResponse, tags=["Embedding"])
async def embed_all_chunks(
    batch_size: int = Query(100, ge=1, le=500, description="Chunks per API call"),
    limit: int = Query(None, ge=1, description="Max chunks to process"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate embeddings for all un-embedded chunks.
    
    Uses OpenAI's text-embedding-3-small model (1536 dimensions).
    Processes chunks in batches for efficiency.
    
    Requires OPENAI_API_KEY environment variable.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )
    
    service = EmbeddingService(db)
    stats = await service.embed_all_chunks(
        batch_size=batch_size,
        limit=limit,
    )
    
    return EmbedResponse(
        chunks_processed=stats["chunks_processed"],
        chunks_embedded=stats["chunks_embedded"],
        papers_updated=stats["papers_updated"],
        errors=stats.get("errors", []),
    )


@router.get("/embed/stats", response_model=EmbedStatsResponse, tags=["Embedding"])
async def get_embedding_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about embeddings in the database.
    """
    service = EmbeddingService(db)
    stats = await service.get_embedding_stats()
    
    return EmbedStatsResponse(**stats)


@router.post("/embed/query", response_model=EmbedQueryResponse, tags=["Embedding"])
async def embed_query(
    request: EmbedQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate embedding for a search query.
    
    Useful for testing and debugging semantic search.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured."
        )
    
    service = EmbeddingService(db)
    embedding = await service.embed_query(request.query)
    
    return EmbedQueryResponse(
        query=request.query,
        embedding=embedding,
        dimensions=len(embedding),
    )
