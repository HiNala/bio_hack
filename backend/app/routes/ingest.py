"""
Paper Ingestion Endpoint

Fetches papers from literature APIs and stores them.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import SearchQuery
from app.schemas import IngestRequest, IngestResponse
from app.services.literature import LiteratureService
from app.services.chunking import ChunkingService
from app.errors import ValidationError, NotFoundError

router = APIRouter()


class ProcessResponse(BaseModel):
    """Response from full processing pipeline."""
    query_id: str
    papers_found: int
    papers_stored: int
    chunks_created: int
    status: str


@router.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_papers(
    request: IngestRequest,
    auto_chunk: bool = Query(False, description="Automatically chunk papers after ingestion"),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest papers for a parsed query.
    
    Fetches papers from:
    - OpenAlex (250M+ works)
    - Semantic Scholar (200M+ papers)
    
    Papers are normalized, deduplicated by DOI, and stored in the database.
    Papers without abstracts are skipped (required for RAG).
    
    The query_id should be from a previous /analyze call.
    
    Set auto_chunk=true to automatically chunk papers after ingestion.
    """
    # Validate query_id
    try:
        query_uuid = uuid.UUID(request.query_id)
    except ValueError:
        raise ValidationError("Invalid query_id format", "query_id")

    # Get the search query from database
    result = await db.execute(
        select(SearchQuery).where(SearchQuery.id == query_uuid)
    )
    search_query = result.scalar_one_or_none()

    if not search_query:
        raise NotFoundError("SearchQuery", request.query_id)
    
    # Update status to ingesting
    search_query.status = "ingesting"
    await db.commit()
    
    # Create literature service
    lit_service = LiteratureService(db)

    # Get parsed query parameters
    parsed = search_query.parsed_query or {}

    # Build search query from primary terms
    primary_terms = parsed.get("primary_terms", [])
    search_text = " ".join(primary_terms) if primary_terms else search_query.raw_query

    # Get year filters
    year_from = parsed.get("year_from")
    year_to = parsed.get("year_to")

    # Fetch and store papers
    stats = await lit_service.search_and_store(
        query=search_text,
        year_from=year_from,
        year_to=year_to,
        max_per_source=50,
    )

    # Update search query with results
    search_query.papers_found = (
        stats["openalex"]["found"] +
        stats["semantic_scholar"]["found"]
    )

    # Auto-chunk if requested
    if auto_chunk and stats["total_stored"] > 0:
        search_query.status = "chunking"
        await db.commit()

        chunk_service = ChunkingService(db)
        await chunk_service.chunk_all_papers()

    search_query.status = "ingested"
    search_query.completed_at = datetime.utcnow()
    await db.commit()

    chunks_created = 0
    if auto_chunk and stats["total_stored"] > 0:
        from app.models import Chunk
        chunks_result = await db.execute(select(func.count(Chunk.id)))
        chunks_created = chunks_result.scalar_one() or 0

    return IngestResponse(
        query_id=request.query_id,
        papers_found=search_query.papers_found,
        papers_stored=stats["total_stored"],
        chunks_created=chunks_created,
        status="ingested",
        message=f"Ingested {stats['total_stored']} papers" + (f" and created {chunks_created} chunks" if chunks_created else ""),
    )


@router.post("/ingest/direct", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_papers_direct(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    max_results: int = 50,
    auto_chunk: bool = Query(False, description="Automatically chunk papers after ingestion"),
    db: AsyncSession = Depends(get_db),
):
    """
    Direct ingestion endpoint without prior /analyze call.
    
    Useful for quick testing and demos. Creates a query record
    and immediately fetches papers.
    """
    # Create a search query record
    search_query = SearchQuery(
        id=uuid.uuid4(),
        raw_query=query,
        parsed_query={
            "primary_terms": query.split()[:5],
            "year_from": year_from,
            "year_to": year_to,
        },
        status="ingesting",
        created_at=datetime.utcnow(),
    )
    db.add(search_query)
    await db.commit()
    
    # Create literature service
    lit_service = LiteratureService(db)

    # Fetch and store papers
    stats = await lit_service.search_and_store(
        query=query,
        year_from=year_from,
        year_to=year_to,
        max_per_source=max_results,
    )

    # Update search query
    search_query.papers_found = (
        stats["openalex"]["found"] +
        stats["semantic_scholar"]["found"]
    )

    # Auto-chunk if requested
    if auto_chunk and stats["total_stored"] > 0:
        search_query.status = "chunking"
        await db.commit()

        chunk_service = ChunkingService(db)
        await chunk_service.chunk_all_papers()

    search_query.status = "ingested"
    search_query.completed_at = datetime.utcnow()
    await db.commit()

    chunks_created = 0
    if auto_chunk and stats["total_stored"] > 0:
        from app.models import Chunk
        chunks_result = await db.execute(select(func.count(Chunk.id)))
        chunks_created = chunks_result.scalar_one() or 0

    return IngestResponse(
        query_id=str(search_query.id),
        papers_found=search_query.papers_found,
        papers_stored=stats["total_stored"],
        chunks_created=chunks_created,
        status="ingested",
        message=f"Ingested {stats['total_stored']} papers" + (f" and created {chunks_created} chunks" if chunks_created else ""),
    )


@router.post("/process", response_model=ProcessResponse, tags=["Pipeline"])
async def process_query(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    max_results: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Full processing pipeline: Analyze → Ingest → Chunk
    
    This is the recommended endpoint for the full workflow:
    1. Creates a search query record
    2. Fetches papers from OpenAlex and Semantic Scholar
    3. Stores and deduplicates papers
    4. Chunks all paper abstracts for RAG
    
    After this endpoint completes, papers are ready for:
    - Embedding (Mission 4)
    - Semantic search (Mission 5)
    - RAG synthesis (Mission 7)
    """
    # Create a search query record
    search_query = SearchQuery(
        id=uuid.uuid4(),
        raw_query=query,
        parsed_query={
            "primary_terms": query.split()[:5],
            "year_from": year_from,
            "year_to": year_to,
        },
        status="processing",
        created_at=datetime.utcnow(),
    )
    db.add(search_query)
    await db.commit()
    
    # Step 1: Ingest papers
    search_query.status = "ingesting"
    await db.commit()

    lit_service = LiteratureService(db)
    ingest_stats = await lit_service.search_and_store(
        query=query,
        year_from=year_from,
        year_to=year_to,
        max_per_source=max_results,
    )

    search_query.papers_found = (
        ingest_stats["openalex"]["found"] +
        ingest_stats["semantic_scholar"]["found"]
    )

    # Step 2: Chunk papers
    search_query.status = "chunking"
    await db.commit()

    chunk_service = ChunkingService(db)
    chunk_stats = await chunk_service.chunk_all_papers()

    # Complete
    search_query.status = "ready"  # Ready for embedding
    search_query.completed_at = datetime.utcnow()
    await db.commit()

    return ProcessResponse(
        query_id=str(search_query.id),
        papers_found=search_query.papers_found,
        papers_stored=ingest_stats["total_stored"],
        chunks_created=chunk_stats["chunks_created"],
        status="ready",
    )
