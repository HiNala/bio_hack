"""
OpenAlex API Client

Async client for the OpenAlex academic literature API.
https://docs.openalex.org/

Coverage: 250M+ works across all disciplines
Rate limit: ~100 req/sec (very generous)
No API key required (but email recommended for polite pool)
"""

import httpx
from typing import Optional
from urllib.parse import quote

from app.config import get_settings
from app.services.literature.models import UnifiedPaper, Author, SearchResult

settings = get_settings()


class OpenAlexClient:
    """
    Async client for OpenAlex API.
    
    OpenAlex is a fully open catalog of the global research system.
    It's a replacement for Microsoft Academic Graph.
    """
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self):
        self.email = settings.openalex_email
        # Add email to headers for "polite pool" (faster rate limits)
        self.headers = {}
        if self.email:
            self.headers["User-Agent"] = f"ScienceRAG/1.0 (mailto:{self.email})"
    
    async def search(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        per_page: int = 50,
        page: int = 1,
    ) -> SearchResult:
        """
        Search for papers matching a query.
        
        Args:
            query: Search query string
            year_from: Minimum publication year
            year_to: Maximum publication year
            per_page: Number of results per page (max 200)
            page: Page number (1-indexed)
            
        Returns:
            SearchResult with list of UnifiedPaper objects
        """
        # Build filters
        filters = ["has_abstract:true"]
        
        if year_from:
            filters.append(f"publication_year:>={year_from}")
        if year_to:
            filters.append(f"publication_year:<={year_to}")
        
        filter_str = ",".join(filters)
        
        # Build URL
        params = {
            "search": query,
            "filter": filter_str,
            "per_page": min(per_page, 200),
            "page": page,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/works",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
        
        # Parse results
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
        """
        Get a specific paper by its OpenAlex ID.
        
        Args:
            openalex_id: OpenAlex ID (e.g., "W2741809807")
            
        Returns:
            UnifiedPaper if found, None otherwise
        """
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
        """
        Parse an OpenAlex work object into a UnifiedPaper.
        
        OpenAlex has some quirks:
        - Abstracts are stored as "inverted index" format
        - Authors are nested in authorships
        - Concepts have scores and levels
        """
        try:
            # Extract OpenAlex ID (remove URL prefix)
            openalex_id = work.get("id", "").replace("https://openalex.org/", "")
            if not openalex_id:
                return None
            
            # Parse title
            title = work.get("title") or work.get("display_name")
            if not title:
                return None
            
            # Parse abstract from inverted index
            abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))
            
            # Parse authors
            authors = []
            for authorship in work.get("authorships", []):
                author_data = authorship.get("author", {})
                if author_data.get("display_name"):
                    authors.append(Author(
                        name=author_data["display_name"],
                        orcid=author_data.get("orcid"),
                        affiliation=self._get_first_affiliation(authorship),
                    ))
            
            # Parse year
            year = work.get("publication_year")
            
            # Parse venue
            venue = None
            primary_location = work.get("primary_location") or {}
            source = primary_location.get("source") or {}
            venue = source.get("display_name")
            
            # Parse DOI
            doi = work.get("doi")
            if doi and doi.startswith("https://doi.org/"):
                doi = doi.replace("https://doi.org/", "")
            
            # Parse topics/concepts
            topics = []
            for concept in work.get("concepts", [])[:10]:  # Limit to top 10
                if concept.get("display_name") and concept.get("score", 0) > 0.3:
                    topics.append(concept["display_name"])
            
            # Parse fields of study from topics (level 0 = broad fields)
            fields = []
            for concept in work.get("concepts", []):
                if concept.get("level") == 0 and concept.get("display_name"):
                    fields.append(concept["display_name"])
            
            # Parse URLs
            pdf_url = None
            landing_url = None
            
            # Check primary location for open access PDF
            if primary_location.get("is_oa"):
                pdf_url = primary_location.get("pdf_url")
                landing_url = primary_location.get("landing_page_url")
            
            # Fallback to best_oa_location
            best_oa = work.get("best_oa_location") or {}
            if not pdf_url:
                pdf_url = best_oa.get("pdf_url")
            if not landing_url:
                landing_url = best_oa.get("landing_page_url")
            
            # Final fallback to DOI landing page
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
            # Log error but don't fail the whole batch
            print(f"Error parsing OpenAlex work: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Optional[dict]) -> Optional[str]:
        """
        Reconstruct abstract text from OpenAlex's inverted index format.
        
        OpenAlex stores abstracts as {word: [positions]} for compression.
        We need to reconstruct the original text.
        """
        if not inverted_index:
            return None
        
        try:
            # Build list of (position, word) tuples
            position_word = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    position_word.append((pos, word))
            
            # Sort by position and join
            position_word.sort(key=lambda x: x[0])
            abstract = " ".join(word for _, word in position_word)
            
            return abstract if abstract.strip() else None
            
        except Exception:
            return None
    
    def _get_first_affiliation(self, authorship: dict) -> Optional[str]:
        """Get the first institution affiliation for an author."""
        institutions = authorship.get("institutions", [])
        if institutions and institutions[0].get("display_name"):
            return institutions[0]["display_name"]
        return None
