"""
Timeout utilities and context managers.
"""
import asyncio
from typing import TypeVar, Coroutine
from contextlib import asynccontextmanager

T = TypeVar('T')


async def with_timeout(coro: Coroutine[any, any, T], timeout: float, default: T = None) -> T:
    """
    Execute a coroutine with a timeout.
    Returns default value if timeout occurs.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return default


@asynccontextmanager
async def timeout_context(seconds: float):
    """Context manager for timeout operations."""
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {seconds}s")







