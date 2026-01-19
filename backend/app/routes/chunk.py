"""
Chunking Endpoints

API endpoints for text chunking operations.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.chunking import ChunkingService
from app.cache import cached

router = APIRouter()


class ChunkResponse(BaseModel):
    """Response from chunking operation."""
    papers_processed: int
    chunks_created: int
    papers_skipped: int = 0
    errors: list[dict] = []


class ChunkStatsResponse(BaseModel):
    """Statistics about chunks."""
    total_chunks: int
    embedded_chunks: int
    avg_tokens_per_chunk: float
    chunked_papers: int
    unchunked_papers: int


class PaperChunksResponse(BaseModel):
    """Response with chunks for a specific paper."""
    paper_id: str
    chunks: list[dict]
    total: int


@router.post("/chunk/all", response_model=ChunkResponse, tags=["Chunking"])
async def chunk_all_papers(
    batch_size: int = Query(100, ge=1, le=500, description="Papers per batch"),
    limit: int = Query(None, ge=1, description="Max papers to process"),
    db: AsyncSession = Depends(get_db),
):
    """
    Chunk all unchunked papers in the database.
    
    This processes papers that have abstracts but haven't been chunked yet.
    Each paper's abstract is split into overlapping chunks optimized for
    RAG retrieval.
    
    Chunking parameters (from config):
    - Target chunk size: ~500 tokens
    - Overlap: ~50 tokens
    - Min chunk size: 50 tokens
    """
    service = ChunkingService(db)
    
    stats = await service.chunk_all_papers(
        batch_size=batch_size,
        limit=limit,
    )
    
    return ChunkResponse(
        papers_processed=stats["papers_processed"],
        chunks_created=stats["chunks_created"],
        papers_skipped=stats.get("papers_skipped", 0),
        errors=stats.get("errors", []),
    )


@router.post("/chunk/paper/{paper_id}", tags=["Chunking"])
async def chunk_single_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Chunk a specific paper by ID.
    
    Useful for re-processing a single paper or testing.
    """
    try:
        paper_uuid = uuid.UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id format")
    
    service = ChunkingService(db)
    
    try:
        chunks_created = await service.chunk_paper_by_id(paper_uuid)
        return {
            "paper_id": paper_id,
            "chunks_created": chunks_created,
            "status": "success",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/chunk/stats", response_model=ChunkStatsResponse, tags=["Chunking"])
@cached(ttl_seconds=60)  # Cache for 1 minute
async def get_chunk_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about chunks in the database.
    
    Returns counts and averages for monitoring chunking progress.
    """
    service = ChunkingService(db)
    
    stats = await service.get_chunk_stats()
    unchunked = await service.get_unchunked_count()
    
    return ChunkStatsResponse(
        total_chunks=stats["total_chunks"],
        embedded_chunks=stats["embedded_chunks"],
        avg_tokens_per_chunk=stats["avg_tokens_per_chunk"],
        chunked_papers=stats["chunked_papers"],
        unchunked_papers=unchunked,
    )


@router.get("/chunk/paper/{paper_id}", response_model=PaperChunksResponse, tags=["Chunking"])
async def get_paper_chunks(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all chunks for a specific paper.
    
    Returns chunks in order with their metadata.
    """
    try:
        paper_uuid = uuid.UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id format")
    
    service = ChunkingService(db)
    chunks = await service.get_chunks_for_paper(paper_uuid)
    
    return PaperChunksResponse(
        paper_id=paper_id,
        chunks=[
            {
                "id": str(c.id),
                "chunk_index": c.chunk_index,
                "text": c.text,
                "section": c.section,
                "token_count": c.token_count,
                "char_count": c.char_count,
                "has_embedding": c.embedding is not None,
            }
            for c in chunks
        ],
        total=len(chunks),
    )


@router.post("/chunk/preview", tags=["Chunking"])
async def preview_chunking(
    text: str = Query(..., min_length=10, description="Text to chunk"),
    title: str = Query("Sample Paper", description="Paper title for context"),
):
    """
    Preview how text would be chunked.
    
    Useful for testing and debugging the chunking algorithm.
    Does not store anything in the database.
    """
    from app.services.chunking import TextChunker
    
    chunker = TextChunker()
    chunks = chunker.chunk_paper(title=title, abstract=text)
    
    return {
        "input_length": len(text),
        "input_tokens": chunker.count_tokens(text),
        "num_chunks": len(chunks),
        "chunks": [
            {
                "index": c.chunk_index,
                "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                "tokens": c.token_count,
                "chars": c.char_count,
                "section": c.section,
                "has_overlap": c.has_overlap,
            }
            for c in chunks
        ],
    }
