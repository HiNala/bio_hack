"""Initial schema with pgvector support

Revision ID: 20260118_000001
Revises: 
Create Date: 2026-01-18 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '20260118_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create papers table
    op.create_table(
        'papers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('external_id', sa.String(500), nullable=False),
        sa.Column('doi', sa.String(200), nullable=True, index=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('authors', postgresql.JSON(), default=list),
        sa.Column('year', sa.Integer(), nullable=True, index=True),
        sa.Column('venue', sa.String(500), nullable=True),
        sa.Column('topics', postgresql.JSON(), default=list),
        sa.Column('fields_of_study', postgresql.JSON(), default=list),
        sa.Column('citation_count', sa.Integer(), default=0),
        sa.Column('pdf_url', sa.String(1000), nullable=True),
        sa.Column('landing_url', sa.String(1000), nullable=True),
        sa.Column('is_chunked', sa.Boolean(), default=False),
        sa.Column('is_embedded', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('source_id', 'external_id', name='uq_paper_source_external'),
    )
    
    # Create chunks table with vector column
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('papers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(100), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('char_count', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create HNSW index for vector similarity search
    op.execute('''
        CREATE INDEX chunks_embedding_idx ON chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')
    
    # Create search_queries table
    op.create_table(
        'search_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_query', sa.Text(), nullable=False),
        sa.Column('parsed_query', postgresql.JSON(), default=dict),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('papers_found', sa.Integer(), nullable=True),
        sa.Column('papers_embedded', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    
    # Seed initial sources
    op.execute('''
        INSERT INTO sources (id, name, base_url, is_active, created_at) VALUES
        (gen_random_uuid(), 'OpenAlex', 'https://api.openalex.org', true, NOW()),
        (gen_random_uuid(), 'Semantic Scholar', 'https://api.semanticscholar.org', true, NOW())
    ''')


def downgrade() -> None:
    op.drop_table('search_queries')
    op.drop_table('chunks')
    op.drop_table('papers')
    op.drop_table('sources')
    op.execute('DROP EXTENSION IF EXISTS vector')
