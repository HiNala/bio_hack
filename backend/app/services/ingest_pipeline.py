"""
Intelligent Ingest Pipeline Service

Orchestrates the complete ingestion workflow from user query to vector-embedded
chunks ready for semantic search.

Pipeline Stages:
1. Query Parsing - Extract concepts, temporal bounds, generate search queries
2. Literature Fetching - Parallel fetch from OpenAlex and Semantic Scholar
3. Deduplication - DOI and fuzzy title matching
4. Storage - Upsert papers to database
5. Chunking - Intelligent sentence-aware text segmentation
6. Embedding - Batch vector generation with OpenAI

Principles:
- Fail gracefully - partial results are better than no results
- Be observable - log everything, track progress
- Be efficient - batch operations, parallel requests
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session_maker
from app.models import IngestJob
from app.services.query_parser import QueryParser
from app.services.literature.service import LiteratureService
from app.services.chunking.service import ChunkingService
from app.services.embedding.service import EmbeddingService
from app.services.activity_stream import activity_stream

logger = logging.getLogger(__name__)


class IngestPipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, stage: str, message: str, recoverable: bool = True):
        self.stage = stage
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"[{stage}] {message}")


class IngestPipeline:
    """
    Coordinates the complete ingestion workflow with progress tracking
    and comprehensive error handling.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def run(
        self,
        job_id: str,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 50,
    ) -> dict:
        """
        Run the complete pipeline for a given job.
        
        Args:
            job_id: Unique job identifier
            query: User's research query
            sources: List of sources to query (default: all)
            max_results_per_source: Max papers per source
            
        Returns:
            Final statistics dictionary
        """
        async with async_session_maker() as session:
            start_time = time.time()
            
            try:
                # ========== STAGE 1: PARSE QUERY ==========
                await self._update_job(session, job_id, status="parsing")
                logger.info(f"Job {job_id}: Starting query parsing")
                
                # Broadcast: Thinking
                await activity_stream.thinking(
                    f"Analyzing your query: \"{query[:60]}{'...' if len(query) > 60 else ''}\"",
                    detail="Breaking down research concepts and keywords...",
                    job_id=job_id
                )
                
                parser = QueryParser()
                parsed = parser.parse(query)
                
                search_queries = parsed.get("search_queries", []) or [query]
                
                logger.info(f"Job {job_id}: Parsed into {len(search_queries)} search queries")
                logger.info(f"Job {job_id}: Primary terms: {parsed.get('primary_terms', [])}")
                
                await self._update_job(
                    session,
                    job_id,
                    parsed_queries=parsed,
                    progress=self._build_progress(
                        "parsing",
                        stages={
                            "parsing": {"status": "completed", "duration_ms": int((time.time() - start_time) * 1000)},
                            "fetching": {"status": "pending"},
                            "storing": {"status": "pending"},
                            "chunking": {"status": "pending"},
                            "embedding": {"status": "pending"},
                        },
                    ),
                )

                # ========== STAGE 2: FETCH FROM SOURCES ==========
                await self._update_job(
                    session,
                    job_id,
                    status="fetching",
                    progress=self._build_progress(
                        "fetching",
                        stages={
                            "parsing": {"status": "completed"},
                            "fetching": {"status": "in_progress"},
                            "storing": {"status": "pending"},
                            "chunking": {"status": "pending"},
                            "embedding": {"status": "pending"},
                        },
                    ),
                )
                
                logger.info(f"Job {job_id}: Fetching from literature sources")
                
                # Broadcast: Searching
                await activity_stream.searching(
                    "Searching academic literature databases...",
                    api_call="GET /openalex, GET /semantic_scholar",
                    job_id=job_id
                )
                
                literature = LiteratureService(session)

                # Async progress callback
                async def fetch_progress_callback(progress_data: dict):
                    openalex = progress_data.get("openalex_found", 0)
                    semantic = progress_data.get("semantic_scholar_found", 0)
                    total = openalex + semantic
                    
                    # Broadcast: Fetching progress
                    await activity_stream.fetching(
                        f"Found {total} papers ({openalex} OpenAlex, {semantic} Semantic Scholar)...",
                        articles_found=total,
                        api_call="Retrieving paper metadata and abstracts",
                        job_id=job_id
                    )
                    
                    await self._update_job(
                        session,
                        job_id,
                        progress=self._build_progress(
                            "fetching",
                            papers={
                                "openalex_found": openalex,
                                "semantic_scholar_found": semantic,
                                "duplicates_removed": progress_data.get("duplicates_removed", 0),
                                "unique_papers": progress_data.get("unique_papers", 0),
                                "papers_stored": progress_data.get("papers_stored", 0),
                            },
                            stages={
                                "parsing": {"status": "completed"},
                                "fetching": {"status": "in_progress"},
                                "storing": {"status": "pending"},
                                "chunking": {"status": "pending"},
                                "embedding": {"status": "pending"},
                            },
                        ),
                    )

                stats = await literature.search_and_store_multi(
                    queries=search_queries,
                    max_per_source=max_results_per_source,
                    sources=sources,
                    ingest_job_id=uuid.UUID(job_id),
                    progress_callback=fetch_progress_callback,
                )

                papers_progress = {
                    "openalex_found": stats["openalex"]["found"],
                    "semantic_scholar_found": stats["semantic_scholar"]["found"],
                    "duplicates_removed": stats["duplicates_skipped"],
                    "unique_papers": stats["total_stored"],
                    "papers_stored": stats["total_stored"],
                }

                logger.info(f"Job {job_id}: Stored {stats['total_stored']} papers")
                
                # Broadcast: Processing/storing
                await activity_stream.processing(
                    f"Deduplicating and storing {stats['total_stored']} unique papers...",
                    detail=f"Removed {stats['duplicates_skipped']} duplicate entries",
                    job_id=job_id
                )

                if stats.get("fetch_errors"):
                    logger.warning(f"Job {job_id}: Fetch errors: {stats['fetch_errors']}")

                await self._update_job(
                    session,
                    job_id,
                    status="storing",
                    progress=self._build_progress(
                        "storing",
                        papers=papers_progress,
                        stages={
                            "parsing": {"status": "completed"},
                            "fetching": {"status": "completed"},
                            "storing": {"status": "completed"},
                            "chunking": {"status": "pending"},
                            "embedding": {"status": "pending"},
                        },
                    ),
                )

                # ========== STAGE 3: CHUNKING ==========
                await self._update_job(session, job_id, status="chunking")
                logger.info(f"Job {job_id}: Starting chunking")
                
                # Broadcast: Chunking
                await activity_stream.processing(
                    "Chunking paper abstracts into semantic segments...",
                    detail="Creating searchable text passages",
                    job_id=job_id
                )
                
                chunker = ChunkingService(session)
                chunk_stats = await chunker.chunk_papers_for_job(uuid.UUID(job_id))
                chunks_created = chunk_stats.get("chunks_created", 0)
                avg_per_paper = 0.0
                if papers_progress["papers_stored"]:
                    avg_per_paper = chunks_created / papers_progress["papers_stored"]

                logger.info(f"Job {job_id}: Created {chunks_created} chunks")
                
                # Broadcast: Chunks created
                await activity_stream.processing(
                    f"Created {chunks_created} text chunks from {papers_progress['papers_stored']} papers",
                    detail=f"Average {avg_per_paper:.1f} chunks per paper",
                    job_id=job_id
                )

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
                            "parsing": {"status": "completed"},
                            "fetching": {"status": "completed"},
                            "storing": {"status": "completed"},
                            "chunking": {"status": "completed"},
                            "embedding": {"status": "in_progress"},
                        },
                    ),
                )

                # ========== STAGE 4: EMBEDDING ==========
                logger.info(f"Job {job_id}: Starting embedding")
                
                # Broadcast: Embedding start
                await activity_stream.embedding(
                    f"Generating vector embeddings for {chunks_created} chunks...",
                    progress=0.0,
                    job_id=job_id
                )
                
                try:
                    embedder = EmbeddingService(session)

                    async def embed_progress_callback(done: int, total: int):
                        percent = round((done / total) * 100, 1) if total else 0
                        
                        # Broadcast: Embedding progress
                        await activity_stream.embedding(
                            f"Generating vector embeddings... {percent}%",
                            progress=percent / 100,
                            job_id=job_id
                        )
                        
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
                                "percent": percent,
                            },
                            stages={
                                "parsing": {"status": "completed"},
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
                    
                    logger.info(f"Job {job_id}: Embedded {embed_stats.get('embedded', 0)} chunks")
                    
                    if embed_stats.get("errors"):
                        logger.warning(f"Job {job_id}: Embedding errors: {embed_stats['errors']}")
                    
                except ValueError as e:
                    # OpenAI API key not configured
                    logger.error(f"Job {job_id}: Embedding failed - {e}")
                    embed_stats = {"embedded": 0, "total": chunks_created, "errors": [str(e)]}

                # ========== COMPLETE ==========
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                final_progress = self._build_progress(
                    "completed",
                    papers=papers_progress,
                    chunks={
                        "total_created": chunks_created,
                        "average_per_paper": round(avg_per_paper, 2),
                    },
                    embeddings={
                        "completed": embed_stats.get("embedded", 0),
                        "total": embed_stats.get("total", chunks_created),
                        "percent": 100.0 if embed_stats.get("embedded", 0) == embed_stats.get("total", 0) else round((embed_stats.get("embedded", 0) / max(embed_stats.get("total", 1), 1)) * 100, 1),
                    },
                    stages={
                        "parsing": {"status": "completed"},
                        "fetching": {"status": "completed"},
                        "storing": {"status": "completed"},
                        "chunking": {"status": "completed"},
                        "embedding": {"status": "completed" if not embed_stats.get("errors") else "completed_with_errors"},
                    },
                )
                
                await self._update_job(
                    session,
                    job_id,
                    status="completed",
                    completed_at=datetime.utcnow(),
                    processing_time_ms=elapsed_ms,
                    progress=final_progress,
                )
                
                logger.info(f"Job {job_id}: Completed in {elapsed_ms}ms")
                
                # Broadcast: Complete
                await activity_stream.complete(
                    f"Ingestion complete! Processed {papers_progress['papers_stored']} papers.",
                    detail=f"Created {chunks_created} chunks with {embed_stats.get('embedded', 0)} embeddings in {elapsed_ms/1000:.1f}s",
                    job_id=job_id
                )
                
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "papers_stored": papers_progress["papers_stored"],
                    "chunks_created": chunks_created,
                    "embeddings_generated": embed_stats.get("embedded", 0),
                    "elapsed_ms": elapsed_ms,
                }

            except Exception as exc:
                elapsed_ms = int((time.time() - start_time) * 1000)
                error_message = str(exc)
                
                logger.error(f"Job {job_id}: Failed with error: {error_message}", exc_info=True)
                
                # Broadcast: Error
                await activity_stream.error(
                    "Pipeline encountered an error",
                    detail=error_message[:200],
                    job_id=job_id
                )
                
                await self._update_job(
                    session,
                    job_id,
                    status="failed",
                    error_message=error_message,
                    completed_at=datetime.utcnow(),
                    processing_time_ms=elapsed_ms,
                )
                
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": error_message,
                    "elapsed_ms": elapsed_ms,
                }

    async def _update_job(self, session: AsyncSession, job_id: str, **updates) -> None:
        """Update job record in database."""
        job = await self._get_job(session, job_id)
        for key, value in updates.items():
            setattr(job, key, value)
        job.updated_at = datetime.utcnow()
        await session.commit()

    async def _get_job(self, session: AsyncSession, job_id: str) -> IngestJob:
        """Get job by ID."""
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
        """Build progress dict for job status updates."""
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
