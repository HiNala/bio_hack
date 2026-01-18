"""
Ingest Pipeline Service

Orchestrates parsing, fetching, storing, chunking, and embedding.
"""

import time
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session_maker
from app.models import IngestJob
from app.services.query_parser import QueryParser
from app.services.literature.service import LiteratureService
from app.services.chunking.service import ChunkingService
from app.services.embedding.service import EmbeddingService


class IngestPipeline:
    """Coordinates the ingestion workflow and updates job progress."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def run(
        self,
        job_id: str,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 50,
    ) -> None:
        """Run the pipeline for a given job."""
        async with async_session_maker() as session:
            start_time = time.time()
            try:
                await self._update_job(session, job_id, status="parsing")

                # Stage: Parsing
                parser = QueryParser()
                parsed = parser.parse(query)
                await self._update_job(
                    session,
                    job_id,
                    parsed_queries=parsed,
                    progress=self._build_progress("parsing", stages={
                        "parsing": {"status": "completed", "duration_ms": 50},
                        "fetching": {"status": "pending"},
                        "storing": {"status": "pending"},
                        "chunking": {"status": "pending"},
                        "embedding": {"status": "pending"},
                    }),
                )

                # Stage: Fetching + Storing
                await self._update_job(
                    session,
                    job_id,
                    status="fetching",
                    progress=self._build_progress(
                        "fetching",
                        stages={
                            "parsing": {"status": "completed", "duration_ms": 50},
                            "fetching": {"status": "in_progress"},
                            "storing": {"status": "pending"},
                            "chunking": {"status": "pending"},
                            "embedding": {"status": "pending"},
                        },
                    ),
                )
                literature = LiteratureService(session)

                stats = await literature.search_and_store_multi(
                    queries=parsed["search_queries"] or [query],
                    max_per_source=max_results_per_source,
                    sources=sources,
                    ingest_job_id=uuid.UUID(job_id),
                    progress_callback=None,
                )

                papers_progress = {
                    "openalex_found": stats["openalex"]["found"],
                    "semantic_scholar_found": stats["semantic_scholar"]["found"],
                    "duplicates_removed": stats["duplicates_skipped"],
                    "unique_papers": stats["total_stored"],
                    "papers_stored": stats["total_stored"],
                }

                await self._update_job(
                    session,
                    job_id,
                    status="storing",
                    progress=self._build_progress(
                        "storing",
                        papers=papers_progress,
                        stages={
                            "parsing": {"status": "completed", "duration_ms": 50},
                            "fetching": {"status": "completed"},
                            "storing": {"status": "completed"},
                            "chunking": {"status": "pending"},
                            "embedding": {"status": "pending"},
                        },
                    ),
                )

                # Stage: Chunking
                await self._update_job(session, job_id, status="chunking")
                chunker = ChunkingService(session)
                chunk_stats = await chunker.chunk_papers_for_job(uuid.UUID(job_id))
                chunks_created = chunk_stats.get("chunks_created", 0)
                avg_per_paper = 0.0
                if papers_progress["papers_stored"]:
                    avg_per_paper = chunks_created / papers_progress["papers_stored"]

                await self._update_job(
                    session,
                    job_id,
                    status="embedding",
                    progress=self._build_progress(
                        "embedding",
                        papers=papers_progress,
                        chunks={
                            "total_created": chunks_created,
                            "average_per_paper": round(avg_per_paper, 2),
                        },
                        stages={
                            "parsing": {"status": "completed", "duration_ms": 50},
                            "fetching": {"status": "completed"},
                            "storing": {"status": "completed"},
                            "chunking": {"status": "completed"},
                            "embedding": {"status": "in_progress"},
                        },
                    ),
                )

                # Stage: Embedding
                embedder = EmbeddingService(session)

                async def embed_progress_callback(done: int, total: int):
                    progress = self._build_progress(
                        "embedding",
                        papers=papers_progress,
                        chunks={
                            "total_created": chunks_created,
                            "average_per_paper": round(avg_per_paper, 2),
                        },
                        embeddings={
                            "completed": done,
                            "total": total,
                            "percent": round((done / total) * 100, 1) if total else 0,
                        },
                        stages={
                            "parsing": {"status": "completed", "duration_ms": 50},
                            "fetching": {"status": "completed"},
                            "storing": {"status": "completed"},
                            "chunking": {"status": "completed"},
                            "embedding": {"status": "in_progress"},
                        },
                    )
                    await self._update_job(session, job_id, progress=progress)

                embed_stats = await embedder.embed_unembedded_chunks(
                    ingest_job_id=uuid.UUID(job_id),
                    progress_callback=embed_progress_callback,
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                await self._update_job(
                    session,
                    job_id,
                    status="completed",
                    completed_at=datetime.utcnow(),
                    processing_time_ms=elapsed_ms,
                    progress=self._build_progress(
                        "completed",
                        papers=papers_progress,
                        chunks={
                            "total_created": chunks_created,
                            "average_per_paper": round(avg_per_paper, 2),
                        },
                        embeddings={
                            "completed": embed_stats.get("embedded", 0),
                            "total": embed_stats.get("total", 0),
                            "percent": 100.0 if embed_stats.get("total", 0) else 0.0,
                        },
                        stages={
                            "parsing": {"status": "completed", "duration_ms": 50},
                            "fetching": {"status": "completed"},
                            "storing": {"status": "completed"},
                            "chunking": {"status": "completed"},
                            "embedding": {"status": "completed"},
                        },
                    ),
                )
            except Exception as exc:
                elapsed_ms = int((time.time() - start_time) * 1000)
                await self._update_job(
                    session,
                    job_id,
                    status="failed",
                    error_message=str(exc),
                    completed_at=datetime.utcnow(),
                    processing_time_ms=elapsed_ms,
                )

    async def _update_job(self, session: AsyncSession, job_id: str, **updates) -> None:
        job = await self._get_job(session, job_id)
        for key, value in updates.items():
            setattr(job, key, value)
        job.updated_at = datetime.utcnow()
        await session.commit()

    async def _get_job(self, session: AsyncSession, job_id: str) -> IngestJob:
        result = await session.execute(
            select(IngestJob).where(IngestJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Ingest job not found: {job_id}")
        return job

    def _build_progress(
        self,
        current_stage: str,
        papers: Optional[dict] = None,
        chunks: Optional[dict] = None,
        embeddings: Optional[dict] = None,
        stages: Optional[dict] = None,
    ) -> dict:
        return {
            "current_stage": current_stage,
            "stages": stages or {},
            "papers": papers or {
                "openalex_found": 0,
                "semantic_scholar_found": 0,
                "duplicates_removed": 0,
                "unique_papers": 0,
                "papers_stored": 0,
            },
            "chunks": chunks or {
                "total_created": 0,
                "average_per_paper": 0.0,
            },
            "embeddings": embeddings or {
                "completed": 0,
                "total": 0,
                "percent": 0.0,
            },
        }
