"""
Ingest Jobs API

Start and monitor ingestion jobs with live progress.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import IngestJob, Paper, Chunk
from app.schemas.ingest_job import (
    IngestJobCreateRequest,
    IngestJobCreateResponse,
    IngestJobResponse,
    IngestJobListResponse,
    IngestJobSummary,
    IngestJobPapersResponse,
    IngestJobPaper,
    IngestJobError,
)
from app.services.ingest_pipeline import IngestPipeline
from app.errors import ValidationError, NotFoundError
from app.security import limiter, InputValidation

router = APIRouter(prefix="/api/ingest", tags=["Ingest Jobs"])


@router.post("", response_model=IngestJobCreateResponse, status_code=202)
@limiter.limit("5/minute")
async def start_ingest_job(
    request: IngestJobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Validate and sanitize input
    request.query = InputValidation.sanitize_query(request.query)

    job = IngestJob(
        id=uuid.uuid4(),
        status="pending",
        original_query=request.query,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        progress={
            "current_stage": "pending",
            "stages": {
                "parsing": {"status": "pending"},
                "fetching": {"status": "pending"},
                "storing": {"status": "pending"},
                "chunking": {"status": "pending"},
                "embedding": {"status": "pending"},
            },
            "papers": {
                "openalex_found": 0,
                "semantic_scholar_found": 0,
                "duplicates_removed": 0,
                "unique_papers": 0,
                "papers_stored": 0,
            },
            "chunks": {"total_created": 0, "average_per_paper": 0.0},
            "embeddings": {"completed": 0, "total": 0, "percent": 0.0},
        },
    )
    db.add(job)
    await db.commit()

    pipeline = IngestPipeline()
    background_tasks.add_task(
        pipeline.run,
        str(job.id),
        request.query,
        request.sources,
        request.max_results_per_source,
    )

    return IngestJobCreateResponse(
        job_id=str(job.id),
        status="pending",
        message="Ingestion job created. Poll /api/ingest/{job_id} for updates.",
    )


@router.get("/{job_id}", response_model=IngestJobResponse)
async def get_ingest_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise ValidationError("Invalid job_id format", "job_id")

    result = await db.execute(select(IngestJob).where(IngestJob.id == job_uuid))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("IngestJob", job_id)

    elapsed_ms = None
    if job.processing_time_ms is not None:
        elapsed_ms = job.processing_time_ms
    else:
        elapsed_ms = int((datetime.utcnow() - job.created_at).total_seconds() * 1000)

    error = None
    if job.status == "failed" and job.error_message:
        error = IngestJobError(stage=job.progress.get("current_stage", "unknown"), message=job.error_message)

    return IngestJobResponse(
        job_id=str(job.id),
        status=job.status,
        original_query=job.original_query,
        parsed_queries=job.parsed_queries,
        progress=job.progress,
        elapsed_time_ms=elapsed_ms,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=error,
    )


@router.get("", response_model=IngestJobListResponse)
async def list_ingest_jobs(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IngestJob).order_by(IngestJob.created_at.desc()).limit(limit)
    )
    jobs = list(result.scalars().all())
    summaries = []
    for job in jobs:
        papers_count = 0
        if job.progress:
            papers_count = job.progress.get("papers", {}).get("papers_stored", 0)
        summaries.append(
            IngestJobSummary(
                job_id=str(job.id),
                status=job.status,
                original_query=job.original_query,
                papers_count=papers_count,
                created_at=job.created_at.isoformat(),
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
            )
        )
    return IngestJobListResponse(jobs=summaries)


@router.get("/{job_id}/papers", response_model=IngestJobPapersResponse)
async def get_job_papers(
    job_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise ValidationError("Invalid job_id format", "job_id")

    count_stmt = select(func.count(Paper.id)).where(Paper.ingest_job_id == job_uuid)
    total = await db.scalar(count_stmt) or 0

    result = await db.execute(
        select(Paper)
        .where(Paper.ingest_job_id == job_uuid)
        .order_by(Paper.citation_count.desc())
        .offset(offset)
        .limit(limit)
    )
    papers = list(result.scalars().all())

    response_papers = []
    for paper in papers:
        chunk_count = await db.scalar(
            select(func.count(Chunk.id)).where(Chunk.paper_id == paper.id)
        ) or 0
        response_papers.append(
            IngestJobPaper(
                id=str(paper.id),
                title=paper.title,
                authors=paper.authors if isinstance(paper.authors, list) else [],
                year=paper.year,
                venue=paper.venue,
                citation_count=paper.citation_count or 0,
                abstract_preview=paper.abstract[:200] + "..." if paper.abstract else None,
                chunk_count=chunk_count,
                is_embedded=paper.is_embedded,
                doi=paper.doi,
                url=paper.landing_url,
            )
        )

    return IngestJobPapersResponse(
        job_id=job_id,
        total_papers=total,
        papers=response_papers,
    )
