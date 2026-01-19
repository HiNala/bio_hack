"""Add core intelligence contradictions table

Revision ID: 20260118_000006
Revises: 20260118_000005
Create Date: 2026-01-18 23:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260118_000006'
down_revision: Union[str, None] = '20260118_000005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contradictions table
    op.create_table(
        'contradictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contradiction_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.Float(), nullable=False),
        sa.Column('evidence_a_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('evidence_b_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('resolution_suggestion', sa.Text(), nullable=True),
        sa.Column('paper_a_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('paper_b_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['evidence_a_id'], ['claim_evidence.id']),
        sa.ForeignKeyConstraint(['evidence_b_id'], ['claim_evidence.id']),
        sa.ForeignKeyConstraint(['paper_a_id'], ['papers.id']),
        sa.ForeignKeyConstraint(['paper_b_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_id', 'evidence_a_id', 'evidence_b_id', name='uq_contradiction_evidence')
    )
    op.create_index('idx_contradictions_claim', 'contradictions', ['claim_id'])
    op.create_index('idx_contradictions_severity', 'contradictions', ['severity'])


def downgrade() -> None:
    op.drop_index('idx_contradictions_severity', table_name='contradictions')
    op.drop_index('idx_contradictions_claim', table_name='contradictions')
    op.drop_table('contradictions')