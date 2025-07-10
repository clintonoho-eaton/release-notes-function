"""
Base Atlassian API client for interacting with Atlassian products.

This module provides the base class for Jira and Confluence API clients.
"""

import logging
import requests
from typing import Any, Dict, Optional

from src.exceptions.api_exceptions import HttpUnauthorizedError

# Suppress InsecureRequestWarning if needed
try:
    from urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

class BaseAtlassianClient:
    """Base class for Atlassian API clients."""
    
    def __init__(self, instance_url: str, username: str, api_token: str):
        """Initialize the Atlassian client with the given credentials.
        
        Args:
            instance_url: URL of the Atlassian instance
            username: Username for authentication
            api_token: API token for authentication
        """
        self.instance_url = instance_url
        self.username = username
        self.api_token = api_token
        self.auth = (username, api_token)
    
    def _parse_response(self, response):
        """Parse an API response consistently.
        
        Args:
            response: Response object from requests or a dictionary
            
        Returns:
            Dict: Parsed response data
        """
        import logging
        
        if response is None:
            logging.debug("Received None response")
            return {}
            
        if hasattr(response, 'json'):
            try:
                if not response.text:
                    return {}
                return response.json()
            except Exception as e:
                logging.error(f"Error parsing JSON response: {str(e)}")
                logging.debug(f"Response content: {response.text[:500]}")
                return {}
        else:
            # Already parsed JSON or a dictionary
            return response
            
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                      json_data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the API with standard error handling.
        
        Args:
            method: HTTP method (get, post, put, delete)
            endpoint: API endpoint (will be appended to instance_url)
            params: URL parameters
            json_data: JSON data for the request body
            headers: HTTP headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        url = f"{self.instance_url}{endpoint}"
        default_headers = {}
        if json_data:
            default_headers["Content-Type"] = "application/json"
            
        all_headers = {**default_headers, **(headers or {})}
        
        logging.debug(f"API Request: {method.upper()} {url}")
        if params:
            logging.debug(f"Request params: {params}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                params=params,
                json=json_data,
                headers=all_headers,
                verify=False
            )
            
            response_data = self._parse_response(response)
            
            if response.status_code == 200 or response.status_code == 201:
                return response_data
            elif response.status_code == 401:
                error_msg = f"Unauthorized access to {url}"
                logging.error(error_msg)
                raise HttpUnauthorizedError(error_msg)
            elif response.status_code == 404:
                logging.info(f"Resource not found: {url}")
                return {}
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logging.error(error_msg)
                raise Exception(error_msg)
                
        except HttpUnauthorizedError:
            raise
        except Exception as e:
            if "401" in str(e):
                raise HttpUnauthorizedError(f"Authentication failed: {str(e)}")
            logging.error(f"Request failed: {str(e)}")
            raise

    def _make_wiki_request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                          json_data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Confluence API with standard error handling.
        
        Args:
            method: HTTP method (get, post, put, delete)
            endpoint: API endpoint (will be appended to instance_url/wiki)
            params: URL parameters
            json_data: JSON data for the request body
            headers: HTTP headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        import logging
        
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
            
        # Append /wiki to the endpoint for Confluence API
        wiki_endpoint = f"/wiki{endpoint}"
        
        logging.debug(f"Making wiki request: {method.upper()} {self.instance_url}{wiki_endpoint}")
        
        try:
            result = self._make_request(method, wiki_endpoint, params, json_data, headers)
            logging.debug(f"Wiki request successful: {method.upper()} {self.instance_url}{wiki_endpoint}")
            return result
        except Exception as e:
            logging.error(f"Wiki request failed: {method.upper()} {self.instance_url}{wiki_endpoint}")
            import traceback
            logging.error(f"Wiki request error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise
