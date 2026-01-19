"""
Data Validation and Sanitization Utilities

Comprehensive validation for all input data types.
"""

import re
import html
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import bleach

from app.errors import ValidationError


class DataValidator:
    """Comprehensive data validation and sanitization."""

    # Email validation regex
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # URL validation regex
    URL_REGEX = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    # DOI validation regex
    DOI_REGEX = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.IGNORECASE)

    # UUID validation regex
    UUID_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

    # SQL injection patterns (expanded)
    SQL_INJECTION_PATTERNS = [
        r';\s*(select|insert|update|delete|drop|create|alter|truncate|exec|union)\s',
        r'--',
        r'/\*.*\*/',
        r'xp_cmdshell',
        r'exec\s*\(',
        r'cast\s*\(',
        r'convert\s*\(',
        r'information_schema',
        r'sysobjects',
        r'systables',
    ]

    # XSS patterns (expanded)
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
        r'eval\s*\(',
        r'document\.',
        r'window\.',
    ]

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            raise ValidationError("Value must be a string", "value")

        # Remove null bytes and control characters
        value = value.replace('\x00', '').strip()

        # Check length
        if max_length and len(value) > max_length:
            raise ValidationError(f"Value too long (max {max_length} characters)", "value")

        # HTML escape if not allowing HTML
        if not allow_html:
            value = html.escape(value)
        else:
            # Use bleach to clean HTML
            value = bleach.clean(value, tags=['p', 'br', 'strong', 'em', 'u'], strip=True)

        return value

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address."""
        email = DataValidator.sanitize_string(email, 254)

        if not DataValidator.EMAIL_REGEX.match(email):
            raise ValidationError("Invalid email format", "email")

        return email.lower()

    @staticmethod
    def validate_url(url: str, allow_relative: bool = False) -> str:
        """Validate and sanitize URL."""
        url = DataValidator.sanitize_string(url, 2000)

        if allow_relative and not url.startswith(('http://', 'https://')):
            # Allow relative URLs
            return url

        if not DataValidator.URL_REGEX.match(url):
            raise ValidationError("Invalid URL format", "url")

        # Additional security check
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError("URL must use HTTP or HTTPS", "url")

        return url

    @staticmethod
    def validate_doi(doi: str) -> str:
        """Validate DOI format."""
        doi = DataValidator.sanitize_string(doi, 100)

        if not DataValidator.DOI_REGEX.match(doi):
            raise ValidationError("Invalid DOI format", "doi")

        return doi

    @staticmethod
    def validate_uuid(uuid_str: str, field_name: str = "id") -> str:
        """Validate UUID format."""
        uuid_str = DataValidator.sanitize_string(uuid_str, 36)

        if not DataValidator.UUID_REGEX.match(uuid_str):
            raise ValidationError(f"Invalid {field_name} format", field_name)

        return uuid_str

    @staticmethod
    def validate_year(year: Union[int, str, None]) -> Optional[int]:
        """Validate year format."""
        if year is None:
            return None

        if isinstance(year, str):
            try:
                year = int(year)
            except ValueError:
                raise ValidationError("Year must be a valid number", "year")

        if not (1800 <= year <= 2100):
            raise ValidationError("Year must be between 1800 and 2100", "year")

        return year

    @staticmethod
    def validate_authors(authors: List[str]) -> List[str]:
        """Validate and sanitize author list."""
        if not isinstance(authors, list):
            raise ValidationError("Authors must be a list", "authors")

        if len(authors) > 100:
            raise ValidationError("Too many authors (max 100)", "authors")

        sanitized_authors = []
        for i, author in enumerate(authors):
            if not isinstance(author, str):
                raise ValidationError(f"Author {i} must be a string", f"authors[{i}]")

            sanitized = DataValidator.sanitize_string(author, 200)
            if sanitized:  # Only add non-empty authors
                sanitized_authors.append(sanitized)

        return sanitized_authors

    @staticmethod
    def validate_pagination_params(
        page: Union[int, str],
        page_size: Union[int, str],
        max_page_size: int = 100
    ) -> tuple[int, int]:
        """Validate pagination parameters."""
        try:
            page = int(page) if isinstance(page, str) else page
            page_size = int(page_size) if isinstance(page_size, str) else page_size
        except ValueError:
            raise ValidationError("Page and page_size must be valid numbers", "pagination")

        if page < 1:
            raise ValidationError("Page must be >= 1", "page")

        if page_size < 1 or page_size > max_page_size:
            raise ValidationError(f"Page size must be between 1 and {max_page_size}", "page_size")

        return page, page_size

    @staticmethod
    def check_sql_injection(value: str) -> None:
        """Check for SQL injection patterns."""
        value_lower = value.lower()
        for pattern in DataValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                raise ValidationError("Potentially unsafe input detected", "input")

    @staticmethod
    def check_xss(value: str) -> None:
        """Check for XSS patterns."""
        value_lower = value.lower()
        for pattern in DataValidator.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                raise ValidationError("Potentially unsafe input detected", "input")

    @staticmethod
    def validate_query_text(query: str) -> str:
        """Validate and sanitize search query."""
        query = DataValidator.sanitize_string(query, 1000)

        if len(query.strip()) < 3:
            raise ValidationError("Query must be at least 3 characters long", "query")

        # Check for injection attacks
        DataValidator.check_sql_injection(query)
        DataValidator.check_xss(query)

        return query

    @staticmethod
    def validate_paper_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete paper data."""
        validated = {}

        # Required fields
        if 'title' not in data or not data['title']:
            raise ValidationError("Title is required", "title")

        validated['title'] = DataValidator.sanitize_string(data['title'], 500)

        # Optional fields
        if 'abstract' in data and data['abstract']:
            validated['abstract'] = DataValidator.sanitize_string(data['abstract'], 5000, allow_html=False)

        if 'authors' in data and data['authors']:
            validated['authors'] = DataValidator.validate_authors(data['authors'])

        if 'year' in data:
            validated['year'] = DataValidator.validate_year(data['year'])

        if 'doi' in data and data['doi']:
            validated['doi'] = DataValidator.validate_doi(data['doi'])

        if 'url' in data and data['url']:
            validated['url'] = DataValidator.validate_url(data['url'])

        if 'venue' in data and data['venue']:
            validated['venue'] = DataValidator.sanitize_string(data['venue'], 200)

        return validated

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            name = name[:255-len(ext)-1] if ext else name[:255]
            filename = f"{name}.{ext}" if ext else name

        return filename


# Convenience functions for common validations
def validate_search_query(query: str) -> str:
    """Validate search query input."""
    return DataValidator.validate_query_text(query)


def validate_paper_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Validate paper metadata."""
    return DataValidator.validate_paper_data(metadata)


def validate_pagination(page: int, page_size: int) -> tuple[int, int]:
    """Validate pagination parameters."""
    return DataValidator.validate_pagination_params(page, page_size)