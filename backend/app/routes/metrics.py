"""
Metrics and Monitoring Endpoints

Provides health metrics and monitoring data for the application.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
import psutil
import asyncio
from typing import Dict, Any

from app.database import get_db
from app.models import Paper, Chunk, SearchQuery, IngestJob
from app.utils.db_optimization import DatabaseOptimizer

router = APIRouter(prefix="/metrics", tags=["Metrics"])


class MetricsCollector:
    """Collect system and application metrics."""

    @staticmethod
    async def get_database_metrics(db: AsyncSession) -> Dict[str, Any]:
        """Get database-related metrics."""
        # Paper metrics
        papers_result = await db.execute(
            select(
                func.count(Paper.id).label('total_papers'),
                func.sum(func.cast(Paper.is_chunked, text('INTEGER'))).label('chunked_papers'),
                func.sum(func.cast(Paper.is_embedded, text('INTEGER'))).label('embedded_papers'),
                func.avg(func.length(Paper.abstract)).label('avg_abstract_length'),
            )
        )
        papers_row = papers_result.first()

        # Chunk metrics
        chunks_result = await db.execute(
            select(
                func.count(Chunk.id).label('total_chunks'),
                func.avg(Chunk.token_count).label('avg_tokens_per_chunk'),
                func.avg(Chunk.char_count).label('avg_chars_per_chunk'),
            )
        )
        chunks_row = chunks_result.first()

        # Job metrics
        jobs_result = await db.execute(
            select(
                func.count(IngestJob.id).label('total_jobs'),
                func.avg(
                    func.extract('epoch', IngestJob.completed_at - IngestJob.created_at)
                ).label('avg_job_duration_seconds'),
            ).where(IngestJob.status == 'completed')
        )
        jobs_row = jobs_result.first()

        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_jobs_result = await db.execute(
            select(func.count(IngestJob.id)).where(IngestJob.created_at >= yesterday)
        )
        recent_jobs = recent_jobs_result.scalar_one() or 0

        return {
            "papers": {
                "total": papers_row.total_papers or 0,
                "chunked": papers_row.chunked_papers or 0,
                "embedded": papers_row.embedded_papers or 0,
                "avg_abstract_length": float(papers_row.avg_abstract_length or 0),
            },
            "chunks": {
                "total": chunks_row.total_chunks or 0,
                "avg_tokens_per_chunk": float(chunks_row.avg_tokens_per_chunk or 0),
                "avg_chars_per_chunk": float(chunks_row.avg_chars_per_chunk or 0),
            },
            "jobs": {
                "total": jobs_row.total_jobs or 0,
                "avg_duration_seconds": float(jobs_row.avg_job_duration_seconds or 0),
                "recent_24h": recent_jobs,
            }
        }

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get system-level metrics."""
        return {
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": psutil.virtual_memory().total / (1024**3),
                "available_gb": psutil.virtual_memory().available / (1024**3),
                "usage_percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total_gb": psutil.disk_usage('/').total / (1024**3),
                "free_gb": psutil.disk_usage('/').free / (1024**3),
                "usage_percent": psutil.disk_usage('/').percent,
            }
        }


@router.get("/health", tags=["Health"])
async def get_health_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get comprehensive health and metrics data.

    Returns system health, database status, and application metrics.
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))

        # Get metrics
        db_metrics = await MetricsCollector.get_database_metrics(db)
        system_metrics = MetricsCollector.get_system_metrics()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "connected",
                **db_metrics
            },
            "system": system_metrics,
            "uptime": psutil.boot_time(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "disconnected",
                "error": str(e)
            },
            "system": MetricsCollector.get_system_metrics(),
            "error": str(e),
        }


@router.get("/database", tags=["Metrics"])
async def get_database_metrics(db: AsyncSession = Depends(get_db)):
    """Get detailed database metrics."""
    return await MetricsCollector.get_database_metrics(db)


@router.get("/system", tags=["Metrics"])
async def get_system_metrics():
    """Get system-level metrics."""
    return MetricsCollector.get_system_metrics()


@router.get("/database/health", tags=["Metrics"])
async def get_database_health(db: AsyncSession = Depends(get_db)):
    """Get database health metrics."""
    return await DatabaseOptimizer.get_database_health(db)


@router.get("/database/optimization", tags=["Metrics"])
async def get_database_optimization_info(db: AsyncSession = Depends(get_db)):
    """Get database optimization recommendations."""
    return await DatabaseOptimizer.optimize_paper_queries(db)


@router.get("/database/cleanup", tags=["Metrics"])
async def get_cleanup_info(db: AsyncSession = Depends(get_db), days: int = 90):
    """Get information about data that could be cleaned up."""
    return await DatabaseOptimizer.cleanup_old_data(db, days)


@router.get("/performance/query-analysis", tags=["Metrics"])
async def get_query_performance_analysis(db: AsyncSession = Depends(get_db)):
    """Get query performance analysis."""
    return await DatabaseOptimizer.analyze_query_performance(db)