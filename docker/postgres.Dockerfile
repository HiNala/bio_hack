# Use official pgvector image with PostgreSQL 16
FROM pgvector/pgvector:pg16

# Set environment variables
ENV POSTGRES_USER=sciencerag
ENV POSTGRES_PASSWORD=sciencerag
ENV POSTGRES_DB=sciencerag

# Copy initialization script
COPY docker/init-db.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432
