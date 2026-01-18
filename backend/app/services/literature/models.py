"""
Unified Paper Models

Normalized schema for papers from any literature source.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Author(BaseModel):
    """Author information."""
    name: str
    orcid: Optional[str] = None
    affiliation: Optional[str] = None


class UnifiedPaper(BaseModel):
    """
    Unified paper representation from any literature source.
    
    This normalizes data from OpenAlex, Semantic Scholar, etc.
    into a consistent format for storage and processing.
    """
    
    # Source identification
    source: str = Field(..., description="Source name: 'openalex' or 'semantic_scholar'")
    external_id: str = Field(..., description="ID from the source API")
    
    # Standard identifiers
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    
    # Core metadata
    title: str
    abstract: Optional[str] = None
    authors: list[Author] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = Field(None, description="Journal or conference name")
    
    # Classification
    topics: list[str] = Field(default_factory=list, description="Topic/concept labels")
    fields_of_study: list[str] = Field(default_factory=list, description="Academic fields")
    
    # Metrics
    citation_count: int = 0
    
    # URLs
    pdf_url: Optional[str] = None
    landing_url: Optional[str] = None
    
    # Processing metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_author_names(self) -> list[str]:
        """Get list of author names as strings."""
        return [a.name for a in self.authors]
    
    def has_abstract(self) -> bool:
        """Check if paper has a non-empty abstract."""
        return bool(self.abstract and self.abstract.strip())
    
    def to_db_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "external_id": self.external_id,
            "doi": self.doi,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.get_author_names(),
            "year": self.year,
            "venue": self.venue,
            "topics": self.topics,
            "fields_of_study": self.fields_of_study,
            "citation_count": self.citation_count,
            "pdf_url": self.pdf_url,
            "landing_url": self.landing_url,
        }


class SearchResult(BaseModel):
    """Result from a literature search."""
    papers: list[UnifiedPaper]
    total_results: int
    source: str
    query: str
    error: Optional[str] = None  # Error message if search failed
