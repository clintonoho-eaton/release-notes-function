"""
Context managers for Atlassian API clients.
"""
import logging
from typing import Any, Dict, Optional, Union

from ..jira_client import JiraAPIWrapper
from ..confluence_api_wrapper import ConfluenceAPIWrapper
from ..confluence_client import ConfluenceClient
from .client_factory import JiraClientFactory, ConfluenceClientFactory

class ClientContextManager:
    """
    Async context manager for Atlassian API clients.
    
    Example usage:
    ```
    async with ClientContextManager(config, "jira") as jira_client:
        issues = jira_client.search("project = XYZ")
    ```
    """
    
    def __init__(self, config: Dict[str, Any], client_type: str):
        """
        Initialize context manager.
        
        Args:
            config: Configuration dictionary
            client_type: Type of client ("jira" or "confluence")
        """
        self.config = config
        self.client_type = client_type.lower()
        self.client = None
        
    async def __aenter__(self) -> Optional[Union[JiraAPIWrapper, ConfluenceAPIWrapper, ConfluenceClient]]:
        """
        Create and return client on context entry.
        
        Returns:
            JiraAPIWrapper, ConfluenceAPIWrapper, or ConfluenceClient instance
        
        Raises:
            ValueError: If client_type is invalid
        """
        if self.client_type == "jira":
            self.client = JiraClientFactory.create(self.config)
        elif self.client_type == "confluence":
            self.client = ConfluenceClientFactory.create(self.config)
        else:
            raise ValueError(f"Unsupported client type: {self.client_type}")
        
        if not self.client:
            logging.error(f"Failed to create {self.client_type} client")
            
        return self.client
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Clean up on context exit."""
        # Currently, no cleanup is needed, but this method can be extended
        # if cleanup operations are required in the future
        self.client = None
