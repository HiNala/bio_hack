"""
Database Optimization Utilities

Tools for monitoring and optimizing database performance.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Paper, Chunk, IngestJob, SearchQuery


class DatabaseOptimizer:
    """Database performance monitoring and optimization tools."""

    @staticmethod
    async def analyze_query_performance(db: AsyncSession) -> Dict[str, Any]:
        """Analyze database query performance."""
        try:
            # Get PostgreSQL query statistics
            result = await db.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY seq_scan DESC
            """))

            table_stats = []
            for row in result:
                table_stats.append({
                    "table": row.tablename,
                    "sequential_scans": row.seq_scan,
                    "sequential_tuples_read": row.seq_tup_read,
                    "index_scans": row.idx_scan,
                    "index_tuples_fetched": row.idx_tup_fetch,
                    "inserts": row.n_tup_ins,
                    "updates": row.n_tup_upd,
                    "deletes": row.n_tup_del,
                })

            # Get index usage statistics
            index_result = await db.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
            """))

            index_stats = []
            for row in index_result:
                index_stats.append({
                    "table": row.tablename,
                    "index": row.indexname,
                    "scans": row.idx_scan,
                    "tuples_read": row.idx_tup_read,
                    "tuples_fetched": row.idx_tup_fetch,
                })

            return {
                "table_statistics": table_stats,
                "index_statistics": index_stats,
            }

        except Exception as e:
            return {"error": f"Failed to analyze query performance: {str(e)}"}

    @staticmethod
    async def optimize_paper_queries(db: AsyncSession, batch_size: int = 1000) -> Dict[str, Any]:
        """Optimize common paper-related queries."""
        start_time = time.time()

        # Analyze current query patterns
        paper_count = await db.scalar(select(func.count(Paper.id)))

        # Check for papers without chunks
        unchunked_result = await db.execute(
            select(func.count(Paper.id)).where(Paper.is_chunked == False)
        )
        unchunked_count = unchunked_result.scalar_one()

        # Check for chunks without embeddings
        unembedded_result = await db.execute(
            select(func.count(Chunk.id)).where(Chunk.embedding.is_(None))
        )
        unembedded_count = unembedded_result.scalar_one()

        # Get average chunk and embedding counts
        avg_chunks_result = await db.execute(text("""
            SELECT AVG(chunk_count) as avg_chunks
            FROM (
                SELECT COUNT(*) as chunk_count
                FROM chunks
                GROUP BY paper_id
            ) as chunk_counts
        """))
        avg_chunks = avg_chunks_result.scalar_one() or 0

        optimization_time = time.time() - start_time

        return {
            "total_papers": paper_count,
            "unchunked_papers": unchunked_count,
            "unembedded_chunks": unembedded_count,
            "average_chunks_per_paper": float(avg_chunks),
            "analysis_time_seconds": optimization_time,
            "recommendations": [
                "Consider chunking remaining papers" if unchunked_count > 0 else "All papers are chunked",
                "Consider generating embeddings for remaining chunks" if unembedded_count > 0 else "All chunks have embeddings",
                f"Average of {avg_chunks:.1f} chunks per paper - consider adjusting chunk size if too high/low",
            ]
        }

    @staticmethod
    async def cleanup_old_data(db: AsyncSession, days_old: int = 90) -> Dict[str, Any]:
        """Clean up old temporary data."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Count old search queries that could be archived
        old_queries_result = await db.execute(
            select(func.count(SearchQuery.id)).where(SearchQuery.created_at < cutoff_date)
        )
        old_queries_count = old_queries_result.scalar_one()

        # Count completed old jobs
        old_jobs_result = await db.execute(
            select(func.count(IngestJob.id))
            .where(IngestJob.created_at < cutoff_date)
            .where(IngestJob.status.in_(['completed', 'failed']))
        )
        old_jobs_count = old_jobs_result.scalar_one()

        return {
            "old_search_queries": old_queries_count,
            "old_ingest_jobs": old_jobs_count,
            "cutoff_date": cutoff_date.isoformat(),
            "cleanup_recommendations": [
                f"Archive {old_queries_count} search queries older than {days_old} days" if old_queries_count > 0 else "No old search queries to clean up",
                f"Archive {old_jobs_count} completed ingest jobs older than {days_old} days" if old_jobs_count > 0 else "No old ingest jobs to clean up",
            ]
        }

    @staticmethod
    async def get_database_health(db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive database health metrics."""
        try:
            # Database size
            size_result = await db.execute(text("""
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    pg_database_size(current_database()) as db_size_bytes
            """))
            size_row = size_result.first()

            # Connection count
            conn_result = await db.execute(text("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """))
            conn_count = conn_result.scalar_one()

            # Table sizes
            table_size_result = await db.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """))

            table_sizes = []
            for row in table_size_result:
                table_sizes.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "size": row.size,
                })

            # Cache hit ratio (if available)
            cache_result = await db.execute(text("""
                SELECT
                    sum(blks_hit) * 100 / (sum(blks_hit) + sum(blks_read)) as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
            """))
            cache_hit_ratio = cache_result.scalar_one()

            return {
                "database_size": size_row.db_size if size_row else "Unknown",
                "database_size_bytes": size_row.db_size_bytes if size_row else 0,
                "active_connections": conn_count or 0,
                "cache_hit_ratio": float(cache_hit_ratio) if cache_hit_ratio else None,
                "largest_tables": table_sizes,
                "health_status": "healthy" if conn_count and conn_count < 50 else "warning",
            }

        except Exception as e:
            return {
                "error": f"Failed to get database health: {str(e)}",
                "health_status": "error",
            }