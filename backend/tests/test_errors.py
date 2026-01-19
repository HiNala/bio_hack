"""
Tests for error handling system.
"""

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.errors import (
    ValidationError,
    NotFoundError,
    ConfigurationError,
    handle_exception
)


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling functionality."""

    def test_validation_error(self):
        """Test validation error creation."""
        error = ValidationError("Invalid input", "field_name")

        assert error.message == "Invalid input"
        assert error.status_code == 400
        assert error.details["field"] == "field_name"

    def test_not_found_error(self):
        """Test not found error creation."""
        error = NotFoundError("User", "123")

        assert error.message == "User not found: 123"
        assert error.status_code == 404
        assert error.details["resource"] == "User"
        assert error.details["identifier"] == "123"

    def test_configuration_error(self):
        """Test configuration error creation."""
        error = ConfigurationError("OpenAI API", "key not set")

        assert error.message == "OpenAI API key not set"
        assert error.status_code == 503

    def test_handle_exception_with_custom_error(self):
        """Test handling custom ScienceRAG exceptions."""
        error = ValidationError("Test error", "test_field")
        http_exception = handle_exception(error)

        assert http_exception.status_code == 400
        response_data = http_exception.detail
        assert response_data["error"] == "ValidationError"
        assert response_data["message"] == "Test error"
        assert response_data["details"]["field"] == "test_field"

    def test_handle_exception_with_http_exception(self):
        """Test handling FastAPI HTTPException."""
        http_exc = HTTPException(status_code=404, detail="Not found")
        result = handle_exception(http_exc)

        assert result is http_exc

    def test_handle_exception_with_generic_error(self):
        """Test handling generic exceptions."""
        error = ValueError("Something went wrong")
        http_exception = handle_exception(error)

        assert http_exception.status_code == 500
        response_data = http_exception.detail
        assert response_data["error"] == "InternalServerError"
        assert "Something went wrong" in response_data["message"]