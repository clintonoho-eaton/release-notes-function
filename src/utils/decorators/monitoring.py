"""
Performance monitoring decorator for async functions.
"""
import functools
import logging
import time
from typing import Any, Callable

def async_performance_monitor(logger=None) -> Callable:
    """
    Decorator for monitoring the performance of async functions.
    
    Args:
        logger: Logger instance to use for logging
        
    Returns:
        Decorated function with performance monitoring
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = logger or logging.getLogger()
            start_time = time.time()
            
            try:
                # Get function details for better logging
                module = func.__module__
                name = func.__qualname__
                func_path = f"{module}.{name}"
                
                log.info(f"Starting {func_path}")
                result = await func(*args, **kwargs)
                
                # Log performance metrics
                execution_time = time.time() - start_time
                log.info(f"Completed {func_path} in {execution_time:.2f}s")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log.error(f"Error in {func.__name__} after {execution_time:.2f}s: {str(e)}")
                raise
                
        return wrapper
    return decorator
