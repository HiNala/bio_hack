"""
Settings Service

Manages user settings with validation and defaults.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.settings import SettingsResponse, DEFAULT_SETTINGS


class SettingsService:
    """Manage user settings with validation."""
    
    VALID_SOURCES = ["openalex", "semantic_scholar", "pubmed", "arxiv"]
    VALID_DETAIL_LEVELS = ["brief", "balanced", "detailed"]
    VALID_THEMES = ["light", "dark", "system"]
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_user(self, user_id: Optional[str] = None) -> User:
        """Get or create a user. For hackathon, creates anonymous users."""
        if user_id:
            result = await self.db.execute(
                select(User).where(User.id == uuid.UUID(user_id))
            )
            user = result.scalar_one_or_none()
            if user:
                return user
        
        # Create anonymous user
        user = User(
            id=uuid.uuid4(),
            auth_provider="anonymous",
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user_settings(self, user_id: str) -> SettingsResponse:
        """Get user settings with defaults for missing values."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == uuid.UUID(user_id))
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # Return defaults
            return DEFAULT_SETTINGS
        
        # Convert to response with defaults for any None values
        return SettingsResponse(
            default_sources=settings.default_sources or DEFAULT_SETTINGS.default_sources,
            papers_per_query=settings.papers_per_query or DEFAULT_SETTINGS.papers_per_query,
            min_citations=settings.min_citations if settings.min_citations is not None else DEFAULT_SETTINGS.min_citations,
            year_from=settings.year_from,
            year_to=settings.year_to,
            synthesis_detail=settings.synthesis_detail or DEFAULT_SETTINGS.synthesis_detail,
            max_sources_cited=settings.max_sources_cited or DEFAULT_SETTINGS.max_sources_cited,
            include_methodology=settings.include_methodology if settings.include_methodology is not None else DEFAULT_SETTINGS.include_methodology,
            include_limitations=settings.include_limitations if settings.include_limitations is not None else DEFAULT_SETTINGS.include_limitations,
            include_consensus=settings.include_consensus if settings.include_consensus is not None else DEFAULT_SETTINGS.include_consensus,
            include_contested=settings.include_contested if settings.include_contested is not None else DEFAULT_SETTINGS.include_contested,
            chunks_per_query=settings.chunks_per_query or DEFAULT_SETTINGS.chunks_per_query,
            similarity_threshold=settings.similarity_threshold or DEFAULT_SETTINGS.similarity_threshold,
            reranking_enabled=settings.reranking_enabled if settings.reranking_enabled is not None else DEFAULT_SETTINGS.reranking_enabled,
            diversify_sources=settings.diversify_sources if settings.diversify_sources is not None else DEFAULT_SETTINGS.diversify_sources,
            theme=settings.theme or DEFAULT_SETTINGS.theme,
            sidebar_collapsed=settings.sidebar_collapsed if settings.sidebar_collapsed is not None else DEFAULT_SETTINGS.sidebar_collapsed,
        )
    
    async def update_user_settings(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> SettingsResponse:
        """Update user settings with validation."""
        # Validate updates
        validated = self._validate_settings(updates)
        
        # Get or create settings
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == uuid.UUID(user_id))
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # Create new settings
            settings = UserSettings(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
            )
            self.db.add(settings)
        
        # Apply updates
        for key, value in validated.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(settings)
        
        return await self.get_user_settings(user_id)
    
    def _validate_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate setting values are within allowed ranges."""
        validated = {}
        
        # Retrieval settings
        if "default_sources" in updates:
            sources = updates["default_sources"]
            if isinstance(sources, list):
                validated["default_sources"] = [
                    s for s in sources if s in self.VALID_SOURCES
                ] or DEFAULT_SETTINGS.default_sources
        
        if "papers_per_query" in updates:
            val = updates["papers_per_query"]
            if isinstance(val, int):
                validated["papers_per_query"] = max(10, min(200, val))
        
        if "min_citations" in updates:
            val = updates["min_citations"]
            if isinstance(val, int):
                validated["min_citations"] = max(0, min(1000, val))
        
        if "year_from" in updates:
            val = updates["year_from"]
            if val is None or (isinstance(val, int) and 1900 <= val <= 2100):
                validated["year_from"] = val
        
        if "year_to" in updates:
            val = updates["year_to"]
            if val is None or (isinstance(val, int) and 1900 <= val <= 2100):
                validated["year_to"] = val
        
        # Synthesis settings
        if "synthesis_detail" in updates:
            if updates["synthesis_detail"] in self.VALID_DETAIL_LEVELS:
                validated["synthesis_detail"] = updates["synthesis_detail"]
        
        if "max_sources_cited" in updates:
            val = updates["max_sources_cited"]
            if isinstance(val, int):
                validated["max_sources_cited"] = max(5, min(25, val))
        
        # Boolean settings
        for key in ["include_methodology", "include_limitations", 
                    "include_consensus", "include_contested",
                    "reranking_enabled", "diversify_sources", "sidebar_collapsed"]:
            if key in updates and isinstance(updates[key], bool):
                validated[key] = updates[key]
        
        # RAG settings
        if "chunks_per_query" in updates:
            val = updates["chunks_per_query"]
            if isinstance(val, int):
                validated["chunks_per_query"] = max(5, min(50, val))
        
        if "similarity_threshold" in updates:
            val = updates["similarity_threshold"]
            if isinstance(val, (int, float)):
                validated["similarity_threshold"] = max(0.5, min(0.95, float(val)))
        
        # UI settings
        if "theme" in updates:
            if updates["theme"] in self.VALID_THEMES:
                validated["theme"] = updates["theme"]
        
        return validated
    
    async def reset_to_defaults(self, user_id: str) -> SettingsResponse:
        """Reset all settings to defaults."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == uuid.UUID(user_id))
        )
        settings = result.scalar_one_or_none()
        
        if settings:
            await self.db.delete(settings)
            await self.db.commit()
        
        return DEFAULT_SETTINGS
