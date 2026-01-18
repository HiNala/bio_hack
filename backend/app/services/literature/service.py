"""
Literature Service

Orchestrates paper fetching from multiple sources with deduplication.
"""

import asyncio
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models import Paper, Source
from app.services.literature.openalex import OpenAlexClient
from app.services.literature.semantic_scholar import SemanticScholarClient
from app.services.literature.models import UnifiedPaper


class LiteratureService:
    """
    Orchestrates paper fetching from multiple literature sources.
    
    Responsibilities:
    - Coordinate searches across OpenAlex and Semantic Scholar
    - Deduplicate papers by DOI
    - Normalize and store papers in the database
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openalex = OpenAlexClient()
        self.semantic_scholar = SemanticScholarClient()
        
        # Track seen DOIs for deduplication
        self._seen_dois: set[str] = set()
        
        # Cache source IDs
        self._source_ids: dict[str, uuid.UUID] = {}
    
    async def search_and_store(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        max_per_source: int = 50,
        sources: Optional[list[str]] = None,
        ingest_job_id: Optional[uuid.UUID] = None,
        progress_callback: Optional[callable] = None,
    ) -> dict:
        """
        Search multiple sources and store unique papers.
        
        Args:
            query: Search query string
            year_from: Minimum publication year
            year_to: Maximum publication year
            max_per_source: Max papers to fetch from each source
            
        Returns:
            Dictionary with statistics about the operation
        """
        # Reset deduplication tracking for this search
        self._seen_dois.clear()
        
        # Load existing DOIs from database to avoid re-adding
        await self._load_existing_dois()
        
        # Ensure source records exist
        await self._ensure_sources()
        
        sources = sources or ["openalex", "semantic_scholar"]

        # Fetch from sources concurrently
        tasks = []
        if "openalex" in sources:
            tasks.append(self._fetch_from_openalex(query, year_from, year_to, max_per_source))
        else:
            tasks.append([])
        if "semantic_scholar" in sources:
            tasks.append(self._fetch_from_semantic_scholar(query, year_from, year_to, max_per_source))
        else:
            tasks.append([])
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        stats = {
            "query": query,
            "openalex": {"found": 0, "stored": 0, "errors": None},
            "semantic_scholar": {"found": 0, "stored": 0, "errors": None},
            "total_stored": 0,
            "duplicates_skipped": 0,
        }
        
        all_papers = []
        
        # Process OpenAlex results
        if isinstance(results[0], Exception):
            stats["openalex"]["errors"] = str(results[0])
        else:
            openalex_papers = results[0]
            stats["openalex"]["found"] = len(openalex_papers)
            for paper in openalex_papers:
                if self._is_duplicate(paper):
                    stats["duplicates_skipped"] += 1
                else:
                    all_papers.append(paper)
                    stats["openalex"]["stored"] += 1
        
        # Process Semantic Scholar results
        if isinstance(results[1], Exception):
            stats["semantic_scholar"]["errors"] = str(results[1])
        else:
            s2_papers = results[1]
            stats["semantic_scholar"]["found"] = len(s2_papers)
            for paper in s2_papers:
                if self._is_duplicate(paper):
                    stats["duplicates_skipped"] += 1
                else:
                    all_papers.append(paper)
                    stats["semantic_scholar"]["stored"] += 1
        
        # Store papers in database
        if all_papers:
            await self._store_papers(all_papers, ingest_job_id=ingest_job_id)
        
        stats["total_stored"] = len(all_papers)

        if progress_callback:
            progress_callback({
                "openalex_found": stats["openalex"]["found"],
                "semantic_scholar_found": stats["semantic_scholar"]["found"],
                "duplicates_removed": stats["duplicates_skipped"],
                "unique_papers": stats["total_stored"],
                "papers_stored": stats["total_stored"],
            })
        
        return stats

    async def search_and_store_multi(
        self,
        queries: list[str],
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        max_per_source: int = 50,
        sources: Optional[list[str]] = None,
        ingest_job_id: Optional[uuid.UUID] = None,
        progress_callback: Optional[callable] = None,
    ) -> dict:
        """
        Run multiple queries and store deduplicated results.
        """
        combined_stats = {
            "openalex": {"found": 0, "stored": 0, "errors": None},
            "semantic_scholar": {"found": 0, "stored": 0, "errors": None},
            "total_stored": 0,
            "duplicates_skipped": 0,
        }

        for query in queries:
            stats = await self.search_and_store(
                query=query,
                year_from=year_from,
                year_to=year_to,
                max_per_source=max_per_source,
                sources=sources,
                ingest_job_id=ingest_job_id,
                progress_callback=None,
            )
            combined_stats["openalex"]["found"] += stats["openalex"]["found"]
            combined_stats["semantic_scholar"]["found"] += stats["semantic_scholar"]["found"]
            combined_stats["openalex"]["stored"] += stats["openalex"]["stored"]
            combined_stats["semantic_scholar"]["stored"] += stats["semantic_scholar"]["stored"]
            combined_stats["duplicates_skipped"] += stats["duplicates_skipped"]
            combined_stats["total_stored"] += stats["total_stored"]

        if progress_callback:
            progress_callback({
                "openalex_found": combined_stats["openalex"]["found"],
                "semantic_scholar_found": combined_stats["semantic_scholar"]["found"],
                "duplicates_removed": combined_stats["duplicates_skipped"],
                "unique_papers": combined_stats["total_stored"],
                "papers_stored": combined_stats["total_stored"],
            })

        return combined_stats
    
    async def _fetch_from_openalex(
        self,
        query: str,
        year_from: Optional[int],
        year_to: Optional[int],
        limit: int,
    ) -> list[UnifiedPaper]:
        """Fetch papers from OpenAlex."""
        try:
            result = await self.openalex.search(
                query=query,
                year_from=year_from,
                year_to=year_to,
                per_page=limit,
            )
            # Filter to papers with abstracts
            return [p for p in result.papers if p.has_abstract()]
        except Exception as e:
            print(f"OpenAlex fetch error: {e}")
            raise
    
    async def _fetch_from_semantic_scholar(
        self,
        query: str,
        year_from: Optional[int],
        year_to: Optional[int],
        limit: int,
    ) -> list[UnifiedPaper]:
        """Fetch papers from Semantic Scholar."""
        try:
            result = await self.semantic_scholar.search(
                query=query,
                year_from=year_from,
                year_to=year_to,
                limit=limit,
            )
            # Filter to papers with abstracts
            return [p for p in result.papers if p.has_abstract()]
        except Exception as e:
            print(f"Semantic Scholar fetch error: {e}")
            raise
    
    def _is_duplicate(self, paper: UnifiedPaper) -> bool:
        """
        Check if paper is a duplicate based on DOI.
        
        Also marks the DOI as seen for future checks.
        """
        if paper.doi:
            normalized_doi = paper.doi.lower().strip()
            if normalized_doi in self._seen_dois:
                return True
            self._seen_dois.add(normalized_doi)
        
        return False
    
    async def _load_existing_dois(self):
        """Load existing DOIs from database for deduplication."""
        result = await self.db.execute(
            select(Paper.doi).where(Paper.doi.isnot(None))
        )
        for row in result:
            if row[0]:
                self._seen_dois.add(row[0].lower().strip())
    
    async def _ensure_sources(self):
        """Ensure source records exist and cache their IDs."""
        sources_data = [
            ("openalex", "OpenAlex", "https://api.openalex.org"),
            ("semantic_scholar", "Semantic Scholar", "https://api.semanticscholar.org"),
        ]
        
        for key, name, base_url in sources_data:
            # Check if source exists
            result = await self.db.execute(
                select(Source).where(Source.name == name)
            )
            source = result.scalar_one_or_none()
            
            if source:
                self._source_ids[key] = source.id
            else:
                # Create source
                source = Source(
                    name=name,
                    base_url=base_url,
                    is_active=True,
                    created_at=datetime.utcnow(),
                )
                self.db.add(source)
                await self.db.flush()
                self._source_ids[key] = source.id
        
        await self.db.commit()
    
    async def _store_papers(self, papers: list[UnifiedPaper], ingest_job_id: Optional[uuid.UUID] = None):
        """
        Store papers in the database.
        
        Uses upsert to handle any remaining duplicates gracefully.
        """
        for paper in papers:
            source_id = self._source_ids.get(paper.source)
            if not source_id:
                continue
            
            # Prepare paper data
            paper_data = {
                "id": uuid.uuid4(),
                "source_id": source_id,
                "ingest_job_id": ingest_job_id,
                "external_id": paper.external_id,
                "doi": paper.doi,
                "title": paper.title,
                "abstract": paper.abstract,
                "authors": paper.get_author_names(),
                "year": paper.year,
                "venue": paper.venue,
                "topics": paper.topics,
                "fields_of_study": paper.fields_of_study,
                "citation_count": paper.citation_count,
                "pdf_url": paper.pdf_url,
                "landing_url": paper.landing_url,
                "is_chunked": False,
                "is_embedded": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            # Use INSERT ... ON CONFLICT DO NOTHING for deduplication
            stmt = insert(Paper).values(**paper_data)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_paper_source_external"
            )
            
            await self.db.execute(stmt)
        
        await self.db.commit()
    
    async def get_papers_by_query_terms(
        self,
        terms: list[str],
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get stored papers matching search terms.
        
        This is for retrieving previously ingested papers.
        """
        # Simple title/abstract search for now
        # Could be enhanced with full-text search
        result = await self.db.execute(
            select(Paper)
            .where(Paper.abstract.isnot(None))
            .order_by(Paper.citation_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
