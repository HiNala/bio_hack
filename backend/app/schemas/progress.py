"""
Progress Schemas

Models for ingestion progress tracking.
"""

from typing import Optional
from pydantic import BaseModel


class StageProgress(BaseModel):
    status: str  # pending | in_progress | completed | failed
    duration_ms: Optional[int] = None
    detail: Optional[str] = None


class PaperProgress(BaseModel):
    openalex_found: int = 0
    semantic_scholar_found: int = 0
    duplicates_removed: int = 0
    unique_papers: int = 0
    papers_stored: int = 0


class ChunkProgress(BaseModel):
    total_created: int = 0
    average_per_paper: float = 0.0


class EmbeddingProgress(BaseModel):
    completed: int = 0
    total: int = 0
    percent: float = 0.0


class JobProgress(BaseModel):
    current_stage: str
    stages: dict[str, StageProgress]
    papers: PaperProgress
    chunks: ChunkProgress
    embeddings: EmbeddingProgress
