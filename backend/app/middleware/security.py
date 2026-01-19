"""
Security Headers Middleware

Adds comprehensive security headers to all responses.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List, Optional


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    def __init__(
        self,
        app,
        csp_directives: Optional[Dict[str, List[str]]] = None,
        hsts_max_age: int = 31536000,
        include_subdomains: bool = True,
        preload: bool = False,
    ):
        super().__init__(app)

        # Content Security Policy
        self.csp_directives = csp_directives or self._get_default_csp()

        # HSTS settings
        self.hsts_max_age = hsts_max_age
        self.include_subdomains = include_subdomains
        self.preload = preload

    def _get_default_csp(self) -> Dict[str, List[str]]:
        """Get default Content Security Policy directives."""
        return {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],  # Allow Next.js
            "style-src": ["'self'", "'unsafe-inline'"],  # Allow styled-components/tailwind
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "connect-src": ["'self'", "https://api.openalex.org", "https://api.semanticscholar.org"],
            "frame-src": ["'none'"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
        }

    def _build_csp_header(self) -> str:
        """Build CSP header from directives."""
        directives = []
        for directive, sources in self.csp_directives.items():
            if sources:
                directives.append(f"{directive} {' '.join(sources)}")
            else:
                directives.append(directive)

        return "; ".join(directives)

    def _build_hsts_header(self) -> str:
        """Build HSTS header."""
        hsts = f"max-age={self.hsts_max_age}"
        if self.include_subdomains:
            hsts += "; includeSubDomains"
        if self.preload:
            hsts += "; preload"
        return hsts

    async def dispatch(self, request: Request, call_next):
        """Add security headers to the response."""
        response = await call_next(request)

        # Only add security headers for HTML responses and API responses
        if self._should_add_security_headers(request, response):
            # Content Security Policy
            csp_header = self._build_csp_header()
            response.headers["Content-Security-Policy"] = csp_header

            # HTTP Strict Transport Security (only for HTTPS)
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = self._build_hsts_header()

            # X-Frame-Options
            response.headers["X-Frame-Options"] = "DENY"

            # X-Content-Type-Options
            response.headers["X-Content-Type-Options"] = "nosniff"

            # X-XSS-Protection
            response.headers["X-XSS-Protection"] = "1; mode=block"

            # Referrer-Policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Permissions-Policy (formerly Feature-Policy)
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), "
                "accelerometer=(), gyroscope=(), speaker=(), "
                "fullscreen=(self), autoplay=()"
            )

            # Cross-Origin-Embedder-Policy (for better security)
            response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"

            # Cross-Origin-Opener-Policy
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

            # Cross-Origin-Resource-Policy
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response

    def _should_add_security_headers(self, request: Request, response: Response) -> bool:
        """Determine if security headers should be added."""
        # Add to HTML pages and API responses
        content_type = response.headers.get("content-type", "").lower()

        # HTML pages
        if "text/html" in content_type:
            return True

        # API responses (JSON)
        if "application/json" in content_type:
            return True

        # API docs
        if "/docs" in str(request.url.path) or "/redoc" in str(request.url.path):
            return True

        return False


class SecurityHeaders:
    """Utility class for security headers."""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get all security headers as a dictionary."""
        return {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), accelerometer=(), gyroscope=(), speaker=(), fullscreen=(self), autoplay=()",
            "Cross-Origin-Embedder-Policy": "credentialless",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    @staticmethod
    def get_csp_header() -> str:
        """Get Content Security Policy header."""
        directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "connect-src": ["'self'", "https://api.openalex.org", "https://api.semanticscholar.org"],
            "frame-src": ["'none'"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
        }

        csp_parts = []
        for directive, sources in directives.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")
            else:
                csp_parts.append(directive)

        return "; ".join(csp_parts)