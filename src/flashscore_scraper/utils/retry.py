"""Retry logic utilities."""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

try:
    from playwright.async_api import TimeoutError as PlaywrightTimeout

    HAS_PLAYWRIGHT = True
except ImportError:
    PlaywrightTimeout = Exception
    HAS_PLAYWRIGHT = False


def with_retry(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """
    Decorator for retrying failed operations with exponential backoff.

    Handles:
    - Network timeouts
    - Connection errors
    - Temporary failures

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Retry decorator
    """
    retry_exceptions = [
        ConnectionError,
        TimeoutError,
    ]

    if HAS_PLAYWRIGHT:
        retry_exceptions.append(PlaywrightTimeout)

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(tuple(retry_exceptions)),
        reraise=True,
    )
