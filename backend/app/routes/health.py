"""
Health Check Endpoint

System health and readiness checks.
"""

from fastapi import APIRouter

from app.schemas import HealthResponse
from app.database import check_db_connection
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Check system health.
    
    Returns status of all critical services.
    """
    db_status = "connected" if await check_db_connection() else "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.app_version,
        database=db_status,
    )
