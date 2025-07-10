"""
Confluence API wrapper for interacting with Confluence.

This module provides wrapper functionality for Confluence API client.
"""

import json
import logging
from typing import Any, Dict, Optional, List, ClassVar

from src.exceptions.api_exceptions import HttpUnauthorizedError
from src.atlassian.api_wrapper import AtlassianAPIWrapper
from src.atlassian.confluence_client import ConfluenceClient
from src.atlassian.decorators.client_decorators import ensure_client_initialized, handle_api_errors

class ConfluenceAPIWrapper(AtlassianAPIWrapper):
    """Wrapper for Confluence API."""
    
    REQUIRED_CONFIG: ClassVar[List[str]] = ["confluence_instance_url", "confluence_username", "confluence_api_token"]
    is_jira: ClassVar[bool] = False
    
    def initialize_client(self) -> bool:
        """Initialize the Confluence client if it is not already initialized."""
        if self.confluence is None:
            missing_configs = self._validate_required_config(self.REQUIRED_CONFIG, "Confluence")
            if missing_configs:
                return False
                
            try:
                logging.info(f"Initializing Confluence client with URL: {self.confluence_instance_url}")
                self.confluence = ConfluenceClient(
                    instance_url=self.confluence_instance_url,
                    username=self.confluence_username,
                    api_token=self.confluence_api_token
                )
                logging.info("Confluence client initialized successfully")
                return True
            except Exception as e:
                logging.error(f"Error initializing Confluence client: {str(e)}")
                raise
                
        return True

    @handle_api_errors
    def test_connection(self) -> bool:
        """Test connection to Confluence API."""
        self.initialize_client()
        self.confluence.get_space("TEST")
        logging.info("Successfully connected to Confluence API")
        return True

    @ensure_client_initialized
    @handle_api_errors
    def page_create(self, query: str) -> Dict[str, Any]:
        """Create or update a Confluence page."""
        try:
            params = json.loads(query)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in page_create: {str(e)}"
            logging.error(error_msg)
            return {"status": "error", "message": error_msg, "pages_created": 0}
            
        return self.confluence.page_create(params)

    @ensure_client_initialized
    def run(self, mode: str, query: str) -> Any:
        """Run the Confluence wrapper with the specified mode and query."""
        try:
            if mode == "create_page":
                return self.page_create(query)
            else:
                error_msg = f"Unsupported mode: {mode}"
                logging.error(error_msg)
                return {"error": error_msg}
        except Exception as e:
            logging.error(f"Error in run: {str(e)}")
            return {"error": str(e)}
