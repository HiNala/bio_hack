"""Add ingest_jobs table and paper ingest_job_id

Revision ID: 20260118_000002
Revises: 20260118_000001
Create Date: 2026-01-18 22:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260118_000002"
down_revision = "20260118_000001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ingest_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False, index=True),
        sa.Column("original_query", sa.Text(), nullable=False),
        sa.Column("parsed_queries", sa.JSON(), nullable=True),
        sa.Column("progress", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.add_column(
        "papers",
        sa.Column("ingest_job_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_papers_ingest_job_id", "papers", ["ingest_job_id"])
    op.create_foreign_key(
        "fk_papers_ingest_job",
        "papers",
        "ingest_jobs",
        ["ingest_job_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_papers_ingest_job", "papers", type_="foreignkey")
    op.drop_index("ix_papers_ingest_job_id", table_name="papers")
    op.drop_column("papers", "ingest_job_id")
    op.drop_table("ingest_jobs")
