"""Pagination utilities for async API calls."""
import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from loguru import logger

from auraframes.exceptions import NetworkError
from auraframes.utils.retry import with_retry

T = TypeVar('T')


async def paginate(
    fetch_fn: Callable[..., Awaitable[tuple[list[T], str | None]]],
    *args: Any,
    delay: float = 0.5,
    progress_callback: Callable[[int], None] | None = None,
    max_retries: int = 3,
    **kwargs: Any
) -> list[T]:
    """
    Generic async pagination helper with retry support.

    Calls fetch_fn repeatedly until no more pages, collecting all results.
    Each page fetch is retried with exponential backoff on network errors.

    :param fetch_fn: Async function that returns (items, next_cursor)
    :param args: Positional arguments to pass to fetch_fn
    :param delay: Delay between pagination requests (default 0.5s)
    :param progress_callback: Optional callback(count) called after each page
    :param max_retries: Maximum retries per page fetch (default 3)
    :param kwargs: Keyword arguments to pass to fetch_fn
    :return: All items from all pages
    :raises NetworkError: If a page fetch fails after all retries
    """
    items: list[T] = []

    async def fetch_page(**fetch_kwargs: Any) -> tuple[list[T], str | None]:
        return await with_retry(
            fetch_fn,
            *args,
            max_retries=max_retries,
            retry_exceptions=(NetworkError, ConnectionError, TimeoutError),
            **{**kwargs, **fetch_kwargs}
        )

    try:
        result, cursor = await fetch_page()
        items.extend(result)
        if progress_callback:
            progress_callback(len(items))

        while cursor:
            await asyncio.sleep(delay)
            result, cursor = await fetch_page(cursor=cursor)
            items.extend(result)
            if progress_callback:
                progress_callback(len(items))

    except Exception as e:
        logger.error(f"Pagination failed after fetching {len(items)} items: {e}")
        raise

    return items
