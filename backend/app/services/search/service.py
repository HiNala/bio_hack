"""
Search Service

Semantic vector search over embedded chunks using pgvector.
"""

import math
from typing import Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, bindparam
from sqlalchemy.orm import joinedload

from app.models import Chunk, Paper
from app.services.embedding import EmbeddingService
from app.config import get_settings

settings = get_settings()


@dataclass
class SearchResult:
    """Single search result with metadata."""
    chunk_id: str
    paper_id: str
    paper_title: str
    paper_year: Optional[int]
    paper_authors: list[str]
    paper_citation_count: int
    paper_doi: Optional[str]
    paper_url: Optional[str]
    chunk_text: str
    chunk_section: Optional[str]
    similarity_score: float
    final_score: float


class SearchService:
    """
    Semantic search service using pgvector.
    
    Features:
    - Cosine similarity search
    - Ranking by relevance + recency + citations
    - Deduplication across papers
    - Configurable result limits
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize search service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = EmbeddingService(db)
    
    async def search(
        self,
        query: str,
        top_k: int = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        dedupe_papers: bool = True,
    ) -> list[SearchResult]:
        """
        Perform semantic search over embedded chunks.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            year_from: Minimum publication year
            year_to: Maximum publication year
            dedupe_papers: If True, return only top chunk per paper
            
        Returns:
            List of SearchResult objects
        """
        top_k = top_k or settings.retrieval_top_k
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)
        
        # Format embedding as PostgreSQL vector literal
        embedding_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Build query with proper parameter escaping
        # Note: We embed the vector directly in the SQL to avoid parameter binding issues with pgvector
        limit = top_k * 3 if dedupe_papers else top_k
        
        # Build WHERE clause dynamically
        where_clauses = ["c.embedding IS NOT NULL"]
        params = {"limit_val": limit}
        
        if year_from is not None:
            where_clauses.append("p.year >= :year_from")
            params["year_from"] = year_from
        
        if year_to is not None:
            where_clauses.append("p.year <= :year_to")
            params["year_to"] = year_to
        
        where_sql = " AND ".join(where_clauses)
        
        # Use string formatting for the embedding vector (safe since we control it)
        sql = text(f"""
            SELECT 
                c.id as chunk_id,
                c.paper_id,
                c.text as chunk_text,
                c.section as chunk_section,
                p.title as paper_title,
                p.year as paper_year,
                p.authors as paper_authors,
                p.citation_count as paper_citation_count,
                p.doi as paper_doi,
                p.landing_url as paper_url,
                1 - (c.embedding <=> '{embedding_literal}'::vector) as similarity
            FROM chunks c
            JOIN papers p ON c.paper_id = p.id
            WHERE {where_sql}
            ORDER BY c.embedding <=> '{embedding_literal}'::vector
            LIMIT :limit_val
        """)
        
        result = await self.db.execute(sql, params)
        rows = result.fetchall()
        
        # Process results with ranking
        results = []
        seen_papers = set()
        
        for row in rows:
            paper_id = str(row.paper_id)
            
            # Dedupe by paper
            if dedupe_papers and paper_id in seen_papers:
                continue
            seen_papers.add(paper_id)
            
            # Calculate final score with boosts
            similarity = float(row.similarity)
            final_score = self._calculate_score(
                similarity=similarity,
                year=row.paper_year,
                citation_count=row.paper_citation_count,
            )
            
            results.append(SearchResult(
                chunk_id=str(row.chunk_id),
                paper_id=paper_id,
                paper_title=row.paper_title,
                paper_year=row.paper_year,
                paper_authors=row.paper_authors if isinstance(row.paper_authors, list) else [],
                paper_citation_count=row.paper_citation_count or 0,
                paper_doi=row.paper_doi,
                paper_url=row.paper_url,
                chunk_text=row.chunk_text,
                chunk_section=row.chunk_section,
                similarity_score=similarity,
                final_score=final_score,
            ))
            
            if len(results) >= top_k:
                break
        
        # Sort by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        return results
    
    async def search_by_embedding(
        self,
        embedding: list[float],
        top_k: int = None,
    ) -> list[SearchResult]:
        """
        Search using a pre-computed embedding.
        
        Args:
            embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        top_k = top_k or settings.retrieval_top_k
        
        embedding_literal = "[" + ",".join(str(x) for x in embedding) + "]"
        
        sql = text(f"""
            SELECT 
                c.id as chunk_id,
                c.paper_id,
                c.text as chunk_text,
                c.section as chunk_section,
                p.title as paper_title,
                p.year as paper_year,
                p.authors as paper_authors,
                p.citation_count as paper_citation_count,
                p.doi as paper_doi,
                p.landing_url as paper_url,
                1 - (c.embedding <=> '{embedding_literal}'::vector) as similarity
            FROM chunks c
            JOIN papers p ON c.paper_id = p.id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <=> '{embedding_literal}'::vector
            LIMIT :limit_val
        """)
        
        result = await self.db.execute(sql, {"limit_val": top_k})
        rows = result.fetchall()
        
        results = []
        for row in rows:
            similarity = float(row.similarity)
            final_score = self._calculate_score(
                similarity=similarity,
                year=row.paper_year,
                citation_count=row.paper_citation_count,
            )
            
            results.append(SearchResult(
                chunk_id=str(row.chunk_id),
                paper_id=str(row.paper_id),
                paper_title=row.paper_title,
                paper_year=row.paper_year,
                paper_authors=row.paper_authors if isinstance(row.paper_authors, list) else [],
                paper_citation_count=row.paper_citation_count or 0,
                paper_doi=row.paper_doi,
                paper_url=row.paper_url,
                chunk_text=row.chunk_text,
                chunk_section=row.chunk_section,
                similarity_score=similarity,
                final_score=final_score,
            ))
        
        return results
    
    def _calculate_score(
        self,
        similarity: float,
        year: Optional[int],
        citation_count: int,
    ) -> float:
        """
        Calculate final ranking score.
        
        Formula: similarity * (1 + log(citations + 1) * 0.1) * recency_factor
        
        Args:
            similarity: Cosine similarity (0-1)
            year: Publication year
            citation_count: Number of citations
            
        Returns:
            Final score
        """
        # Citation boost: log scale to avoid outliers dominating
        citation_boost = 1 + math.log(citation_count + 1) * 0.1
        
        # Recency factor
        if year is None:
            recency_factor = 0.85
        elif year >= 2020:
            recency_factor = 1.0
        elif year >= 2015:
            recency_factor = 0.95
        elif year >= 2010:
            recency_factor = 0.9
        else:
            recency_factor = 0.85
        
        return similarity * citation_boost * recency_factor
    
    async def get_search_stats(self) -> dict:
        """Get statistics about searchable content."""
        # Total embedded chunks
        embedded_result = await self.db.execute(
            select(func.count(Chunk.id))
            .where(Chunk.embedding.isnot(None))
        )
        embedded_chunks = embedded_result.scalar_one()
        
        # Total embedded papers
        embedded_papers_result = await self.db.execute(
            select(func.count(Paper.id))
            .where(Paper.is_embedded == True)
        )
        embedded_papers = embedded_papers_result.scalar_one()
        
        return {
            "searchable_chunks": embedded_chunks,
            "searchable_papers": embedded_papers,
            "index_type": "HNSW",
            "distance_metric": "cosine",
        }
