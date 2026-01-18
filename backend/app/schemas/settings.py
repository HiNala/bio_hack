"""
Settings Schemas

Pydantic schemas for user settings API.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class SettingsBase(BaseModel):
    """Base settings schema with all configurable options."""
    
    # Retrieval settings
    default_sources: Optional[List[str]] = None
    papers_per_query: Optional[int] = Field(None, ge=10, le=200)
    min_citations: Optional[int] = Field(None, ge=0, le=1000)
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    
    # Synthesis settings
    synthesis_detail: Optional[str] = None  # 'brief', 'balanced', 'detailed'
    max_sources_cited: Optional[int] = Field(None, ge=5, le=25)
    include_methodology: Optional[bool] = None
    include_limitations: Optional[bool] = None
    include_consensus: Optional[bool] = None
    include_contested: Optional[bool] = None
    
    # RAG settings
    chunks_per_query: Optional[int] = Field(None, ge=5, le=50)
    similarity_threshold: Optional[float] = Field(None, ge=0.5, le=0.95)
    reranking_enabled: Optional[bool] = None
    diversify_sources: Optional[bool] = None
    
    # UI preferences
    theme: Optional[str] = None
    sidebar_collapsed: Optional[bool] = None


class SettingsUpdate(SettingsBase):
    """Schema for updating settings - all fields optional."""
    pass


class SettingsResponse(BaseModel):
    """Full settings response with all values."""
    
    # Retrieval settings
    default_sources: List[str] = ["openalex", "semantic_scholar"]
    papers_per_query: int = 50
    min_citations: int = 0
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    
    # Synthesis settings
    synthesis_detail: str = "balanced"
    max_sources_cited: int = 10
    include_methodology: bool = True
    include_limitations: bool = True
    include_consensus: bool = True
    include_contested: bool = True
    
    # RAG settings
    chunks_per_query: int = 20
    similarity_threshold: float = 0.7
    reranking_enabled: bool = True
    diversify_sources: bool = True
    
    # UI preferences
    theme: str = "light"
    sidebar_collapsed: bool = False
    
    class Config:
        from_attributes = True


# Default settings instance
DEFAULT_SETTINGS = SettingsResponse()
