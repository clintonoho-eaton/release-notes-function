"""
Utilities for async operations and performance optimization.
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Callable, Optional, TypeVar, Awaitable
from functools import wraps

T = TypeVar('T')

class AsyncBatchProcessor:
    """Utility class for processing items in concurrent batches."""
    
    def __init__(
        self,
        max_concurrent: int = 5,
        batch_size: int = 10,
        delay_between_batches: float = 0.5
    ):
        """
        Initialize the batch processor.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
            batch_size: Number of items per batch
            delay_between_batches: Delay in seconds between batches
        """
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)
    
    async def process_items(
        self,
        items: List[Any],
        processor_func: Callable[[Any], Awaitable[T]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[T]:
        """
        Process items in concurrent batches.
        
        Args:
            items: List of items to process
            processor_func: Async function to process each item
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of processed results
        """
        total_items = len(items)
        all_results = []
        processed_count = 0
        
        self.logger.info(f"Processing {total_items} items with max {self.max_concurrent} concurrent operations")
        
        # Process items in batches
        for batch_start in range(0, total_items, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_items)
            batch = items[batch_start:batch_end]
            batch_num = (batch_start // self.batch_size) + 1
            total_batches = (total_items + self.batch_size - 1) // self.batch_size
            
            self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
            
            # Create tasks for concurrent processing within the batch
            async def process_with_semaphore(item):
                async with self.semaphore:
                    return await processor_func(item)
            
            tasks = [asyncio.create_task(process_with_semaphore(item)) for item in batch]
            
            # Wait for all tasks in the batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend(batch_results)
            
            processed_count += len(batch)
            
            if progress_callback:
                progress_callback(processed_count, total_items)
            
            # Add delay between batches to be gentle on APIs
            if batch_end < total_items:
                await asyncio.sleep(self.delay_between_batches)
        
        self.logger.info(f"Completed processing {total_items} items")
        return all_results


def async_timeout(timeout_seconds: int):
    """
    Decorator to add timeout to async functions.
    
    Args:
        timeout_seconds: Timeout in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
        return wrapper
    return decorator


def async_rate_limit(calls_per_second: float):
    """
    Decorator to rate limit async function calls.
    
    Args:
        calls_per_second: Maximum calls per second
    """
    min_interval = 1.0 / calls_per_second
    last_called = 0.0
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_called
            current_time = time.time()
            elapsed = current_time - last_called
            
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                await asyncio.sleep(sleep_time)
            
            last_called = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class AsyncPerformanceMonitor:
    """Monitor performance of async operations."""
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.end_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting {self.name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if exc_type:
            self.logger.error(f"{self.name} failed after {duration:.2f}s: {exc_val}")
        else:
            self.logger.info(f"{self.name} completed in {duration:.2f}s")


def create_async_semaphore_pool(max_concurrent: int = 5) -> asyncio.Semaphore:
    """
    Create a semaphore for controlling concurrent async operations.
    
    Args:
        max_concurrent: Maximum number of concurrent operations
        
    Returns:
        asyncio.Semaphore instance
    """
    return asyncio.Semaphore(max_concurrent)


async def run_with_concurrency_limit(
    tasks: List[Awaitable[T]],
    max_concurrent: int = 5
) -> List[T]:
    """
    Run tasks with a concurrency limit.
    
    Args:
        tasks: List of awaitable tasks
        max_concurrent: Maximum number of concurrent tasks
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_task(task):
        async with semaphore:
            return await task
    
    limited_tasks = [run_task(task) for task in tasks]
    return await asyncio.gather(*limited_tasks)
