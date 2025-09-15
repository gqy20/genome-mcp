"""
Async utilities for Genome MCP.

This module provides async decorators and utility functions.
"""

import asyncio
from typing import Any, Callable, Optional

from genome_mcp.exceptions import TimeoutError


def retry_async(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator for retrying async functions.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        backoff_factor: Factor for exponential backoff
        exceptions: Tuple of exceptions to retry on

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        delay = retry_delay * (backoff_factor**attempt)
                        await asyncio.sleep(delay)
                    else:
                        pass

            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError("Unexpected error in retry decorator")

        return wrapper

    return decorator


def async_timeout(timeout_seconds: float) -> Callable:
    """
    Decorator to add timeout to async function.

    Args:
        timeout_seconds: Timeout in seconds

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError(
                    message=f"Function {func.__name__} timed out after {timeout_seconds} seconds",
                    timeout_duration=timeout_seconds,
                    operation=func.__name__,
                )

        return wrapper

    return decorator


def log_execution_time(func_name: Optional[str] = None) -> Callable:
    """
    Decorator to log function execution time.

    Args:
        func_name: Optional function name for logging

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                raise

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
