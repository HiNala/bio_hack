"""
Semantic Scholar API Client

Async client for the Semantic Scholar academic literature API.
https://api.semanticscholar.org/

Coverage: 200M+ papers with strong CS/AI coverage
Rate limit: ~100 req/5min without key, higher with key
"""

import httpx
from typing import Optional

from app.config import get_settings
from app.services.literature.models import UnifiedPaper, Author, SearchResult

settings = get_settings()


class SemanticScholarClient:
    """
    Async client for Semantic Scholar API.
    
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
    
    async def search(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SearchResult:
        """
        Search for papers matching a query.
        
        Args:
            query: Search query string
            year_from: Minimum publication year
            year_to: Maximum publication year
            limit: Number of results (max 100)
            offset: Offset for pagination
            
        Returns:
            SearchResult with list of UnifiedPaper objects
        """
        # Build parameters
        params = {
            "query": query,
            "fields": ",".join(self.PAPER_FIELDS),
            "limit": min(limit, 100),
            "offset": offset,
        }
        
        # Add year filter if provided
        if year_from or year_to:
            year_range = f"{year_from or ''}-{year_to or ''}"
            params["year"] = year_range
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
        
        # Parse results
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
        """
        Get a specific paper by its Semantic Scholar ID.
        
        Args:
            paper_id: Semantic Scholar paper ID
            
        Returns:
            UnifiedPaper if found, None otherwise
        """
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
        """
        Get a paper by its DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            UnifiedPaper if found, None otherwise
        """
        return await self.get_by_id(f"DOI:{doi}")
    
    def _parse_paper(self, paper: dict) -> Optional[UnifiedPaper]:
        """
        Parse a Semantic Scholar paper object into a UnifiedPaper.
        """
        try:
            # Extract ID
            paper_id = paper.get("paperId")
            if not paper_id:
                return None
            
            # Parse title
            title = paper.get("title")
            if not title:
                return None
            
            # Parse abstract
            abstract = paper.get("abstract")
            
            # Parse authors
            authors = []
            for author_data in paper.get("authors", []):
                if author_data.get("name"):
                    authors.append(Author(
                        name=author_data["name"],
                        # S2 doesn't always provide ORCID in search results
                    ))
            
            # Parse year
            year = paper.get("year")
            
            # Parse venue
            venue = paper.get("venue")
            
            # Parse DOI from external IDs
            doi = None
            external_ids = paper.get("externalIds") or {}
            doi = external_ids.get("DOI")
            
            # Parse fields of study
            fields = []
            s2_fields = paper.get("s2FieldsOfStudy") or []
            for field in s2_fields:
                if field.get("category"):
                    fields.append(field["category"])
            
            # Also include basic fieldsOfStudy
            basic_fields = paper.get("fieldsOfStudy") or []
            for field in basic_fields:
                if field and field not in fields:
                    fields.append(field)
            
            # Parse URLs
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
                topics=[],  # S2 doesn't have fine-grained topics like OpenAlex
                fields_of_study=fields,
                citation_count=paper.get("citationCount", 0),
                pdf_url=pdf_url,
                landing_url=landing_url,
            )
            
        except Exception as e:
            print(f"Error parsing Semantic Scholar paper: {e}")
            return None
