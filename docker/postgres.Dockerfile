# Use official pgvector image with PostgreSQL 16
FROM pgvector/pgvector:pg16

# Set environment variables
ENV POSTGRES_USER=sciencerag
ENV POSTGRES_PASSWORD=sciencerag
ENV POSTGRES_DB=sciencerag
ENV POSTGRES_INITDB_ARGS="--encoding=UTF-8 --lc-collate=C --lc-ctype=C"

# Copy initialization script
COPY docker/init-db.sql /docker-entrypoint-initdb.d/

# Add health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD pg_isready -U sciencerag -d sciencerag || exit 1

# Expose PostgreSQL port
EXPOSE 5432
