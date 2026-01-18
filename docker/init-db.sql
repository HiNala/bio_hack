-- ScienceRAG Database Initialization
-- This script runs when the container is first created

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension enabled successfully';
END
$$;
