"""Add performance indexes

Revision ID: 20260118_000005
Revises: 20260118_000004
Create Date: 2026-01-18 00:00:05.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260118_000005'
down_revision: Union[str, None] = '20260118_000004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for better query performance

    # Papers table indexes
    op.create_index('idx_papers_source_id', 'papers', ['source_id'])
    op.create_index('idx_papers_year', 'papers', ['year'])
    op.create_index('idx_papers_citation_count', 'papers', ['citation_count'])
    op.create_index('idx_papers_created_at', 'papers', ['created_at'])
    op.create_index('idx_papers_is_chunked', 'papers', ['is_chunked'])
    op.create_index('idx_papers_is_embedded', 'papers', ['is_embedded'])

    # Composite indexes for common queries
    op.create_index('idx_papers_year_citations', 'papers', ['year', 'citation_count'])
    op.create_index('idx_papers_chunked_embedded', 'papers', ['is_chunked', 'is_embedded'])

    # Chunks table indexes
    op.create_index('idx_chunks_paper_id', 'chunks', ['paper_id'])
    op.create_index('idx_chunks_token_count', 'chunks', ['token_count'])
    op.create_index('idx_chunks_created_at', 'chunks', ['created_at'])

    # Search queries table indexes
    op.create_index('idx_search_queries_status', 'search_queries', ['status'])
    op.create_index('idx_search_queries_created_at', 'search_queries', ['created_at'])

    # Ingest jobs table indexes
    op.create_index('idx_ingest_jobs_status', 'ingest_jobs', ['status'])
    op.create_index('idx_ingest_jobs_created_at', 'ingest_jobs', ['created_at'])

    # Collections table indexes
    op.create_index('idx_collections_workspace_type', 'collections', ['workspace_id', 'type'])

    # Collection papers junction table indexes (already exist but ensure they're named)
    op.create_index('idx_collection_papers_collection', 'collection_papers', ['collection_id'], if_not_exists=True)
    op.create_index('idx_collection_papers_paper', 'collection_papers', ['paper_id'], if_not_exists=True)

    # Synthesis results indexes
    op.create_index('idx_synthesis_results_workspace_query', 'synthesis_results', ['workspace_id', 'query_id'])
    op.create_index('idx_synthesis_results_created_at', 'synthesis_results', ['created_at'])

    # Saved queries indexes
    op.create_index('idx_saved_queries_workspace_name', 'saved_queries', ['workspace_id', 'name'])

    # User settings indexes (ensure unique constraint is properly indexed)
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'], unique=True, if_not_exists=True)

    # Add partial indexes for better performance on filtered queries
    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_recent ON papers (created_at) WHERE created_at > NOW() - INTERVAL \'30 days\'')
    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_with_abstract ON papers (id) WHERE abstract IS NOT NULL')
    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_with_embeddings ON chunks (id) WHERE embedding IS NOT NULL')


def downgrade() -> None:
    # Remove indexes in reverse order

    # Partial indexes
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_chunks_with_embeddings')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_papers_with_abstract')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_papers_recent')

    # User settings
    op.drop_index('idx_user_settings_user_id', table_name='user_settings')

    # Saved queries
    op.drop_index('idx_saved_queries_workspace_name', table_name='saved_queries')

    # Synthesis results
    op.drop_index('idx_synthesis_results_created_at', table_name='synthesis_results')
    op.drop_index('idx_synthesis_results_workspace_query', table_name='synthesis_results')

    # Collections
    op.drop_index('idx_collections_workspace_type', table_name='collections')

    # Ingest jobs
    op.drop_index('idx_ingest_jobs_created_at', table_name='ingest_jobs')
    op.drop_index('idx_ingest_jobs_status', table_name='ingest_jobs')

    # Search queries
    op.drop_index('idx_search_queries_created_at', table_name='search_queries')
    op.drop_index('idx_search_queries_status', table_name='search_queries')

    # Chunks
    op.drop_index('idx_chunks_created_at', table_name='chunks')
    op.drop_index('idx_chunks_token_count', table_name='chunks')
    op.drop_index('idx_chunks_paper_id', table_name='chunks')

    # Papers
    op.drop_index('idx_papers_chunked_embedded', table_name='papers')
    op.drop_index('idx_papers_year_citations', table_name='papers')
    op.drop_index('idx_papers_is_embedded', table_name='papers')
    op.drop_index('idx_papers_is_chunked', table_name='papers')
    op.drop_index('idx_papers_created_at', table_name='papers')
    op.drop_index('idx_papers_citation_count', table_name='papers')
    op.drop_index('idx_papers_year', table_name='papers')
    op.drop_index('idx_papers_source_id', table_name='papers')