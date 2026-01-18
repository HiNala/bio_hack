"""
OpenAlex API Client

Async client for the OpenAlex academic literature API with retry logic
and fault tolerance.

https://docs.openalex.org/

Coverage: 250M+ works across all disciplines
Rate limit: ~100 req/sec (very generous)
No API key required (but email recommended for polite pool)
"""

import asyncio
import time
from typing import Optional, List

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import get_settings
from app.services.literature.models import UnifiedPaper, Author, SearchResult

settings = get_settings()


class RetryableError(Exception):
    """Errors that should trigger a retry."""
    pass


class NonRetryableError(Exception):
    """Errors that should not be retried."""
    pass


class CircuitBreaker:
    """
    Prevent cascade failures by stopping requests to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
    
    def can_proceed(self) -> bool:
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout):
                self.state = "half-open"
                return True
            return False
        
        if self.state == "half-open":
            return True
        
        return False
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class OpenAlexClient:
    """
    Async client for OpenAlex API with retry logic and circuit breaker.
    
    OpenAlex is a fully open catalog of the global research system.
    It's a replacement for Microsoft Academic Graph.
    """
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self):
        self.email = settings.openalex_email
        self.headers = {}
        if self.email:
            self.headers["User-Agent"] = f"ScienceRAG/1.0 (mailto:{self.email})"
        
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    
    async def search(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        per_page: int = 50,
        page: int = 1,
    ) -> SearchResult:
        """
        Search for papers matching a query with retry logic.
        """
        if not self.circuit_breaker.can_proceed():
            return SearchResult(
                papers=[],
                total_results=0,
                source="openalex",
                query=query,
                error="Circuit breaker open - service temporarily unavailable"
            )
        
        try:
            result = await self._search_with_retry(query, year_from, year_to, per_page, page)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            return SearchResult(
                papers=[],
                total_results=0,
                source="openalex",
                query=query,
                error=str(e)
            )
    
    async def search_multiple_queries(
        self,
        queries: List[str],
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        max_results: int = 50,
    ) -> List[UnifiedPaper]:
        """
        Search with multiple queries and aggregate results.
        Deduplicates by external_id within this source.
        """
        all_papers = []
        seen_ids = set()
        
        for query in queries:
            if len(all_papers) >= max_results:
                break
            
            result = await self.search(
                query=query,
                year_from=year_from,
                year_to=year_to,
                per_page=min(50, max_results - len(all_papers)),
            )
            
            for paper in result.papers:
                if paper.external_id not in seen_ids:
                    seen_ids.add(paper.external_id)
                    all_papers.append(paper)
                    if len(all_papers) >= max_results:
                        break
        
        return all_papers[:max_results]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RetryableError),
    )
    async def _search_with_retry(
        self,
        query: str,
        year_from: Optional[int],
        year_to: Optional[int],
        per_page: int,
        page: int,
    ) -> SearchResult:
        """Execute search with retry logic."""
        filters = ["has_abstract:true"]
        
        if year_from:
            filters.append(f"publication_year:>={year_from}")
        if year_to:
            filters.append(f"publication_year:<={year_to}")
        
        filter_str = ",".join(filters)
        
        params = {
            "search": query,
            "filter": filter_str,
            "per_page": min(per_page, 200),
            "page": page,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/works",
                    params=params,
                    headers=self.headers,
                )
                
                if response.status_code == 429:
                    raise RetryableError("Rate limited")
                elif response.status_code >= 500:
                    raise RetryableError(f"Server error: {response.status_code}")
                elif response.status_code == 404:
                    return SearchResult(
                        papers=[],
                        total_results=0,
                        source="openalex",
                        query=query,
                    )
                elif response.status_code >= 400:
                    raise NonRetryableError(f"Client error: {response.status_code}")
                
                response.raise_for_status()
                data = response.json()
                
            except httpx.TimeoutException:
                raise RetryableError("Request timeout")
            except httpx.NetworkError:
                raise RetryableError("Network error")
        
        papers = []
        for work in data.get("results", []):
            paper = self._parse_work(work)
            if paper:
                papers.append(paper)
        
        return SearchResult(
            papers=papers,
            total_results=data.get("meta", {}).get("count", 0),
            source="openalex",
            query=query,
        )
    
    async def get_by_id(self, openalex_id: str) -> Optional[UnifiedPaper]:
        """Get a specific paper by its OpenAlex ID."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/works/{openalex_id}",
                headers=self.headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
        
        return self._parse_work(data)
    
    def _parse_work(self, work: dict) -> Optional[UnifiedPaper]:
        """Parse an OpenAlex work object into a UnifiedPaper."""
        try:
            openalex_id = work.get("id", "").replace("https://openalex.org/", "")
            if not openalex_id:
                return None
            
            title = work.get("title") or work.get("display_name")
            if not title:
                return None
            
            # Clean title
            title = self._clean_text(title)
            
            abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))
            
            authors = []
            for authorship in work.get("authorships", []):
                author_data = authorship.get("author", {})
                if author_data.get("display_name"):
                    authors.append(Author(
                        name=author_data["display_name"],
                        orcid=author_data.get("orcid"),
                        affiliation=self._get_first_affiliation(authorship),
                    ))
            
            year = work.get("publication_year")
            
            venue = None
            primary_location = work.get("primary_location") or {}
            source = primary_location.get("source") or {}
            venue = source.get("display_name")
            
            doi = work.get("doi")
            if doi:
                doi = self._normalize_doi(doi)
            
            topics = []
            for concept in work.get("concepts", [])[:10]:
                if concept.get("display_name") and concept.get("score", 0) > 0.3:
                    topics.append(concept["display_name"])
            
            fields = []
            for concept in work.get("concepts", []):
                if concept.get("level") == 0 and concept.get("display_name"):
                    fields.append(concept["display_name"])
            
            pdf_url = None
            landing_url = None
            
            if primary_location.get("is_oa"):
                pdf_url = primary_location.get("pdf_url")
                landing_url = primary_location.get("landing_page_url")
            
            best_oa = work.get("best_oa_location") or {}
            if not pdf_url:
                pdf_url = best_oa.get("pdf_url")
            if not landing_url:
                landing_url = best_oa.get("landing_page_url")
            
            if not landing_url and doi:
                landing_url = f"https://doi.org/{doi}"
            
            return UnifiedPaper(
                source="openalex",
                external_id=openalex_id,
                doi=doi,
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                venue=venue,
                topics=topics,
                fields_of_study=fields,
                citation_count=work.get("cited_by_count", 0),
                pdf_url=pdf_url,
                landing_url=landing_url,
            )
            
        except Exception as e:
            print(f"Error parsing OpenAlex work: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Optional[dict]) -> Optional[str]:
        """Reconstruct abstract text from OpenAlex's inverted index format."""
        if not inverted_index:
            return None
        
        try:
            position_word = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    position_word.append((pos, word))
            
            position_word.sort(key=lambda x: x[0])
            abstract = " ".join(word for _, word in position_word)
            
            return self._clean_text(abstract) if abstract.strip() else None
            
        except Exception:
            return None
    
    def _normalize_doi(self, doi: str) -> Optional[str]:
        """Normalize DOI to standard format."""
        if not doi:
            return None
        
        doi = doi.lower().strip()
        
        # Remove common prefixes
        prefixes = [
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
        ]
        for prefix in prefixes:
            if doi.startswith(prefix):
                doi = doi[len(prefix):]
        
        # Validate DOI format
        if doi.startswith("10."):
            return doi
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Normalize whitespace
        text = " ".join(text.split())
        
        # Remove control characters
        text = "".join(c for c in text if c.isprintable() or c in "\n\t")
        
        return text.strip()
    
    def _get_first_affiliation(self, authorship: dict) -> Optional[str]:
        """Get the first institution affiliation for an author."""
        institutions = authorship.get("institutions", [])
        if institutions and institutions[0].get("display_name"):
            return institutions[0]["display_name"]
        return None
