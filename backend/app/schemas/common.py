"""
Common Schemas

Shared response models.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
