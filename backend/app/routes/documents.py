"""
Documents Endpoint

Retrieve stored papers/documents.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import math

from app.database import get_db
from app.models import Paper, SearchQuery
from app.schemas import DocumentsResponse, PaperResponse

router = APIRouter()


@router.get("/documents/stats", tags=["Documents"])
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about stored papers.
    """
    # Total papers
    total_result = await db.execute(select(func.count(Paper.id)))
    total = total_result.scalar_one()
    
    # Papers with abstracts
    with_abstract_result = await db.execute(
        select(func.count(Paper.id)).where(Paper.abstract.isnot(None))
    )
    with_abstract = with_abstract_result.scalar_one()
    
    # Chunked papers
    chunked_result = await db.execute(
        select(func.count(Paper.id)).where(Paper.is_chunked == True)
    )
    chunked = chunked_result.scalar_one()
    
    # Embedded papers
    embedded_result = await db.execute(
        select(func.count(Paper.id)).where(Paper.is_embedded == True)
    )
    embedded = embedded_result.scalar_one()
    
    return {
        "total_papers": total,
        "papers_with_abstracts": with_abstract,
        "chunked_papers": chunked,
        "embedded_papers": embedded,
    }


@router.get("/documents", response_model=DocumentsResponse, tags=["Documents"])
async def get_documents(
    query_id: Optional[str] = Query(None, description="ID of the query to get documents for"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get papers, optionally filtered by query.
    
    Returns paginated list of papers sorted by citation count (descending).
    If query_id is provided, returns papers associated with that query.
    Otherwise, returns all papers.
    """
    offset = (page - 1) * page_size
    
    # Base query
    base_query = select(Paper).where(Paper.abstract.isnot(None))
    count_query = select(func.count(Paper.id)).where(Paper.abstract.isnot(None))
    
    # If query_id provided, filter (for now we store query_id, but in simple version just get all)
    if query_id:
        try:
            query_uuid = uuid.UUID(query_id)
            # Check query exists
            result = await db.execute(
                select(SearchQuery).where(SearchQuery.id == query_uuid)
            )
            search_query = result.scalar_one_or_none()
            if not search_query:
                raise HTTPException(status_code=404, detail="Query not found")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid query_id format")
    
    # Get papers with pagination
    result = await db.execute(
        base_query
        .order_by(Paper.citation_count.desc().nullslast())
        .offset(offset)
        .limit(page_size)
    )
    papers = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()
    
    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    # Convert to response format
    paper_responses = [
        PaperResponse(
            id=str(p.id),
            title=p.title,
            abstract=p.abstract,
            authors=p.authors if isinstance(p.authors, list) else [],
            year=p.year,
            venue=p.venue,
            source="openalex" if "W" in (p.external_id or "") else "semantic_scholar",
            citation_count=p.citation_count or 0,
            doi=p.doi,
            url=p.landing_url,
        )
        for p in papers
    ]
    
    return DocumentsResponse(
        query_id=query_id,
        papers=paper_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/documents/{paper_id}", response_model=PaperResponse, tags=["Documents"])
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific paper by ID.
    """
    try:
        paper_uuid = uuid.UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id format")
    
    result = await db.execute(
        select(Paper).where(Paper.id == paper_uuid)
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return PaperResponse(
        id=str(paper.id),
        title=paper.title,
        abstract=paper.abstract,
        authors=paper.authors if isinstance(paper.authors, list) else [],
        year=paper.year,
        venue=paper.venue,
        source="openalex" if "W" in (paper.external_id or "") else "semantic_scholar",
        citation_count=paper.citation_count or 0,
        doi=paper.doi,
        url=paper.landing_url,
    )
