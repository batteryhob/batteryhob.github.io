"""Retry with exponential backoff for API calls."""

from __future__ import annotations

import time
import functools
from typing import TypeVar, Callable

from rich.console import Console

console = Console()

T = TypeVar("T")

# retriable error types (by class name, to avoid hard import deps)
RETRIABLE_ERRORS = {
    "APIConnectionError",
    "RateLimitError",
    "InternalServerError",
    "APITimeoutError",
    "APIStatusError",
    "ConnectionError",
    "TimeoutError",
}


def is_retriable(exc: Exception) -> bool:
    name = type(exc).__name__
    if name in RETRIABLE_ERRORS:
        return True
    # check for HTTP 429, 500, 502, 503, 529
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status and status in (429, 500, 502, 503, 529):
        return True
    return False


def with_retry(
    fn: Callable[..., T],
    max_retries: int = 4,
    base_delay: float = 2.0,
) -> Callable[..., T]:
    """Wrap a function with retry + exponential backoff."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if not is_retriable(e) or attempt == max_retries:
                    raise
                delay = base_delay * (2 ** attempt)
                console.print(f"[yellow]retry {attempt + 1}/{max_retries} in {delay:.0f}s: {e}[/]")
                time.sleep(delay)
        raise last_exc  # unreachable but satisfies type checker

    return wrapper
