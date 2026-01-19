-- ScienceRAG Development Database Initialization
-- Additional setup for development environment

-- Enable additional extensions for development
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create development user with additional privileges
-- Note: This is for development only, never do this in production
GRANT ALL PRIVILEGES ON DATABASE sciencerag TO sciencerag;
GRANT ALL ON SCHEMA public TO sciencerag;

-- Create some sample data for testing
INSERT INTO sources (id, name, base_url, is_active, created_at)
VALUES
    (gen_random_uuid(), 'OpenAlex', 'https://api.openalex.org', true, NOW()),
    (gen_random_uuid(), 'Semantic Scholar', 'https://api.semanticscholar.org', true, NOW())
ON CONFLICT (name) DO NOTHING;

-- Log development initialization
DO $$
BEGIN
    RAISE NOTICE 'Development database initialization completed';
    RAISE NOTICE 'Available extensions:';
    SELECT name FROM pg_available_extensions WHERE installed_version IS NOT NULL;
END
$$;