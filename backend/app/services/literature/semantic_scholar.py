"""
Semantic Scholar API Client

Async client for the Semantic Scholar academic literature API with
rate limiting, retry logic, and fault tolerance.

https://api.semanticscholar.org/

Coverage: 200M+ papers with strong CS/AI coverage
Rate limit: ~100 req/5min without key, higher with key
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


class RateLimiter:
    """
    Simple rate limiter to prevent hitting API limits.
    """
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time: Optional[float] = None
    
    async def acquire(self):
        """Wait if necessary to respect rate limits."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
        
        self.last_request_time = time.time()


class CircuitBreaker:
    """Prevent cascade failures by stopping requests to failing services."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"
    
    def can_proceed(self) -> bool:
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout):
                self.state = "half-open"
                return True
            return False
        
        return True
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class SemanticScholarClient:
    """
    Async client for Semantic Scholar API with rate limiting and retry logic.
    
    Semantic Scholar is an AI-powered research tool that provides
    semantic analysis of academic papers.
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # Fields to request from the API
    PAPER_FIELDS = [
        "paperId",
        "externalIds",
        "title",
        "abstract",
        "year",
        "venue",
        "authors",
        "citationCount",
        "fieldsOfStudy",
        "s2FieldsOfStudy",
        "openAccessPdf",
        "url",
    ]
    
    def __init__(self):
        self.api_key = settings.semantic_scholar_api_key
        self.headers = {}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key
        
        # Rate limiter: conservative without API key
        requests_per_minute = 30 if not self.api_key else 100
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    
    async def search(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SearchResult:
        """
        Search for papers matching a query with rate limiting and retry.
        """
        if not self.circuit_breaker.can_proceed():
            return SearchResult(
                papers=[],
                total_results=0,
                source="semantic_scholar",
                query=query,
                error="Circuit breaker open - service temporarily unavailable"
            )
        
        await self.rate_limiter.acquire()
        
        try:
            result = await self._search_with_retry(query, year_from, year_to, limit, offset)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            return SearchResult(
                papers=[],
                total_results=0,
                source="semantic_scholar",
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
        Includes delay between queries to respect rate limits.
        """
        all_papers = []
        seen_ids = set()
        
        for i, query in enumerate(queries):
            if len(all_papers) >= max_results:
                break
            
            # Add delay between queries (beyond rate limiter)
            if i > 0:
                await asyncio.sleep(0.5)
            
            result = await self.search(
                query=query,
                year_from=year_from,
                year_to=year_to,
                limit=min(100, max_results - len(all_papers)),
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
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type(RetryableError),
    )
    async def _search_with_retry(
        self,
        query: str,
        year_from: Optional[int],
        year_to: Optional[int],
        limit: int,
        offset: int,
    ) -> SearchResult:
        """Execute search with retry logic."""
        params = {
            "query": query,
            "fields": ",".join(self.PAPER_FIELDS),
            "limit": min(limit, 100),
            "offset": offset,
        }
        
        if year_from or year_to:
            year_range = f"{year_from or ''}-{year_to or ''}"
            params["year"] = year_range
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/paper/search",
                    params=params,
                    headers=self.headers,
                )
                
                if response.status_code == 429:
                    # Rate limited - wait longer
                    await asyncio.sleep(5)
                    raise RetryableError("Rate limited")
                elif response.status_code >= 500:
                    raise RetryableError(f"Server error: {response.status_code}")
                elif response.status_code == 404:
                    return SearchResult(
                        papers=[],
                        total_results=0,
                        source="semantic_scholar",
                        query=query,
                    )
                
                response.raise_for_status()
                data = response.json()
                
            except httpx.TimeoutException:
                raise RetryableError("Request timeout")
            except httpx.NetworkError:
                raise RetryableError("Network error")
        
        papers = []
        for paper_data in data.get("data", []):
            paper = self._parse_paper(paper_data)
            if paper:
                papers.append(paper)
        
        return SearchResult(
            papers=papers,
            total_results=data.get("total", 0),
            source="semantic_scholar",
            query=query,
        )
    
    async def get_by_id(self, paper_id: str) -> Optional[UnifiedPaper]:
        """Get a specific paper by its Semantic Scholar ID."""
        await self.rate_limiter.acquire()
        
        params = {"fields": ",".join(self.PAPER_FIELDS)}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params=params,
                headers=self.headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
        
        return self._parse_paper(data)
    
    async def get_by_doi(self, doi: str) -> Optional[UnifiedPaper]:
        """Get a paper by its DOI."""
        return await self.get_by_id(f"DOI:{doi}")
    
    def _parse_paper(self, paper: dict) -> Optional[UnifiedPaper]:
        """Parse a Semantic Scholar paper object into a UnifiedPaper."""
        try:
            paper_id = paper.get("paperId")
            if not paper_id:
                return None
            
            title = paper.get("title")
            if not title:
                return None
            
            title = self._clean_text(title)
            abstract = paper.get("abstract")
            if abstract:
                abstract = self._clean_text(abstract)
            
            authors = []
            for author_data in paper.get("authors", []):
                if author_data.get("name"):
                    authors.append(Author(
                        name=author_data["name"],
                    ))
            
            year = paper.get("year")
            venue = paper.get("venue")
            
            doi = None
            external_ids = paper.get("externalIds") or {}
            doi = external_ids.get("DOI")
            if doi:
                doi = self._normalize_doi(doi)
            
            fields = []
            s2_fields = paper.get("s2FieldsOfStudy") or []
            for field in s2_fields:
                if field.get("category"):
                    fields.append(field["category"])
            
            basic_fields = paper.get("fieldsOfStudy") or []
            for field in basic_fields:
                if field and field not in fields:
                    fields.append(field)
            
            pdf_url = None
            open_access = paper.get("openAccessPdf") or {}
            if open_access.get("url"):
                pdf_url = open_access["url"]
            
            landing_url = paper.get("url")
            
            return UnifiedPaper(
                source="semantic_scholar",
                external_id=paper_id,
                doi=doi,
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                venue=venue,
                topics=[],
                fields_of_study=fields,
                citation_count=paper.get("citationCount", 0),
                pdf_url=pdf_url,
                landing_url=landing_url,
            )
            
        except Exception as e:
            print(f"Error parsing Semantic Scholar paper: {e}")
            return None
    
    def _normalize_doi(self, doi: str) -> Optional[str]:
        """Normalize DOI to standard format."""
        if not doi:
            return None
        
        doi = doi.lower().strip()
        
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
        
        if doi.startswith("10."):
            return doi
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        text = " ".join(text.split())
        text = "".join(c for c in text if c.isprintable() or c in "\n\t")
        
        return text.strip()
