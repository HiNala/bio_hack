"""
Semantic Search Endpoint

Vector similarity search over embedded chunks.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.schemas import SearchRequest, SearchResponse, SearchResult
from app.services.search import SearchService
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class SearchResultDetail(BaseModel):
    """Detailed search result."""
    chunk_id: str
    paper_id: str
    paper_title: str
    paper_year: Optional[int]
    paper_authors: list[str]
    paper_citation_count: int
    paper_doi: Optional[str]
    paper_url: Optional[str]
    text: str
    section: Optional[str]
    similarity_score: float
    final_score: float


class SearchResponseDetail(BaseModel):
    """Detailed search response."""
    query: str
    results: list[SearchResultDetail]
    total: int


class SearchStatsResponse(BaseModel):
    """Search statistics."""
    searchable_chunks: int
    searchable_papers: int
    index_type: str
    distance_metric: str


@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def semantic_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform semantic search over embedded paper chunks.
    
    Uses pgvector for cosine similarity search.
    Results are ranked by: similarity * citation_boost * recency_factor
    
    Returns deduplicated results (one chunk per paper).
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured for query embedding."
        )
    
    service = SearchService(db)
    
    try:
        results = await service.search(
            query=request.query,
            top_k=request.limit,
            dedupe_papers=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    return SearchResponse(
        results=[
            SearchResult(
                chunk_id=r.chunk_id,
                paper_id=r.paper_id,
                paper_title=r.paper_title,
                text=r.chunk_text[:500] + "..." if len(r.chunk_text) > 500 else r.chunk_text,
                score=r.final_score,
            )
            for r in results
        ],
        total=len(results),
    )


@router.post("/search/detailed", response_model=SearchResponseDetail, tags=["Search"])
async def semantic_search_detailed(
    query: str = Query(..., min_length=3, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    year_from: Optional[int] = Query(None, description="Minimum year"),
    year_to: Optional[int] = Query(None, description="Maximum year"),
    db: AsyncSession = Depends(get_db),
):
    """
    Perform semantic search with detailed results.
    
    Returns full metadata for each result including:
    - Paper details (title, authors, year, citations)
    - Chunk details (text, section)
    - Scores (similarity, final)
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured."
        )
    
    service = SearchService(db)
    
    results = await service.search(
        query=query,
        top_k=limit,
        year_from=year_from,
        year_to=year_to,
        dedupe_papers=True,
    )
    
    return SearchResponseDetail(
        query=query,
        results=[
            SearchResultDetail(
                chunk_id=r.chunk_id,
                paper_id=r.paper_id,
                paper_title=r.paper_title,
                paper_year=r.paper_year,
                paper_authors=r.paper_authors,
                paper_citation_count=r.paper_citation_count,
                paper_doi=r.paper_doi,
                paper_url=r.paper_url,
                text=r.chunk_text,
                section=r.chunk_section,
                similarity_score=r.similarity_score,
                final_score=r.final_score,
            )
            for r in results
        ],
        total=len(results),
    )


@router.get("/search/stats", response_model=SearchStatsResponse, tags=["Search"])
async def get_search_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about searchable content.
    """
    service = SearchService(db)
    stats = await service.get_search_stats()
    
    return SearchStatsResponse(**stats)
