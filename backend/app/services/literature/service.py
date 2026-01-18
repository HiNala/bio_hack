"""
Literature Service

Orchestrates paper fetching from multiple sources with intelligent
deduplication, normalization, and storage.
"""

import asyncio
import uuid
from typing import Optional, List, Callable, Awaitable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models import Paper, Source
from app.services.literature.openalex import OpenAlexClient
from app.services.literature.semantic_scholar import SemanticScholarClient
from app.services.literature.models import UnifiedPaper
from app.services.literature.deduplicator import PaperDeduplicator


class LiteratureService:
    """
    Orchestrates paper fetching from multiple literature sources.
    
    Responsibilities:
    - Coordinate searches across OpenAlex and Semantic Scholar
    - Deduplicate papers using DOI and fuzzy title matching
    - Normalize and store papers in the database
    - Handle partial failures gracefully
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openalex = OpenAlexClient()
        self.semantic_scholar = SemanticScholarClient()
        self.deduplicator = PaperDeduplicator()
        
        # Cache source IDs
        self._source_ids: dict[str, uuid.UUID] = {}
    
    async def search_and_store(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        max_per_source: int = 50,
        sources: Optional[List[str]] = None,
        ingest_job_id: Optional[uuid.UUID] = None,
        progress_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """
        Search multiple sources and store unique papers.
        
        Args:
            query: Search query string
            year_from: Minimum publication year
            year_to: Maximum publication year
            max_per_source: Max papers to fetch from each source
            sources: List of sources to query
            ingest_job_id: Job ID for tracking
            progress_callback: Async callback for progress updates
            
        Returns:
            Dictionary with statistics about the operation
        """
        # Ensure source records exist
        await self._ensure_sources()
        
        sources = sources or ["openalex", "semantic_scholar"]
        
        stats = {
            "query": query,
            "openalex": {"found": 0, "stored": 0, "errors": None},
            "semantic_scholar": {"found": 0, "stored": 0, "errors": None},
            "total_stored": 0,
            "duplicates_skipped": 0,
            "fetch_errors": [],
        }
        
        # Fetch from sources in parallel with fault tolerance
        all_papers: List[UnifiedPaper] = []
        
        tasks = []
        if "openalex" in sources:
            tasks.append(("openalex", self._fetch_from_openalex(
                query, year_from, year_to, max_per_source
            )))
        if "semantic_scholar" in sources:
            tasks.append(("semantic_scholar", self._fetch_from_semantic_scholar(
                query, year_from, year_to, max_per_source
            )))
        
        # Execute with individual error handling
        results = await asyncio.gather(
            *[self._safe_fetch(name, task) for name, task in tasks],
            return_exceptions=False
        )
        
        for source_name, papers, error in results:
            if error:
                stats[source_name]["errors"] = str(error)
                stats["fetch_errors"].append({"source": source_name, "error": str(error)})
            else:
                stats[source_name]["found"] = len(papers)
                all_papers.extend(papers)
        
        # Report progress: fetching complete
        if progress_callback:
            await progress_callback({
                "stage": "fetching_complete",
                "openalex_found": stats["openalex"]["found"],
                "semantic_scholar_found": stats["semantic_scholar"]["found"],
            })
        
        # Deduplicate papers
        if all_papers:
            dedup_result = self.deduplicator.deduplicate(all_papers)
            unique_papers = dedup_result.papers
            stats["duplicates_skipped"] = dedup_result.duplicates_removed
            
            # Report progress: deduplication complete
            if progress_callback:
                await progress_callback({
                    "stage": "deduplication_complete",
                    "unique_papers": dedup_result.unique_count,
                    "duplicates_removed": dedup_result.duplicates_removed,
                })
            
            # Load existing DOIs to avoid re-storing
            existing_dois = await self._load_existing_dois()
            
            # Filter out already stored papers
            new_papers = []
            for paper in unique_papers:
                if paper.doi and paper.doi.lower() in existing_dois:
                    stats["duplicates_skipped"] += 1
                else:
                    new_papers.append(paper)
            
            # Store new papers
            if new_papers:
                stored_count = await self._store_papers(new_papers, ingest_job_id)
                stats["total_stored"] = stored_count
                
                # Update per-source stats
                for paper in new_papers:
                    stats[paper.source]["stored"] += 1
            
            # Report progress: storing complete
            if progress_callback:
                await progress_callback({
                    "stage": "storing_complete",
                    "papers_stored": stats["total_stored"],
                })
        
        return stats
    
    async def search_and_store_multi(
        self,
        queries: List[str],
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        max_per_source: int = 50,
        sources: Optional[List[str]] = None,
        ingest_job_id: Optional[uuid.UUID] = None,
        progress_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """
        Run multiple queries and store deduplicated results.
        
        This is more efficient than calling search_and_store multiple times
        because it deduplicates across all queries.
        """
        # Ensure source records exist
        await self._ensure_sources()
        
        sources = sources or ["openalex", "semantic_scholar"]
        
        combined_stats = {
            "openalex": {"found": 0, "stored": 0, "errors": None},
            "semantic_scholar": {"found": 0, "stored": 0, "errors": None},
            "total_stored": 0,
            "duplicates_skipped": 0,
            "queries_processed": 0,
            "fetch_errors": [],
        }
        
        # Collect all papers from all queries
        all_papers: List[UnifiedPaper] = []
        
        for query in queries:
            tasks = []
            if "openalex" in sources:
                tasks.append(("openalex", self._fetch_from_openalex(
                    query, year_from, year_to, max_per_source
                )))
            if "semantic_scholar" in sources:
                tasks.append(("semantic_scholar", self._fetch_from_semantic_scholar(
                    query, year_from, year_to, max_per_source
                )))
            
            results = await asyncio.gather(
                *[self._safe_fetch(name, task) for name, task in tasks],
                return_exceptions=False
            )
            
            for source_name, papers, error in results:
                if error:
                    if not combined_stats[source_name]["errors"]:
                        combined_stats[source_name]["errors"] = str(error)
                    combined_stats["fetch_errors"].append({
                        "source": source_name,
                        "query": query,
                        "error": str(error)
                    })
                else:
                    combined_stats[source_name]["found"] += len(papers)
                    all_papers.extend(papers)
            
            combined_stats["queries_processed"] += 1
        
        # Report progress: fetching complete
        if progress_callback:
            await progress_callback({
                "stage": "fetching_complete",
                "openalex_found": combined_stats["openalex"]["found"],
                "semantic_scholar_found": combined_stats["semantic_scholar"]["found"],
            })
        
        # Deduplicate all papers
        if all_papers:
            dedup_result = self.deduplicator.deduplicate(all_papers)
            unique_papers = dedup_result.papers
            combined_stats["duplicates_skipped"] = dedup_result.duplicates_removed
            
            # Report progress: deduplication complete
            if progress_callback:
                await progress_callback({
                    "stage": "deduplication_complete",
                    "unique_papers": dedup_result.unique_count,
                    "duplicates_removed": dedup_result.duplicates_removed,
                })
            
            # Load existing DOIs
            existing_dois = await self._load_existing_dois()
            
            # Filter out already stored
            new_papers = []
            for paper in unique_papers:
                if paper.doi and paper.doi.lower() in existing_dois:
                    combined_stats["duplicates_skipped"] += 1
                else:
                    new_papers.append(paper)
            
            # Store new papers
            if new_papers:
                stored_count = await self._store_papers(new_papers, ingest_job_id)
                combined_stats["total_stored"] = stored_count
                
                for paper in new_papers:
                    combined_stats[paper.source]["stored"] += 1
            
            # Report progress: storing complete
            if progress_callback:
                await progress_callback({
                    "stage": "storing_complete",
                    "papers_stored": combined_stats["total_stored"],
                })
        
        return combined_stats
    
    async def _safe_fetch(
        self,
        source_name: str,
        fetch_coro,
    ) -> tuple:
        """Wrap a fetch coroutine to catch exceptions."""
        try:
            papers = await fetch_coro
            return (source_name, papers, None)
        except asyncio.TimeoutError:
            return (source_name, [], Exception(f"Timeout fetching from {source_name}"))
        except Exception as e:
            return (source_name, [], e)
    
    async def _fetch_from_openalex(
        self,
        query: str,
        year_from: Optional[int],
        year_to: Optional[int],
        limit: int,
    ) -> List[UnifiedPaper]:
        """Fetch papers from OpenAlex."""
        result = await self.openalex.search(
            query=query,
            year_from=year_from,
            year_to=year_to,
            per_page=limit,
        )
        # Filter to papers with abstracts
        return [p for p in result.papers if p.has_abstract()]
    
    async def _fetch_from_semantic_scholar(
        self,
        query: str,
        year_from: Optional[int],
        year_to: Optional[int],
        limit: int,
    ) -> List[UnifiedPaper]:
        """Fetch papers from Semantic Scholar."""
        result = await self.semantic_scholar.search(
            query=query,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
        )
        return [p for p in result.papers if p.has_abstract()]
    
    async def _load_existing_dois(self) -> set:
        """Load existing DOIs from database for deduplication."""
        result = await self.db.execute(
            select(Paper.doi).where(Paper.doi.isnot(None))
        )
        return {row[0].lower().strip() for row in result if row[0]}
    
    async def _ensure_sources(self):
        """Ensure source records exist and cache their IDs."""
        sources_data = [
            ("openalex", "OpenAlex", "https://api.openalex.org"),
            ("semantic_scholar", "Semantic Scholar", "https://api.semanticscholar.org"),
        ]
        
        for key, name, base_url in sources_data:
            result = await self.db.execute(
                select(Source).where(Source.name == name)
            )
            source = result.scalar_one_or_none()
            
            if source:
                self._source_ids[key] = source.id
            else:
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
    
    async def _store_papers(
        self,
        papers: List[UnifiedPaper],
        ingest_job_id: Optional[uuid.UUID] = None
    ) -> int:
        """
        Store papers in the database.
        Uses upsert to handle any remaining duplicates gracefully.
        """
        stored_count = 0
        
        for paper in papers:
            source_id = self._source_ids.get(paper.source)
            if not source_id:
                continue
            
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
            
            stmt = insert(Paper).values(**paper_data)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_paper_source_external"
            )
            
            result = await self.db.execute(stmt)
            if result.rowcount > 0:
                stored_count += 1
        
        await self.db.commit()
        return stored_count
    
    async def get_papers_by_query_terms(
        self,
        terms: List[str],
        limit: int = 100,
    ) -> List[Paper]:
        """Get stored papers matching search terms."""
        result = await self.db.execute(
            select(Paper)
            .where(Paper.abstract.isnot(None))
            .order_by(Paper.citation_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
