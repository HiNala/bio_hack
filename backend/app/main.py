"""
ScienceRAG Backend Application

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.errors import handle_exception
from app.logging import setup_logging
from app.security import setup_security_middleware
from app.middleware.security import SecurityHeadersMiddleware
import logging

logger = logging.getLogger(__name__)

from app.routes import (
    health_router,
    analyze_router,
    ingest_router,
    ingest_jobs_router,
    documents_router,
    search_router,
    rag_router,
    chunk_router,
    embed_router,
    settings_router,
    workspaces_router,
    synthesis_router,
    claims_router,
    contradictions_router,
    memory_router,
    metrics_router,
    export_router,
    uploads_router,
)
from app.routes.activity import router as activity_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    await init_db()

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered scientific literature intelligence platform",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup security middleware
app = setup_security_middleware(app)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    import time
    start_time = time.time()

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.url.query),
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": request.client.host if request.client else None,
        }
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response
    logger.info(
        f"Response: {response.status_code} in {process_time:.3f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time,
            "path": request.url.path,
        }
    )

    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions with standardized responses."""
    return JSONResponse(
        status_code=handle_exception(exc).status_code,
        content=handle_exception(exc).detail
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(ingest_router)
app.include_router(ingest_jobs_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(rag_router)
app.include_router(chunk_router)
app.include_router(embed_router)
app.include_router(settings_router)
app.include_router(workspaces_router)
app.include_router(synthesis_router)
app.include_router(claims_router)
app.include_router(contradictions_router)
app.include_router(memory_router)
app.include_router(metrics_router)
app.include_router(export_router)
app.include_router(uploads_router)
app.include_router(activity_router)


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "features": {
            "synthesis": "/synthesis",
            "workspaces": "/workspaces",
            "settings": "/settings",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
