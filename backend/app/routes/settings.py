"""
Settings API Routes

Endpoints for managing user settings.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.settings import SettingsUpdate, SettingsResponse
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> Optional[str]:
    """Get user ID from header (simple auth for hackathon)."""
    return x_user_id


@router.get("", response_model=SettingsResponse)
async def get_settings(
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user settings.
    
    Returns default settings if user has no saved settings.
    """
    service = SettingsService(db)
    
    if not user_id:
        # Create anonymous user and return defaults
        user = await service.get_or_create_user()
        return await service.get_user_settings(str(user.id))
    
    return await service.get_user_settings(user_id)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    updates: SettingsUpdate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user settings.
    
    Only provided fields will be updated. Invalid values will be
    coerced to valid ranges.
    """
    service = SettingsService(db)
    
    if not user_id:
        # Create anonymous user
        user = await service.get_or_create_user()
        user_id = str(user.id)
    
    # Convert to dict, excluding None values
    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    return await service.update_user_settings(user_id, update_dict)


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings(
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset all settings to defaults.
    """
    service = SettingsService(db)
    
    if not user_id:
        # Create anonymous user
        user = await service.get_or_create_user()
        user_id = str(user.id)
    
    return await service.reset_to_defaults(user_id)


@router.get("/defaults", response_model=SettingsResponse)
async def get_defaults():
    """
    Get default settings values.
    """
    from app.schemas.settings import DEFAULT_SETTINGS
    return DEFAULT_SETTINGS
