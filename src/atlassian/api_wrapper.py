"""
Atlassian API wrapper for interacting with Jira and Confluence.

This module provides base wrapper functionality for Atlassian API clients.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, List

from pydantic import BaseModel, model_validator

from src.exceptions.api_exceptions import HttpUnauthorizedError
from src.atlassian.decorators.client_decorators import ensure_client_initialized, handle_api_errors


def get_from_dict_or_env(config_dict: Dict[str, Any], dict_key: str, env_key: str, default: str = "") -> str:
    """Get a value from dictionary or environment variable.
    
    Args:
        config_dict: Dictionary to check first
        dict_key: Key to look for in the dictionary
        env_key: Environment variable name to check if dict key not found
        default: Default value if neither dict nor env has the value
        
    Returns:
        The configuration value
    """
    # First check the dictionary
    if dict_key in config_dict and config_dict[dict_key]:
        return str(config_dict[dict_key])
    
    # Then check environment variables
    return os.getenv(env_key, default)

class AtlassianAPIWrapper(BaseModel):
    """Base wrapper for Atlassian APIs (Jira, Confluence)."""

    jira: Any = None  #: :meta private:
    confluence: Any = None  #: :meta private:
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_instance_url: Optional[str] = None
    confluence_username: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_instance_url: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_environment(self) -> 'AtlassianAPIWrapper':
        """Validate that api key and environment variables exist."""
        jira_config = self._get_jira_config()
        config = {**jira_config, **self._get_confluence_config(jira_config)}
        for key, value in config.items():
            setattr(self, key, value)
        return self

    def _validate_required_config(self, config_keys: List[str], service_name: str) -> List[str]:
        """Validate that required configuration values are present."""
        missing = [key.upper() for key in config_keys if not getattr(self, key, None)]
        if missing:
            logging.error(f"Missing {service_name} configuration: {', '.join(missing)}")
        return missing

    def _get_jira_config(self) -> Dict[str, str]:
        """Get JIRA configuration from environment variables."""
        return {
            "jira_username": get_from_dict_or_env(dict(self), "jira_username", "ATLASSIAN_USERNAME", ""),
            "jira_api_token": get_from_dict_or_env(dict(self), "jira_api_token", "ATLASSIAN_API_KEY", ""),
            "jira_instance_url": get_from_dict_or_env(dict(self), "jira_instance_url", "ATLASSIAN_URL", "")
        }

    def _get_confluence_config(self, jira_config: Dict[str, str]) -> Dict[str, str]:
        """Get Confluence configuration from environment variables, with JIRA fallbacks."""
        base_url = jira_config["jira_instance_url"].partition('/rest')[0] or jira_config["jira_instance_url"]
        
        def get_config(conf_key: str, env_key: str, jira_key: str) -> str:
            return get_from_dict_or_env(dict(self), conf_key, env_key, "") or jira_config[jira_key]

        return {
            "confluence_username": get_config("confluence_username", "CONFLUENCE_USERNAME", "jira_username"),
            "confluence_api_token": get_config("confluence_api_token", "CONFLUENCE_API_KEY", "jira_api_token"), 
            "confluence_instance_url": get_from_dict_or_env(dict(self), "confluence_instance_url", "CONFLUENCE_URL", "") or base_url
        }

    @handle_api_errors
    def test_connection(self) -> bool:
        """Test connection to API.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement test_connection")

    @handle_api_errors
    def run(self, mode: str, query: str) -> Any:
        """Run the API wrapper with the specified mode and query.
        
        Args:
            mode: Operation mode
            query: Query string
            
        Returns:
            Result of the operation
        """
        raise NotImplementedError("Subclasses must implement run")
