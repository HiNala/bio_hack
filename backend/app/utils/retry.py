"""
Retry utilities for external API calls and operations.
"""

import asyncio
import logging
from typing import Callable, Any, Optional
from functools import wraps

from app.errors import ExternalAPIError, RateLimitError

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        retry_on: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_on = retry_on


async def retry_async(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: The async function to retry
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of the function call

    Raises:
        The last exception if all retries are exhausted
    """
    last_exception = None
    delay = config.initial_delay

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except config.retry_on as e:
            last_exception = e

            if attempt == config.max_attempts - 1:
                # Last attempt failed
                logger.error(
                    f"Function {func.__name__} failed after {config.max_attempts} attempts",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "last_error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                break

            # Calculate next delay with exponential backoff
            delay = min(delay * config.backoff_factor, config.max_delay)

            logger.warning(
                f"Function {func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}), "
                f"retrying in {delay:.1f}s",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": config.max_attempts,
                    "delay": delay,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )

            await asyncio.sleep(delay)

    # If we get here, all retries failed
    raise last_exception


def retry_on_failure(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retry_on: tuple = (ExternalAPIError, RateLimitError, Exception)
):
    """
    Decorator for retrying async functions on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each failure
        retry_on: Tuple of exception types to retry on
    """
    def decorator(func: Callable) -> Callable:
        config = RetryConfig(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            retry_on=retry_on
        )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config, *args, **kwargs)

        return wrapper
    return decorator


# Pre-configured retry decorators for common use cases
retry_external_api = retry_on_failure(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    retry_on=(ExternalAPIError, RateLimitError, ConnectionError, TimeoutError)
)

retry_database = retry_on_failure(
    max_attempts=2,
    initial_delay=0.5,
    max_delay=5.0,
    retry_on=(Exception,)  # Broad retry for database operations
)