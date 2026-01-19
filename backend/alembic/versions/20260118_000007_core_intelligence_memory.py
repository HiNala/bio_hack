"""Add core intelligence research memory tables

Revision ID: 20260118_000007
Revises: 20260118_000006
Create Date: 2026-01-18 23:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260118_000007'
down_revision: Union[str, None] = '20260118_000006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create research_sessions table
    op.create_table(
        'research_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('primary_topic', sa.Text(), nullable=True),
        sa.Column('related_topics', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=True),
        sa.Column('key_claims', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('key_papers', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('consensus_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create session_queries table
    op.create_table(
        'session_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(50), nullable=True),
        sa.Column('synthesis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('claims_discovered', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('papers_used', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('prior_context_used', sa.Text(), nullable=True),
        sa.Column('context_relevance_score', sa.Float(), nullable=True),
        sa.Column('user_marked_useful', sa.Boolean(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['synthesis_id'], ['synthesis_results.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_session_queries_session', 'session_queries', ['session_id'])

    # Create research_insights table
    op.create_table(
        'research_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('supporting_claims', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('supporting_papers', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('user_confirmed', sa.Boolean(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create memory_summaries table
    op.create_table(
        'memory_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('summary_embedding', postgresql.VECTOR(1536), nullable=True),
        sa.Column('query_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('time_range_start', sa.DateTime(), nullable=True),
        sa.Column('time_range_end', sa.DateTime(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('compression_ratio', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_memory_summaries_embedding', 'memory_summaries', ['summary_embedding'], postgresql_using='hnsw', postgresql_ops={'summary_embedding': 'vector_cosine_ops'})


def downgrade() -> None:
    op.drop_index('idx_memory_summaries_embedding', table_name='memory_summaries')
    op.drop_table('memory_summaries')
    op.drop_table('research_insights')
    op.drop_index('idx_session_queries_session', table_name='session_queries')
    op.drop_table('session_queries')
    op.drop_table('research_sessions')