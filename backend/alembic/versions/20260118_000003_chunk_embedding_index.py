"""Add HNSW index on chunk embeddings

Revision ID: 20260118_000003
Revises: 20260118_000002
Create Date: 2026-01-18 22:35:00.000000
"""

from alembic import op

revision = "20260118_000003"
down_revision = "20260118_000002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw "
        "ON chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw")
