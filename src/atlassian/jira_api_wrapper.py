"""
JIRA API wrapper for interacting with JIRA.

This module provides JIRA-specific wrapper functionality.
"""

from typing import Any, Dict, List, Optional, ClassVar
import json
import logging

from src.exceptions.api_exceptions import HttpUnauthorizedError, JiraFetchError
from src.atlassian.api_wrapper import AtlassianAPIWrapper
from src.atlassian.jira_client import JiraClient
from src.atlassian.decorators.client_decorators import ensure_client_initialized, handle_api_errors

class JiraAPIWrapper(AtlassianAPIWrapper):
    """JIRA-specific API wrapper."""
    
    REQUIRED_CONFIG: ClassVar[List[str]] = ["jira_instance_url", "jira_username", "jira_api_token"]
    is_jira: ClassVar[bool] = True
    
    def initialize_client(self) -> bool:
        """Initialize the JIRA client if it is not already initialized."""
        if self.jira is None:
            missing_configs = self._validate_required_config(self.REQUIRED_CONFIG, "Jira")
            if missing_configs:
                return False
                
            try:
                logging.info(f"Initializing Jira client with URL: {self.jira_instance_url}")
                self.jira = JiraClient(
                    instance_url=self.jira_instance_url,
                    username=self.jira_username,
                    api_token=self.jira_api_token
                )
                logging.info("Jira client initialized successfully")
                return True
            except Exception as e:
                logging.error(f"Error initializing Jira client: {str(e)}")
                raise
                
        return True

    @handle_api_errors
    def test_connection(self) -> bool:
        """Test connection to Jira API."""
        self.initialize_client()
        self.jira.myself()
        logging.info("Successfully connected to Jira API")
        return True

    @ensure_client_initialized
    @handle_api_errors
    def search(self, query: str, max_results: int = 10) -> Dict:
        """Execute JQL and return the raw result."""
        logging.info(f"Executing Jira JQL query: {query}")
        logging.info(f"Maximum results requested: {max_results}")
        
        logging.debug("Query parameters:")
        logging.debug(f"- JQL Query: {query}")
        logging.debug(f"- Max Results: {max_results}")
        logging.debug(f"- Username: {self.jira_username}")
        logging.debug(f"- URL: {self.jira_instance_url}")
        
        issues = self.jira.jql(query=query, limit=max_results)
        
        if issues and "issues" in issues:
            logging.info(f"Found {len(issues['issues'])} issues out of {issues.get('total', 'unknown')} total")
        else:
            logging.warning("No issues found or unexpected response format")
        
        return issues

    @ensure_client_initialized
    @handle_api_errors
    def issue_create(self, query: str) -> Dict[str, Any]:
        """Create a Jira issue."""
        try:
            params = json.loads(query)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in issue_create: {str(e)}")
            raise
            
        result = self.jira.issue_create(fields=dict(params))
        logging.info(f"Successfully created issue: {result.get('key', 'unknown')}")
        return result

    @ensure_client_initialized
    def run(self, mode: str, query: str) -> Any:
        """Run the Jira wrapper with the specified mode and query."""
        try:
            if mode == "jql":
                return self.search(query)
            elif mode == "create_issue":
                return self.issue_create(query)
            else:
                error_msg = f"Unsupported mode: {mode}"
                logging.error(error_msg)
                return {"error": error_msg}
        except Exception as e:
            logging.error(f"Error in run: {str(e)}")
            return {"error": str(e)}
