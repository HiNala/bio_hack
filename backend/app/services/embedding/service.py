"""
Embedding Service

Generates vector embeddings for text chunks using OpenAI.
"""

import uuid
import re
import inspect
from typing import Callable, Optional, Awaitable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import Chunk, Paper

settings = get_settings()


class EmbeddingService:
    """
    Service for generating and storing vector embeddings.
    
    Features:
    - Batch embedding for efficiency
    - Retry logic with exponential backoff
    - Text preprocessing for better embeddings
    - Progress tracking callbacks
    """
    
    # Batch size for OpenAI API calls
    BATCH_SIZE = 100
    
    # Max tokens for embedding model
    MAX_TOKENS = 8191
    
    # Context prefix for better embeddings
    CONTEXT_PREFIX = "Scientific paper excerpt: "
    
    def __init__(self, db: AsyncSession):
        """Initialize embedding service."""
        self.db = db
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    async def embed_unembedded_chunks(
        self,
        ingest_job_id: Optional[str] = None,
        batch_size: int = 100,
        progress_callback: Optional[Callable[[int, int], Awaitable[None] | None]] = None,
    ) -> dict:
        """
        Embed all chunks without embeddings, optionally filtered by job.
        
        Args:
            ingest_job_id: Optional job ID to filter chunks
            batch_size: Chunks per batch
            progress_callback: Optional callback(done, total)
            
        Returns:
            Stats dict with embedded/total/errors
        """
        stats = {
            "embedded": 0,
            "total": 0,
            "errors": [],
        }

        # Build count query
        count_stmt = select(func.count(Chunk.id)).where(Chunk.embedding.is_(None))
        if ingest_job_id:
            job_uuid = uuid.UUID(ingest_job_id) if isinstance(ingest_job_id, str) else ingest_job_id
            count_stmt = count_stmt.join(Paper).where(Paper.ingest_job_id == job_uuid)
        
        total = await self.db.scalar(count_stmt)
        stats["total"] = total or 0

        if not stats["total"]:
            return stats

        offset = 0
        while True:
            # Build select query
            stmt = select(Chunk).where(Chunk.embedding.is_(None))
            if ingest_job_id:
                job_uuid = uuid.UUID(ingest_job_id) if isinstance(ingest_job_id, str) else ingest_job_id
                stmt = stmt.join(Paper).where(Paper.ingest_job_id == job_uuid)
            stmt = stmt.order_by(Chunk.created_at).offset(offset).limit(batch_size)

            result = await self.db.execute(stmt)
            chunks = list(result.scalars().all())
            if not chunks:
                break

            inputs = [self._prepare_text(c.text) for c in chunks]
            try:
                embeddings = await self._embed_batch(inputs)

                # Store embeddings
                for chunk, vector in zip(chunks, embeddings):
                    chunk.embedding = vector

                stats["embedded"] += len(chunks)
                await self.db.commit()

                if progress_callback:
                    cb_result = progress_callback(stats["embedded"], stats["total"])
                    if inspect.isawaitable(cb_result):
                        await cb_result

            except Exception as exc:
                stats["errors"].append(str(exc))
                await self.db.rollback()

            offset += batch_size

        # Mark papers as embedded when all chunks are embedded
        await self._mark_papers_embedded(ingest_job_id)

        return stats

    async def embed_all_chunks(
        self,
        batch_size: int = None,
        limit: Optional[int] = None,
    ) -> dict:
        """
        Embed all chunks without embeddings.
        
        Args:
            batch_size: Chunks per batch
            limit: Max chunks to process
            
        Returns:
            Stats dict
        """
        batch_size = batch_size or self.BATCH_SIZE
        stats = await self.embed_unembedded_chunks(batch_size=batch_size)
        return {
            "chunks_processed": stats["embedded"],
            "chunks_embedded": stats["embedded"],
            "papers_updated": 0,
            "errors": stats.get("errors", []),
        }
    
    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector
        """
        text = self._prepare_text(query, is_query=True)
        embeddings = await self._embed_batch([text])
        return embeddings[0]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts with retry."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    def _prepare_text(self, text: str, is_query: bool = False) -> str:
        """Preprocess text for embedding."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate if too long
        max_chars = self.MAX_TOKENS * 4
        if len(text) > max_chars:
            text = text[:max_chars]
        
        # Add context prefix for documents
        if not is_query and not text.startswith(self.CONTEXT_PREFIX):
            text = self.CONTEXT_PREFIX + text
        
        return text

    async def _mark_papers_embedded(self, ingest_job_id: Optional[str] = None) -> None:
        """Mark papers as embedded when all chunks have embeddings."""
        stmt = select(Paper).where(Paper.is_chunked == True)
        if ingest_job_id:
            job_uuid = uuid.UUID(ingest_job_id) if isinstance(ingest_job_id, str) else ingest_job_id
            stmt = stmt.where(Paper.ingest_job_id == job_uuid)
        
        result = await self.db.execute(stmt)
        papers = list(result.scalars().all())

        for paper in papers:
            chunk_count = await self.db.scalar(
                select(func.count(Chunk.id)).where(Chunk.paper_id == paper.id)
            )
            embedded_count = await self.db.scalar(
                select(func.count(Chunk.id))
                .where(Chunk.paper_id == paper.id)
                .where(Chunk.embedding.is_not(None))
            )
            if chunk_count and chunk_count == embedded_count:
                paper.is_embedded = True
                paper.updated_at = datetime.utcnow()
        
        await self.db.commit()

    async def get_embedding_stats(self) -> dict:
        """Get statistics about embeddings in the database."""
        total_chunks = await self.db.scalar(select(func.count(Chunk.id))) or 0
        embedded_chunks = await self.db.scalar(
            select(func.count(Chunk.id)).where(Chunk.embedding.is_not(None))
        ) or 0
        unembedded_chunks = total_chunks - embedded_chunks
        embedded_papers = await self.db.scalar(
            select(func.count(Paper.id)).where(Paper.is_embedded == True)
        ) or 0
        
        return {
            "total_chunks": total_chunks,
            "embedded_chunks": embedded_chunks,
            "unembedded_chunks": unembedded_chunks,
            "embedded_papers": embedded_papers,
            "embedding_model": self.model,
            "dimensions": self.dimensions,
        }
