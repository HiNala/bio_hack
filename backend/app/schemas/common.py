"""
Common Schemas

Shared response models.
"""

from pydantic import BaseModel
from typing import Any, List


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str


class ValidationError(BaseModel):
    """Validation error details."""
    field: str
    message: str
    value: Any = None


class APIErrorResponse(BaseModel):
    """Standard API error response."""
    error: str
    message: str
    details: List[ValidationError] = []
    request_id: str = None
