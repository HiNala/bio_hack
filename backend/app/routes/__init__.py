"""
API Routes

Route modules for ScienceRAG API.
"""

from app.routes.health import router as health_router
from app.routes.analyze import router as analyze_router
from app.routes.ingest import router as ingest_router
from app.routes.ingest_jobs import router as ingest_jobs_router
from app.routes.documents import router as documents_router
from app.routes.search import router as search_router
from app.routes.rag import router as rag_router
from app.routes.chunk import router as chunk_router
from app.routes.embed import router as embed_router

__all__ = [
    "health_router",
    "analyze_router",
    "ingest_router",
    "ingest_jobs_router",
    "documents_router",
    "search_router",
    "rag_router",
    "chunk_router",
    "embed_router",
]
