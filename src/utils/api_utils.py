import logging
import requests
from typing import Dict, Any

from src.exceptions.api_exceptions import HttpUnauthorizedError, JiraFetchError

def handle_api_response(response: requests.Response, operation_name: str) -> Dict[str, Any]:
    """Handle API response consistently.
    
    Args:
        response: Response object from requests library
        operation_name: Name of the operation for logging
        
    Returns:
        JSON response data
        
    Raises:
        HttpUnauthorizedError: If the response status is 401 (Unauthorized)
        JiraFetchError: For all other non-200 status codes
    """
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        error_msg = f"Unauthorized: {operation_name}"
        logging.error(error_msg)
        raise HttpUnauthorizedError(error_msg)
    else:
        error_msg = f"Error {operation_name}: {response.status_code} - {response.text}"
        logging.error(error_msg)
        raise JiraFetchError(error_msg)
