"""
Security middleware and utilities.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel, validator
import re
from typing import Optional


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


class SecurityConfig:
    """Security configuration constants."""

    # Rate limits
    DEFAULT_RATE_LIMIT = "100/minute"
    API_RATE_LIMIT = "50/minute"
    SEARCH_RATE_LIMIT = "20/minute"

    # Input validation
    MAX_QUERY_LENGTH = 1000
    MAX_TITLE_LENGTH = 500
    MAX_ABSTRACT_LENGTH = 5000

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r';\s*(drop|delete|update|insert|alter|create|truncate)\s',
        r'union\s+select',
        r'--',
        r'/\*.*\*/',
        r'xp_cmdshell',
        r'exec\s*\(',
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
    ]


class InputValidation:
    """Input validation utilities."""

    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize user query input."""
        if not query or not isinstance(query, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query must be a non-empty string"
            )

        query = query.strip()

        if len(query) > SecurityConfig.MAX_QUERY_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query too long (max {SecurityConfig.MAX_QUERY_LENGTH} characters)"
            )

        if len(query) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query too short (minimum 3 characters)"
            )

        # Check for SQL injection patterns
        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid query content"
                )

        # Check for XSS patterns
        for pattern in SecurityConfig.XSS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid query content"
                )

        return query

    @staticmethod
    def validate_uuid(uuid_str: str, field_name: str = "id") -> str:
        """Validate UUID format."""
        import uuid
        try:
            uuid.UUID(uuid_str)
            return uuid_str
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format"
            )

    @staticmethod
    def validate_pagination_params(page: int, page_size: int) -> tuple[int, int]:
        """Validate pagination parameters."""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )

        return page, page_size


def setup_security_middleware(app):
    """Setup security middleware for FastAPI app."""

    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    return app


# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "RateLimitExceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after
        },
        headers={"Retry-After": str(exc.retry_after)}
    )