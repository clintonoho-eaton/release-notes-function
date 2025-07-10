"""
Retry decorator with backoff for async functions.
"""
import asyncio
import functools
import logging
import time
from typing import Any, Awaitable, Callable, TypeVar

# Define type variables for the retry decorator
T = TypeVar('T')
R = TypeVar('R')

def async_retry_with_backoff(
    max_attempts: int = 3,
    initial_backoff: int = 1,
    backoff_multiplier: int = 2,
    retry_exceptions: tuple = (Exception,),
    excluded_exceptions: tuple = (),
    logger=None
) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """
    Decorator for async functions to implement retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_backoff: Initial backoff duration in seconds
        backoff_multiplier: Multiplier for the backoff duration after each attempt
        retry_exceptions: Tuple of exceptions that should trigger a retry
        excluded_exceptions: Tuple of exceptions that should not trigger a retry
        logger: Logger instance to use for logging
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            log = logger or logging.getLogger()
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    log.info(f"Executing {func.__name__} (attempt {attempt + 1}/{max_attempts})")
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    log.info(f"{func.__name__} completed successfully in {time.time() - start_time:.2f}s")
                    return result
                except excluded_exceptions as exc:
                    log.error(f"Non-retryable error in {func.__name__}: {exc}")
                    raise
                except retry_exceptions as exc:
                    last_exception = exc
                    attempt += 1
                    if attempt >= max_attempts:
                        log.error(f"{func.__name__} failed after {max_attempts} attempts. Last error: {exc}")
                        break
                    
                    backoff = initial_backoff * (backoff_multiplier ** (attempt - 1))
                    log.warning(f"{func.__name__} failed with error: {exc}. Retrying after {backoff}s...")
                    
                    # Get more details if available
                    if hasattr(exc, 'response'):
                        try:
                            log.error(f"Response details: {exc.response.text}")
                        except:
                            pass
                    
                    await asyncio.sleep(backoff)
            
            if last_exception:
                raise last_exception
            
            # This should not be reached but just in case
            raise RuntimeError(f"{func.__name__} failed with unknown error after {max_attempts} attempts")
        
        return wrapper
    return decorator
