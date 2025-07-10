"""
Decorators for Atlassian API clients and wrappers.
"""
import functools
import logging
from typing import Any, Callable

from src.exceptions.api_exceptions import HttpUnauthorizedError, JiraFetchError

def ensure_client_initialized(func: Callable) -> Callable:
    """Decorator to ensure client is initialized before method execution."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'initialize_client'):
            raise AttributeError(f"{self.__class__.__name__} must implement initialize_client method")
            
        if not self.initialize_client():
            error_msg = f"Failed to initialize {self.__class__.__name__}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
            
        return func(self, *args, **kwargs)
    return wrapper

def handle_api_errors(func: Callable) -> Callable:
    """Decorator to handle common API errors."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except HttpUnauthorizedError:
            # Re-raise auth errors directly
            raise
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logging.error(error_msg)
            if "401" in str(e):
                raise HttpUnauthorizedError(f"Authentication failed: {str(e)}")
            if hasattr(self, 'is_jira') and self.is_jira:
                raise JiraFetchError(error_msg)
            raise
    return wrapper
