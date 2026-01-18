"""
Literature Services

API clients and orchestration for academic literature sources.
"""

from app.services.literature.models import UnifiedPaper, Author
from app.services.literature.openalex import OpenAlexClient
from app.services.literature.semantic_scholar import SemanticScholarClient
from app.services.literature.service import LiteratureService

__all__ = [
    "UnifiedPaper",
    "Author",
    "OpenAlexClient",
    "SemanticScholarClient",
    "LiteratureService",
]
