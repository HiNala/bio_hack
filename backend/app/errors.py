"""
Centralized Error Handling

Provides consistent error responses and logging across the API.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ScienceRAGException(Exception):
    """Base exception for ScienceRAG-specific errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "error"
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.log_level = log_level
        super().__init__(message)


class ValidationError(ScienceRAGException):
    """Validation error for user input."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else None
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details, "warning")


class NotFoundError(ScienceRAGException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        details = {"resource": resource, "identifier": identifier}
        super().__init__(message, status.HTTP_404_NOT_FOUND, details, "info")


class ConfigurationError(ScienceRAGException):
    """Configuration or service unavailable error."""

    def __init__(self, service: str, message: str = "not configured"):
        details = {"service": service}
        super().__init__(
            f"{service} {message}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            details,
            "warning"
        )


class DatabaseError(ScienceRAGException):
    """Database operation error."""

    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Database operation failed: {operation}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            details,
            "error"
        )


class ExternalAPIError(ScienceRAGException):
    """External API error."""

    def __init__(self, service: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(
            f"External service error: {service}",
            status_code,
            {"service": service},
            "warning"
        )


class RateLimitError(ScienceRAGException):
    """Rate limit exceeded error."""

    def __init__(self, service: str, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded for {service}",
            status.HTTP_429_TOO_MANY_REQUESTS,
            {"service": service, "retry_after": retry_after},
            "warning"
        )


class AuthenticationError(ScienceRAGException):
    """Authentication/authorization error."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, {}, "warning")


class PermissionError(ScienceRAGException):
    """Permission denied error."""

    def __init__(self, resource: str, action: str):
        super().__init__(
            f"Permission denied: cannot {action} {resource}",
            status.HTTP_403_FORBIDDEN,
            {"resource": resource, "action": action},
            "warning"
        )


def handle_exception(exc: Exception) -> HTTPException:
    """
    Convert exceptions to appropriate HTTP exceptions.

    Handles ScienceRAG-specific exceptions and provides fallbacks for others.
    """
    if isinstance(exc, ScienceRAGException):
        # Log the error appropriately
        log_method = getattr(logger, exc.log_level, logger.error)
        log_method(f"{exc.__class__.__name__}: {exc.message}", extra=exc.details)

        return HTTPException(
            status_code=exc.status_code,
            detail=ErrorResponse(
                error=exc.__class__.__name__,
                message=exc.message,
                details=exc.details
            ).model_dump()
        )

    # Handle common FastAPI/Pydantic exceptions
    elif isinstance(exc, HTTPException):
        return exc

    # Handle SQLAlchemy exceptions
    elif "sqlalchemy" in str(type(exc)).lower():
        logger.error(f"Database error: {str(exc)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="DatabaseError",
                message="A database error occurred",
                details={"type": type(exc).__name__}
            ).model_dump()
        )

    # Handle other exceptions
    else:
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred",
                details={"type": type(exc).__name__}
            ).model_dump()
        )


# Convenience functions for common error scenarios
def invalid_uuid_error(field: str = "id") -> HTTPException:
    """Return standardized error for invalid UUID."""
    return ValidationError(f"Invalid {field} format", field)


def resource_not_found(resource: str, identifier: Optional[str] = None) -> HTTPException:
    """Return standardized error for resource not found."""
    return NotFoundError(resource, identifier)


def service_unavailable(service: str) -> HTTPException:
    """Return standardized error for service unavailability."""
    return ConfigurationError(service)


def database_operation_failed(operation: str) -> HTTPException:
    """Return standardized error for database operations."""
    return DatabaseError(operation)


def external_api_failed(service: str, status_code: int = 502) -> HTTPException:
    """Return standardized error for external API failures."""
    return ExternalAPIError(service, status_code)