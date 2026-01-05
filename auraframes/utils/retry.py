"""Retry utilities with exponential backoff for async operations."""
import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from loguru import logger

from auraframes.exceptions import NetworkError

T = TypeVar('T')


async def with_retry(
    fn: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    initial_delay: float = 0.5,
    retry_exceptions: tuple[type[Exception], ...] = (NetworkError, ConnectionError, TimeoutError),
    **kwargs: Any
) -> T:
    """
    Execute an async function with retry and exponential backoff.

    :param fn: Async function to execute
    :param args: Positional arguments to pass to fn
    :param max_retries: Maximum number of retry attempts (default 3)
    :param backoff_factor: Multiplier for delay between retries (default 1.5)
    :param initial_delay: Initial delay in seconds (default 0.5)
    :param retry_exceptions: Tuple of exception types to retry on
    :param kwargs: Keyword arguments to pass to fn
    :return: Result of fn
    :raises: The last exception if all retries fail
    """
    delay = initial_delay
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except retry_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} for {fn.__name__} "
                    f"after {type(e).__name__}: {e}. Waiting {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    f"All {max_retries} retries failed for {fn.__name__}: {e}"
                )

    # Should never reach here, but satisfy type checker
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected retry state")


def retry(
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    initial_delay: float = 0.5,
    retry_exceptions: tuple[type[Exception], ...] = (NetworkError, ConnectionError, TimeoutError),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for adding retry with exponential backoff to async functions.

    :param max_retries: Maximum number of retry attempts (default 3)
    :param backoff_factor: Multiplier for delay between retries (default 1.5)
    :param initial_delay: Initial delay in seconds (default 0.5)
    :param retry_exceptions: Tuple of exception types to retry on
    :return: Decorated function
    """
    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await with_retry(
                fn,
                *args,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                initial_delay=initial_delay,
                retry_exceptions=retry_exceptions,
                **kwargs
            )
        return wrapper
    return decorator
