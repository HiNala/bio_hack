"""
Embedding Service

Generates vector embeddings for text chunks.
"""

from typing import Callable, Optional, Awaitable
import uuid
import inspect
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from openai import AsyncOpenAI

from app.config import get_settings
from app.models import Chunk, Paper

settings = get_settings()


class EmbeddingService:
    """Service for creating embeddings and storing them in pgvector."""

    def __init__(self, db: AsyncSession):
        self.db = db
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed_unembedded_chunks(
        self,
        ingest_job_id: Optional[uuid.UUID] = None,
        batch_size: int = 100,
        progress_callback: Optional[Callable[[int, int], Awaitable[None] | None]] = None,
    ) -> dict:
        """
        Embed all chunks without embeddings.
        """
        stats = {
            "embedded": 0,
            "total": 0,
            "errors": [],
        }

        # Count total chunks to embed
        count_stmt = select(func.count(Chunk.id)).where(Chunk.embedding.is_(None))
        if ingest_job_id:
            count_stmt = count_stmt.join(Paper).where(Paper.ingest_job_id == ingest_job_id)
        total = await self.db.scalar(count_stmt)
        stats["total"] = total or 0

        if not stats["total"]:
            return stats

        offset = 0
        while True:
            stmt = select(Chunk).where(Chunk.embedding.is_(None))
            if ingest_job_id:
                stmt = stmt.join(Paper).where(Paper.ingest_job_id == ingest_job_id)
            stmt = stmt.order_by(Chunk.created_at).offset(offset).limit(batch_size)

            result = await self.db.execute(stmt)
            chunks = list(result.scalars().all())
            if not chunks:
                break

            inputs = [self._prepare_text(c.text) for c in chunks]
            try:
                response = await self.client.embeddings.create(
                    model=settings.embedding_model,
                    input=inputs,
                )
                vectors = [item.embedding for item in response.data]

                # Store embeddings
                for chunk, vector in zip(chunks, vectors):
                    chunk.embedding = vector

                stats["embedded"] += len(chunks)
                await self.db.commit()

                if progress_callback:
                    result = progress_callback(stats["embedded"], stats["total"])
                    if inspect.isawaitable(result):
                        await result

            except Exception as exc:
                stats["errors"].append(str(exc))
                await self.db.rollback()

            offset += batch_size

        # Mark papers as embedded when all chunks are embedded
        await self._mark_papers_embedded(ingest_job_id)

        return stats

    async def embed_all_chunks(self, batch_size: int = 100, limit: Optional[int] = None) -> dict:
        """Compatibility wrapper for embedding all chunks."""
        stats = await self.embed_unembedded_chunks(batch_size=batch_size)
        return {
            "chunks_processed": stats["embedded"],
            "chunks_embedded": stats["embedded"],
            "papers_updated": 0,
            "errors": stats.get("errors", []),
        }

    async def get_embedding_stats(self) -> dict:
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
            "embedding_model": settings.embedding_model,
            "dimensions": settings.embedding_dimensions,
        }

    async def embed_query(self, query: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=[self._prepare_text(query)],
        )
        return response.data[0].embedding

    def _prepare_text(self, text: str) -> str:
        return f"Scientific paper excerpt: {text}"

    async def _mark_papers_embedded(self, ingest_job_id: Optional[uuid.UUID] = None) -> None:
        # Find papers where all chunks have embeddings
        stmt = select(Paper).where(Paper.is_chunked == True)
        if ingest_job_id:
            stmt = stmt.where(Paper.ingest_job_id == ingest_job_id)
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
"""
Embedding Service

Generates and stores vector embeddings using OpenAI's text-embedding-3-small model.
"""

import uuid
from typing import Optional
from datetime import datetime

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
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
    - Progress tracking
    """
    
    # Batch size for OpenAI API calls
    BATCH_SIZE = 100
    
    # Max tokens for embedding model
    MAX_TOKENS = 8191
    
    # Context prefix for better embeddings
    CONTEXT_PREFIX = "Scientific paper excerpt: "
    
    def __init__(self, db: AsyncSession):
        """
        Initialize embedding service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
    
    async def embed_all_chunks(
        self,
        batch_size: int = None,
        limit: Optional[int] = None,
    ) -> dict:
        """
        Embed all chunks that don't have embeddings yet.
        
        Args:
            batch_size: Number of chunks per API call
            limit: Maximum total chunks to process
            
        Returns:
            Statistics about the embedding operation
        """
        batch_size = batch_size or self.BATCH_SIZE
        
        stats = {
            "chunks_processed": 0,
            "chunks_embedded": 0,
            "papers_updated": 0,
            "errors": [],
        }
        
        offset = 0
        total_processed = 0
        
        while True:
            if limit and total_processed >= limit:
                break
            
            # Fetch batch of un-embedded chunks
            result = await self.db.execute(
                select(Chunk)
                .where(Chunk.embedding.is_(None))
                .order_by(Chunk.created_at)
                .offset(offset)
                .limit(batch_size)
            )
            chunks = list(result.scalars().all())
            
            if not chunks:
                break
            
            # Prepare texts for embedding
            texts = []
            for chunk in chunks:
                text = self._preprocess_text(chunk.text)
                texts.append(text)
            
            # Generate embeddings
            try:
                embeddings = await self._embed_batch(texts)
                
                # Store embeddings
                for chunk, embedding in zip(chunks, embeddings):
                    chunk.embedding = embedding
                    stats["chunks_embedded"] += 1
                
                await self.db.commit()
                
            except Exception as e:
                stats["errors"].append({
                    "batch_offset": offset,
                    "error": str(e)
                })
                # Continue with next batch
            
            stats["chunks_processed"] += len(chunks)
            total_processed += len(chunks)
            offset += batch_size
        
        # Update paper is_embedded status
        papers_updated = await self._update_paper_status()
        stats["papers_updated"] = papers_updated
        
        return stats
    
    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector
        """
        # Preprocess query
        text = self._preprocess_text(query, is_query=True)
        
        # Generate embedding
        embeddings = await self._embed_batch([text])
        return embeddings[0]
    
    async def embed_chunk_by_id(self, chunk_id: uuid.UUID) -> bool:
        """
        Generate embedding for a specific chunk.
        
        Args:
            chunk_id: UUID of the chunk
            
        Returns:
            True if successful
        """
        result = await self.db.execute(
            select(Chunk).where(Chunk.id == chunk_id)
        )
        chunk = result.scalar_one_or_none()
        
        if not chunk:
            raise ValueError(f"Chunk not found: {chunk_id}")
        
        text = self._preprocess_text(chunk.text)
        embeddings = await self._embed_batch([text])
        
        chunk.embedding = embeddings[0]
        await self.db.commit()
        
        return True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Uses retry logic for resilience.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )
        
        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]
    
    def _preprocess_text(self, text: str, is_query: bool = False) -> str:
        """
        Preprocess text for embedding.
        
        Args:
            text: Raw text
            is_query: Whether this is a search query
            
        Returns:
            Preprocessed text
        """
        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate if too long (rough estimate: 4 chars per token)
        max_chars = self.MAX_TOKENS * 4
        if len(text) > max_chars:
            text = text[:max_chars]
        
        # Add context prefix for documents (not queries)
        if not is_query and not text.startswith(self.CONTEXT_PREFIX):
            text = self.CONTEXT_PREFIX + text
        
        return text
    
    async def _update_paper_status(self) -> int:
        """
        Update is_embedded status for papers where all chunks are embedded.
        
        Returns:
            Number of papers updated
        """
        # Find papers where all chunks have embeddings
        # This is a bit complex in SQL, so we do it in steps
        
        # Get papers that have chunks
        papers_with_chunks = await self.db.execute(
            select(Chunk.paper_id).distinct()
        )
        paper_ids = [row[0] for row in papers_with_chunks]
        
        updated_count = 0
        
        for paper_id in paper_ids:
            # Check if all chunks have embeddings
            total_result = await self.db.execute(
                select(func.count(Chunk.id))
                .where(Chunk.paper_id == paper_id)
            )
            total_chunks = total_result.scalar_one()
            
            embedded_result = await self.db.execute(
                select(func.count(Chunk.id))
                .where(Chunk.paper_id == paper_id)
                .where(Chunk.embedding.isnot(None))
            )
            embedded_chunks = embedded_result.scalar_one()
            
            if total_chunks > 0 and total_chunks == embedded_chunks:
                await self.db.execute(
                    update(Paper)
                    .where(Paper.id == paper_id)
                    .where(Paper.is_embedded == False)
                    .values(is_embedded=True, updated_at=datetime.utcnow())
                )
                updated_count += 1
        
        await self.db.commit()
        return updated_count
    
    async def get_embedding_stats(self) -> dict:
        """Get statistics about embeddings."""
        # Total chunks
        total_result = await self.db.execute(
            select(func.count(Chunk.id))
        )
        total_chunks = total_result.scalar_one()
        
        # Embedded chunks
        embedded_result = await self.db.execute(
            select(func.count(Chunk.id))
            .where(Chunk.embedding.isnot(None))
        )
        embedded_chunks = embedded_result.scalar_one()
        
        # Embedded papers
        embedded_papers_result = await self.db.execute(
            select(func.count(Paper.id))
            .where(Paper.is_embedded == True)
        )
        embedded_papers = embedded_papers_result.scalar_one()
        
        return {
            "total_chunks": total_chunks,
            "embedded_chunks": embedded_chunks,
            "unembedded_chunks": total_chunks - embedded_chunks,
            "embedded_papers": embedded_papers,
            "embedding_model": self.model,
            "dimensions": self.dimensions,
        }
