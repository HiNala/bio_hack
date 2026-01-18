"""Add user, workspace, collection, settings, and synthesis tables

Revision ID: 20260118_000004
Revises: 20260118_000003
Create Date: 2026-01-18 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260118_000004'
down_revision: Union[str, None] = '20260118_000003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('auth_provider', sa.String(50), server_default='anonymous', nullable=True),
        sa.Column('auth_id', sa.String(255), nullable=True),
        sa.Column('institution', sa.String(255), nullable=True),
        sa.Column('role', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_active_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Create workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('settings', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workspaces_user', 'workspaces', ['user_id'])
    
    # Create collections table
    op.create_table(
        'collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('type', sa.String(50), server_default='manual', nullable=True),
        sa.Column('smart_rules', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collections_workspace', 'collections', ['workspace_id'])
    
    # Create collection_papers junction table
    op.create_table(
        'collection_papers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('user_tags', postgresql.ARRAY(sa.String()), server_default='{}', nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('read_status', sa.String(20), server_default='unread', nullable=True),
        sa.Column('added_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('added_by', sa.String(50), server_default='user', nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)', name='check_rating_range'),
        sa.UniqueConstraint('collection_id', 'paper_id', name='uq_collection_paper')
    )
    op.create_index('idx_collection_papers_collection', 'collection_papers', ['collection_id'])
    op.create_index('idx_collection_papers_paper', 'collection_papers', ['paper_id'])
    
    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('default_sources', postgresql.ARRAY(sa.String()), server_default='{openalex,semantic_scholar}', nullable=True),
        sa.Column('papers_per_query', sa.Integer(), server_default='50', nullable=True),
        sa.Column('min_citations', sa.Integer(), server_default='0', nullable=True),
        sa.Column('year_from', sa.Integer(), nullable=True),
        sa.Column('year_to', sa.Integer(), nullable=True),
        sa.Column('synthesis_detail', sa.String(20), server_default='balanced', nullable=True),
        sa.Column('max_sources_cited', sa.Integer(), server_default='10', nullable=True),
        sa.Column('include_methodology', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('include_limitations', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('include_consensus', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('include_contested', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('chunks_per_query', sa.Integer(), server_default='20', nullable=True),
        sa.Column('similarity_threshold', sa.Float(), server_default='0.7', nullable=True),
        sa.Column('reranking_enabled', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('diversify_sources', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('theme', sa.String(20), server_default='light', nullable=True),
        sa.Column('sidebar_collapsed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.CheckConstraint('papers_per_query >= 10 AND papers_per_query <= 200', name='check_papers_per_query'),
        sa.CheckConstraint('chunks_per_query >= 5 AND chunks_per_query <= 50', name='check_chunks_per_query'),
        sa.CheckConstraint('similarity_threshold >= 0.5 AND similarity_threshold <= 0.95', name='check_similarity_threshold'),
    )
    
    # Create saved_queries table
    op.create_table(
        'saved_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('raw_query', sa.Text(), nullable=False),
        sa.Column('parsed_query', postgresql.JSONB(), nullable=True),
        sa.Column('settings_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('papers_found', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_saved_queries_workspace', 'saved_queries', ['workspace_id'])
    
    # Create synthesis_results table
    op.create_table(
        'synthesis_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mode', sa.String(50), nullable=False),
        sa.Column('input_query', sa.Text(), nullable=False),
        sa.Column('source_papers', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('source_chunks', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('content', postgresql.JSONB(), nullable=False),
        sa.Column('sources_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['query_id'], ['saved_queries.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_synthesis_workspace', 'synthesis_results', ['workspace_id'])
    op.create_index('idx_synthesis_mode', 'synthesis_results', ['mode'])


def downgrade() -> None:
    op.drop_index('idx_synthesis_mode', table_name='synthesis_results')
    op.drop_index('idx_synthesis_workspace', table_name='synthesis_results')
    op.drop_table('synthesis_results')
    
    op.drop_index('idx_saved_queries_workspace', table_name='saved_queries')
    op.drop_table('saved_queries')
    
    op.drop_table('user_settings')
    
    op.drop_index('idx_collection_papers_paper', table_name='collection_papers')
    op.drop_index('idx_collection_papers_collection', table_name='collection_papers')
    op.drop_table('collection_papers')
    
    op.drop_index('idx_collections_workspace', table_name='collections')
    op.drop_table('collections')
    
    op.drop_index('idx_workspaces_user', table_name='workspaces')
    op.drop_table('workspaces')
    
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
