"""
Chunking Service

Service for chunking papers and storing chunks in the database.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.models import Paper, Chunk
from app.services.chunking.chunker import TextChunker, ChunkResult


class ChunkingService:
    """
    Service for chunking papers and storing results.
    
    Handles:
    - Fetching unchunked papers from database
    - Chunking paper text (title + abstract)
    - Storing chunks in the chunks table
    - Updating paper status (is_chunked)
    """
    
    def __init__(self, db: AsyncSession, chunker: Optional[TextChunker] = None):
        """
        Initialize the chunking service.
        
        Args:
            db: Database session
            chunker: Optional custom TextChunker instance
        """
        self.db = db
        self.chunker = chunker or TextChunker()
    
    async def chunk_all_papers(
        self,
        batch_size: int = 100,
        limit: Optional[int] = None,
        ingest_job_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """
        Chunk all unchunked papers in the database.
        
        Args:
            batch_size: Number of papers to process at a time
            limit: Maximum total papers to process (None for all)
            
        Returns:
            Statistics about the chunking operation
        """
        stats = {
            "papers_processed": 0,
            "chunks_created": 0,
            "papers_skipped": 0,
            "errors": [],
        }
        
        offset = 0
        total_processed = 0
        
        while True:
            # Check limit
            if limit and total_processed >= limit:
                break
            
            # Fetch batch of unchunked papers with abstracts
            stmt = (
                select(Paper)
                .where(Paper.is_chunked == False)
                .where(Paper.abstract.isnot(None))
                .order_by(Paper.created_at)
                .offset(offset)
                .limit(batch_size)
            )
            if ingest_job_id:
                stmt = stmt.where(Paper.ingest_job_id == ingest_job_id)

            result = await self.db.execute(stmt)
            papers = list(result.scalars().all())
            
            if not papers:
                break
            
            # Process each paper
            for paper in papers:
                if limit and total_processed >= limit:
                    break
                
                try:
                    chunks_created = await self.chunk_paper(paper)
                    stats["papers_processed"] += 1
                    stats["chunks_created"] += chunks_created
                    total_processed += 1
                except Exception as e:
                    stats["errors"].append({
                        "paper_id": str(paper.id),
                        "error": str(e)
                    })
                    stats["papers_skipped"] += 1
            
            # Commit batch
            await self.db.commit()
            
            offset += batch_size
        
        return stats

    async def chunk_papers_for_job(self, ingest_job_id: uuid.UUID, batch_size: int = 100) -> dict:
        """Chunk papers belonging to a specific ingest job."""
        return await self.chunk_all_papers(batch_size=batch_size, ingest_job_id=ingest_job_id)
    
    async def chunk_paper(self, paper: Paper) -> int:
        """
        Chunk a single paper and store results.
        
        Args:
            paper: Paper model instance
            
        Returns:
            Number of chunks created
        """
        # Skip if no abstract
        if not paper.abstract:
            return 0
        
        # Skip if already chunked
        if paper.is_chunked:
            return 0
        
        # Delete any existing chunks (in case of re-processing)
        await self._delete_existing_chunks(paper.id)
        
        # Chunk the paper
        chunk_results = self.chunker.chunk_paper(
            title=paper.title,
            abstract=paper.abstract,
        )
        
        if not chunk_results:
            return 0
        
        # Store chunks
        for chunk_result in chunk_results:
            chunk = Chunk(
                id=uuid.uuid4(),
                paper_id=paper.id,
                text=chunk_result.text,
                chunk_index=chunk_result.chunk_index,
                section=chunk_result.section,
                token_count=chunk_result.token_count,
                char_count=chunk_result.char_count,
                embedding=None,  # Will be set by embedding service
                created_at=datetime.utcnow(),
            )
            self.db.add(chunk)
        
        # Mark paper as chunked
        paper.is_chunked = True
        paper.updated_at = datetime.utcnow()
        
        return len(chunk_results)
    
    async def chunk_paper_by_id(self, paper_id: uuid.UUID) -> int:
        """
        Chunk a paper by its ID.
        
        Args:
            paper_id: UUID of the paper
            
        Returns:
            Number of chunks created
        """
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = result.scalar_one_or_none()
        
        if not paper:
            raise ValueError(f"Paper not found: {paper_id}")
        
        chunks_created = await self.chunk_paper(paper)
        await self.db.commit()
        
        return chunks_created
    
    async def get_chunks_for_paper(
        self,
        paper_id: uuid.UUID,
    ) -> list[Chunk]:
        """
        Get all chunks for a paper.
        
        Args:
            paper_id: UUID of the paper
            
        Returns:
            List of Chunk model instances
        """
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.paper_id == paper_id)
            .order_by(Chunk.chunk_index)
        )
        return list(result.scalars().all())
    
    async def get_unchunked_count(self) -> int:
        """Get count of papers that haven't been chunked."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Paper.id))
            .where(Paper.is_chunked == False)
            .where(Paper.abstract.isnot(None))
        )
        return result.scalar_one()
    
    async def get_chunk_stats(self) -> dict:
        """Get statistics about chunks in the database."""
        from sqlalchemy import func
        
        # Total chunks
        total_result = await self.db.execute(
            select(func.count(Chunk.id))
        )
        total_chunks = total_result.scalar_one()
        
        # Chunks with embeddings
        embedded_result = await self.db.execute(
            select(func.count(Chunk.id))
            .where(Chunk.embedding.isnot(None))
        )
        embedded_chunks = embedded_result.scalar_one()
        
        # Average tokens per chunk
        avg_tokens_result = await self.db.execute(
            select(func.avg(Chunk.token_count))
        )
        avg_tokens = avg_tokens_result.scalar_one() or 0
        
        # Chunked papers count
        chunked_papers_result = await self.db.execute(
            select(func.count(Paper.id))
            .where(Paper.is_chunked == True)
        )
        chunked_papers = chunked_papers_result.scalar_one()
        
        return {
            "total_chunks": total_chunks,
            "embedded_chunks": embedded_chunks,
            "avg_tokens_per_chunk": round(float(avg_tokens), 1),
            "chunked_papers": chunked_papers,
        }
    
    async def _delete_existing_chunks(self, paper_id: uuid.UUID):
        """Delete existing chunks for a paper (for re-processing)."""
        from sqlalchemy import delete
        await self.db.execute(
            delete(Chunk).where(Chunk.paper_id == paper_id)
        )


async def chunk_papers_batch(
    db: AsyncSession,
    paper_ids: list[uuid.UUID],
) -> dict:
    """
    Convenience function to chunk a specific batch of papers.
    
    Args:
        db: Database session
        paper_ids: List of paper UUIDs to chunk
        
    Returns:
        Statistics about the operation
    """
    service = ChunkingService(db)
    stats = {
        "papers_processed": 0,
        "chunks_created": 0,
        "errors": [],
    }
    
    for paper_id in paper_ids:
        try:
            chunks = await service.chunk_paper_by_id(paper_id)
            stats["papers_processed"] += 1
            stats["chunks_created"] += chunks
        except Exception as e:
            stats["errors"].append({
                "paper_id": str(paper_id),
                "error": str(e)
            })
    
    return stats
