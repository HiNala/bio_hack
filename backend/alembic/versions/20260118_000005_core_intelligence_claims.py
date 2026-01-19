"""Add core intelligence claims tables

Revision ID: 20260118_000005
Revises: 20260118_000004
Create Date: 2026-01-18 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260118_000005'
down_revision: Union[str, None] = '20260118_000004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create claims table
    op.create_table(
        'claims',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('canonical_text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=False),
        sa.Column('claim_type', sa.String(50), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('predicate', sa.Text(), nullable=True),
        sa.Column('object', sa.Text(), nullable=True),
        sa.Column('has_quantitative_data', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('effect_direction', sa.String(20), nullable=True),
        sa.Column('effect_magnitude', sa.Text(), nullable=True),
        sa.Column('domain_tags', postgresql.ARRAY(sa.String()), server_default='{}', nullable=True),
        sa.Column('embedding', postgresql.VECTOR(1536), nullable=True),
        sa.Column('supporting_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('opposing_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('conditional_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_evidence_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('consensus_score', sa.Float(), nullable=True),
        sa.Column('evidence_strength', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_claims_embedding', 'claims', ['embedding'], postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_index('idx_claims_domain', 'claims', ['domain_tags'], postgresql_using='gin')
    op.create_index('idx_claims_type', 'claims', ['claim_type'])

    # Create claim_evidence table
    op.create_table(
        'claim_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stance', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('relevant_quote', sa.Text(), nullable=True),
        sa.Column('conditions', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=True),
        sa.Column('limitations', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=True),
        sa.Column('methodology_type', sa.String(50), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('is_primary_source', sa.Boolean(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('extraction_model', sa.String(100), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_id', 'chunk_id', name='uq_claim_chunk')
    )
    op.create_index('idx_evidence_claim', 'claim_evidence', ['claim_id'])
    op.create_index('idx_evidence_paper', 'claim_evidence', ['paper_id'])
    op.create_index('idx_evidence_stance', 'claim_evidence', ['stance'])

    # Create claim_clusters table
    op.create_table(
        'claim_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('canonical_claim_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('claim_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['canonical_claim_id'], ['claims.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create claim_cluster_members table
    op.create_table(
        'claim_cluster_members',
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['claim_clusters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('cluster_id', 'claim_id')
    )


def downgrade() -> None:
    op.drop_table('claim_cluster_members')
    op.drop_table('claim_clusters')
    op.drop_index('idx_evidence_stance', table_name='claim_evidence')
    op.drop_index('idx_evidence_paper', table_name='claim_evidence')
    op.drop_index('idx_evidence_claim', table_name='claim_evidence')
    op.drop_table('claim_evidence')
    op.drop_index('idx_claims_type', table_name='claims')
    op.drop_index('idx_claims_domain', table_name='claims')
    op.drop_index('idx_claims_embedding', table_name='claims')
    op.drop_table('claims')