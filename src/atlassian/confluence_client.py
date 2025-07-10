"""
Confluence API client for interacting with Confluence.

This module provides utilities to interact with the Confluence API.
"""

import logging
import os
import requests
from typing import Any, Dict, List, Optional
import urllib.parse

from src.exceptions.api_exceptions import HttpUnauthorizedError
from src.atlassian.base_client import BaseAtlassianClient

class ConfluenceClient(BaseAtlassianClient):
    """Client for interacting with Confluence API."""
    
    def __init__(self, instance_url: str, username: str, api_token: str):
        """Initialize the Confluence client with the given credentials.
        
        Args:
            instance_url: URL of the Confluence instance
            username: Username for authentication
            api_token: API token for authentication
        """
        super().__init__(instance_url, username, api_token)
        
        # Initialize API URL for REST API requests
        # Standardize the instance URL format first
        if not instance_url.endswith('/'):
            instance_url = f"{instance_url}/"
            
        # Set up the API URL for the REST API
        self.api_url = f"{instance_url.rstrip('/')}/wiki/rest/api"
        logging.debug(f"Initialized Confluence API URL: {self.api_url}")
        
    def _make_api_request(self, method: str, endpoint: str, params: Optional[Dict] = None,
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
        return self._make_wiki_request(method, endpoint, params, json_data, headers)
        
    def get_space(self, space_key: str) -> Dict[str, Any]:
        """Get a Confluence space by key.
        
        Args:
            space_key: Key of the space
            
        Returns:
            Space data or None if not found
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        endpoint = f"/rest/api/space/{space_key}"
        return self._make_api_request("get", endpoint)
        
    def get_page_by_id(self, page_id: str) -> Dict[str, Any]:
        """Get a Confluence page by ID.
        
        Args:
            page_id: ID of the page
            
        Returns:
            Page data or None if not found
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        endpoint = f"/rest/api/content/{page_id}"
        params = {"expand": "version,space"}
        return self._make_api_request("get", endpoint, params=params)
        
    def get_page_by_title(self, space: str, title: str) -> Dict[str, Any]:
        """Get a Confluence page by title in a space.
        
        Args:
            space: Space key
            title: Page title
            
        Returns:
            Page data or None if not found
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        # URL-encode the title in the query parameter is handled by requests
        endpoint = "/rest/api/content"
        params = {
            "spaceKey": space,
            "title": title,
            "expand": "version,space"
        }
        
        try:
            full_url = f"{self.instance_url}/wiki/rest/api/content"
            logging.debug(f"API Request: GET {full_url}")
            logging.debug(f"Request params: {params}")
            
            response = self._make_api_request("get", endpoint, params=params)
            
            # Parse the response and log
            response_data = self._parse_response(response)
            
            # Log the response for debugging
            logging.debug(f"API Response status: {response_data.get('size', 'unknown')} results found")
            
            if response_data and response_data.get('results') and len(response_data.get('results')) > 0:
                logging.info(f"Found page '{title}' in space '{space}' with ID: {response_data['results'][0]['id']}")
                return response_data.get('results')[0]
            else:
                logging.info(f"No page found with title '{title}' in space '{space}'")
                return None
                
        except Exception as e:
            logging.error(f"Error getting page by title '{title}': {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None
        
    def create_page(self, space: str, title: str, body: str, parent_id: Optional[str] = None, representation: str = "storage") -> Dict[str, Any]:
        """Create a new Confluence page.
        
        Args:
            space: Space key
            title: Page title
            body: Page content
            parent_id: ID of the parent page (optional)
            representation: Content representation (default: storage)
            
        Returns:
            Created page data
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        import logging
        import json
        
        logging.debug(f"Creating new page: '{title}' in space '{space}'")
        
        # Prepare request data
        data = {
            "type": "page",
            "title": title,
            "space": {"key": space},
            "body": {
                representation: {
                    "value": body,
                    "representation": representation
                }
            }
        }
        
        # Add parent page reference if provided
        if parent_id:
            logging.debug(f"Setting parent page ID: {parent_id}")
            data["ancestors"] = [{"id": parent_id}]
            
        # Make API request to create the page
        try:
            # Use the REST API endpoint for content creation
            endpoint = "/rest/api/content"
            full_url = f"{self.instance_url}/wiki/rest/api/content"
            logging.debug(f"API Request: POST {full_url}")
            
            # Create a copy of data with truncated body for logging
            log_data = dict(data)
            if "body" in log_data:
                log_data["body"] = "[CONTENT TRUNCATED]"
            logging.debug(f"Request data: {json.dumps(log_data)}")
            
            # Send the request
            response = self._make_wiki_request("POST", endpoint, json_data=data)
            
            # Parse the response
            response_json = self._parse_response(response)
            
            if response_json and 'id' in response_json:
                logging.info(f"Successfully created page '{title}' with ID: {response_json['id']}")
                logging.debug(f"Page URL: {self.instance_url}/wiki/pages/viewpage.action?pageId={response_json['id']}")
            else:
                logging.warning(f"Page creation for '{title}' returned unexpected response: {response_json}")
            
            return response_json
            
        except Exception as e:
            logging.error(f"Error creating page '{title}' in space '{space}': {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise
        
    def update_page(self, page_id: str, title: str, body: str, version: Optional[int] = None, representation: str = "storage") -> Dict[str, Any]:
        """Update an existing Confluence page.
        
        Args:
            page_id: ID of the page
            title: Page title
            body: Page content
            version: Current version number (optional, will be retrieved if not provided)
            representation: Content representation (default: storage)
            
        Returns:
            Updated page data
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        # First get the current page to check version if not provided
        if version is None:
            current_page = self.get_page_by_id(page_id)
            if not current_page:
                raise Exception(f"Cannot update page {page_id}: Page not found")
            version = current_page.get('version', {}).get('number', 0)
        
        # Increment version number for update
        new_version = int(version) + 1
        
        endpoint = f"/rest/api/content/{page_id}"
        
        # Prepare the request data
        data = {
            "type": "page",
            "title": title,
            "body": {"storage": {"value": body, "representation": representation}},
            "version": {"number": new_version}
        }
        
        response = self._make_api_request("put", endpoint, json_data=data)
        
        logging.info(f"Successfully updated page '{title}' (ID: {page_id})")
        return response
        
    def delete_page(self, page_id: str) -> Dict[str, Any]:
        """Delete a Confluence page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            Response data
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        endpoint = f"/rest/api/content/{page_id}"
        return self._make_api_request("delete", endpoint)

    def page_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a Confluence page.
        
        Args:
            params: Dictionary with page parameters including space, title, body, and parent_id
            
        Returns:
            Dictionary with operation result including status, url and created/updated page details
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            Exception: For other API errors
        """
        import logging
        import os
        import traceback
        from src.utils.html import format_confluence_page
        
        # Log the parameters for troubleshooting, excluding body to keep log manageable
        debug_params = dict(params)
        if 'body' in debug_params:
            debug_params['body'] = f"[Content length: {len(params.get('body', ''))}]"
        logging.debug(f"Confluence page params: {debug_params}")
        
        # Extract parameters
        space_key = params.get('space')
        title = params.get('title')
        body = params.get('body')
        parent_id = params.get('parent_id')
        
        try:
            # Format the body using the utility function
            logging.debug(f"Formatting page content for '{title}'")
            formatted_body = format_confluence_page(params)
            
            # If formatting was successful, replace the body
            if formatted_body:
                body = formatted_body
                logging.debug(f"Successfully formatted page content, length: {len(body)}")
            else:
                logging.warning(f"No formatted body generated for '{title}'")
        
            # Validate required parameters
            missing_params = []
            if not space_key:
                missing_params.append("space")
            if not title:
                missing_params.append("title")
            if not body and not formatted_body:
                missing_params.append("body")
            
            if missing_params:
                error_msg = f"Missing required parameters: {', '.join(missing_params)}"
                logging.error(error_msg)
                return {"status": "error", "message": error_msg, "pages_created": 0}
            
            # Set body to a default value if still None
            if not body:
                body = f"<p>Page content for {title}</p>"
                logging.warning(f"Using default page content for '{title}'")
            
            logging.info(f"Creating/updating page: '{title}' in space: '{space_key}' with parent_id: {parent_id}")
            logging.debug(f"Parent ID details - from params: {params.get('parent_id')}, final value: {parent_id}")
            
            try:            
                # Try to find existing page
                logging.debug(f"Checking if page '{title}' exists in space '{space_key}'")
                existing_page = self.get_page_by_title(space_key, title)
                
                if existing_page:
                    # Update existing page
                    logging.info(f"Found existing page '{title}' with ID: {existing_page['id']}. Updating...")
                    result = self.update_page(
                        page_id=existing_page['id'],
                        title=title,
                        body=body,
                        version=existing_page.get('version', {}).get('number')
                    )
                    # Generate page URL
                    page_url = f"{self.instance_url}/wiki/pages/viewpage.action?pageId={result['id']}"
                    return {
                        "status": "success", 
                        "result": "updated", 
                        "page": result, 
                        "url": page_url
                    }
                else:
                    # Create new page
                    logging.info(f"No existing page '{title}' found. Creating new page...")
                    
                    # Get parent_id from environment variable if not provided
                    # Support both CONFLUENCE_PARENT_ID and CONFLUENCE_PARENT environment variables
                    env_parent_id = os.environ.get('CONFLUENCE_PARENT_ID') or os.environ.get('CONFLUENCE_PARENT')
                    if not parent_id and env_parent_id:
                        parent_id = env_parent_id
                        logging.info(f"Using parent_id from environment variable: {parent_id}")
                    
                    # Log parent_id status
                    if parent_id:
                        logging.debug(f"Using parent_id: {parent_id}")
                    else:
                        logging.warning(f"No parent_id provided for new page '{title}'")
                    
                    # Use direct API call instead of calling create_page to avoid recursion
                    data = {
                        "type": "page",
                        "title": title,
                        "space": {"key": space_key},
                        "body": {
                            "storage": {
                                "value": body,
                                "representation": "storage"
                            }
                        }
                    }
                    
                    # Add parent page reference if provided
                    if parent_id:
                        data["ancestors"] = [{"id": parent_id}]
                        
                    # Make API request to create the page
                    import json
                    endpoint = "/rest/api/content"
                    full_url = f"{self.instance_url}/wiki/rest/api/content"
                    logging.debug(f"API Request: POST {full_url}")
                    
                    # Create a copy of data with truncated body for logging
                    log_data = dict(data)
                    if "body" in log_data:
                        log_data["body"] = "[CONTENT TRUNCATED]"
                    logging.debug(f"Request data: {json.dumps(log_data)}")  # Don't log full body
                    
                    response = self._make_wiki_request("POST", endpoint, json_data=data)
                    
                    # Parse the response
                    result = self._parse_response(response)
                    # Generate page URL
                    page_url = f"{self.instance_url}/wiki/pages/viewpage.action?pageId={result['id']}"
                    logging.info(f"Successfully created page '{title}' with ID: {result['id']}")
                    return {
                        "status": "success", 
                        "result": "created", 
                        "page": result, 
                        "url": page_url
                    }
                    
            except Exception as e:            
                error_msg = f"Error creating/updating Confluence page: {str(e)}"
                logging.error(error_msg)
                logging.error(f"Traceback: {traceback.format_exc()}")
                return {"status": "error", "message": error_msg, "pages_created": 0}
                
        except Exception as e:
            error_msg = f"Error formatting Confluence page content: {str(e)}"
            logging.error(error_msg)
            logging.error(f"Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": error_msg, "pages_created": 0}
