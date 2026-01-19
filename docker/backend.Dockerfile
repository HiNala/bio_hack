# ScienceRAG Backend Dockerfile
# Multi-stage build for development and production

FROM python:3.12-slim AS base

# Metadata
LABEL maintainer="ScienceRAG Team"
LABEL description="AI-powered scientific literature intelligence platform"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONHASHSEED=random

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user early
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Development stage
FROM base AS dev

WORKDIR /app

# Install development dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create uploads directory with correct permissions
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Copy application code
COPY --chown=appuser:appuser backend/ .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]

# Production stage
FROM base AS production

WORKDIR /app

# Install production dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Create uploads directory with correct permissions
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Copy application code
COPY --chown=appuser:appuser backend/ .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start with gunicorn for production
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--log-level", "info"]
