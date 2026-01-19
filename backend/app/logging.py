"""
Logging Configuration

Configures structured logging for the application.
"""

import logging
import sys
from typing import Dict, Any
from pythonjsonlogger import jsonlogger

from app.config import get_settings

settings = get_settings()


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add application context
        log_record['app_name'] = settings.app_name
        log_record['app_version'] = settings.app_version
        log_record['environment'] = 'development' if settings.debug else 'production'

        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id


def setup_logging() -> None:
    """Configure logging for the application."""

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler for development
    if settings.debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
    else:
        # JSON handler for production
        json_handler = logging.StreamHandler(sys.stdout)
        json_formatter = CustomJsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        json_handler.setFormatter(json_formatter)
        json_handler.setLevel(logging.INFO)
        logger.addHandler(json_handler)

    # Set specific log levels for noisy libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

    # Log application startup
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version}",
        extra={
            'app_name': settings.app_name,
            'app_version': settings.app_version,
            'debug': settings.debug
        }
    )