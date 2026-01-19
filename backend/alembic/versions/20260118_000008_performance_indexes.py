"""Add performance indexes for core intelligence features

Revision ID: 20260118_000008
Revises: 20260118_000007
Create Date: 2026-01-18 23:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260118_000008'
down_revision: Union[str, None] = '20260118_000007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additional indexes for performance

    # Claims table - composite indexes for common queries
    op.create_index('idx_claims_created_recent', 'claims', ['created_at'], postgresql_where=sa.text("created_at > NOW() - INTERVAL '30 days'"))
    op.create_index('idx_claims_consensus_score', 'claims', ['consensus_score'])
    op.create_index('idx_claims_evidence_strength', 'claims', ['evidence_strength'])

    # Claim evidence - performance indexes
    op.create_index('idx_evidence_confidence', 'claim_evidence', ['confidence'])
    op.create_index('idx_evidence_created_recent', 'claim_evidence', ['extracted_at'], postgresql_where=sa.text("extracted_at > NOW() - INTERVAL '30 days'"))

    # Contradictions - additional indexes
    op.create_index('idx_contradictions_created_recent', 'contradictions', ['detected_at'], postgresql_where=sa.text("detected_at > NOW() - INTERVAL '30 days'"))

    # Research sessions - performance indexes
    op.create_index('idx_sessions_workspace_active', 'research_sessions', ['workspace_id', 'status'], postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_sessions_last_activity', 'research_sessions', ['last_activity_at'])

    # Session queries - performance indexes
    op.create_index('idx_session_queries_created', 'session_queries', ['created_at'])
    op.create_index('idx_session_queries_type', 'session_queries', ['query_type'])

    # Memory summaries - embedding search performance
    op.create_index('idx_memory_summaries_created', 'memory_summaries', ['created_at'])

    # Composite indexes for common joins
    op.create_index('idx_claims_evidence_claim_paper', 'claim_evidence', ['claim_id', 'paper_id'])
    op.create_index('idx_contradictions_claim_paper', 'contradictions', ['claim_id', 'paper_a_id', 'paper_b_id'])


def downgrade() -> None:
    # Drop all added indexes
    op.drop_index('idx_claims_created_recent', table_name='claims')
    op.drop_index('idx_claims_consensus_score', table_name='claims')
    op.drop_index('idx_claims_evidence_strength', table_name='claims')
    op.drop_index('idx_evidence_confidence', table_name='claim_evidence')
    op.drop_index('idx_evidence_created_recent', table_name='claim_evidence')
    op.drop_index('idx_contradictions_created_recent', table_name='contradictions')
    op.drop_index('idx_sessions_workspace_active', table_name='research_sessions')
    op.drop_index('idx_sessions_last_activity', table_name='research_sessions')
    op.drop_index('idx_session_queries_created', table_name='session_queries')
    op.drop_index('idx_session_queries_type', table_name='session_queries')
    op.drop_index('idx_memory_summaries_created', table_name='memory_summaries')
    op.drop_index('idx_claims_evidence_claim_paper', table_name='claim_evidence')
    op.drop_index('idx_contradictions_claim_paper', table_name='contradictions')