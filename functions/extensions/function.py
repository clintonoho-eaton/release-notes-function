"""
Azure Functions HTTP triggers for extension routes.
"""
import json
import logging
import asyncio
from typing import Any, Dict

import azure.functions as func

from src.config.app_config import Config
from src.atlassian.jira_issue_ai_analyzer import JiraEnricher
from src.exceptions.api_exceptions import HttpUnauthorizedError, JiraFetchError

# Create blueprint
extensions_bp = func.Blueprint()

# Initialize configuration
config_object = Config()

# Process with timeout function
async def process_with_timeout(config, timeout_seconds=300):
    """
    Process with timeout to prevent hanging processes.
    
    Args:
        config: Enricher configuration
        timeout_seconds: Timeout in seconds
        
    Returns:
        Result of the enricher
        
    Raises:
        TimeoutError: If the process takes too long
    """
    try:
        # Create enricher
        enricher = JiraEnricher(config)
        
        # Create a task with timeout
        result = await asyncio.wait_for(
            enricher.fetch_and_analyze_issues(),
            timeout=timeout_seconds
        )
        
        # Include processing time if not present in result
        if isinstance(result, dict) and 'processing_time' not in result:
            result['processing_time'] = 0  # Default value
            
        return result
        
    except asyncio.TimeoutError:
        logging.error(f"Operation timed out after {timeout_seconds} seconds")
        raise TimeoutError(f"Processing timed out after {timeout_seconds} seconds. Please try with fewer issues.")
        
    except Exception as e:
        logging.error(f"Error during processing: {str(e)}")
        raise

@extensions_bp.route(route="extensions/sample", methods=["GET"])
def sample_extension(req: func.HttpRequest) -> func.HttpResponse:
    """
    Sample extension endpoint.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger = logging.getLogger()
    logger.info("Sample extension endpoint called")
    
    response = {
        "status": "success",
        "message": "Sample extension endpoint working correctly"
    }
    
    return func.HttpResponse(
        body=json.dumps(response),
        mimetype="application/json",
        status_code=200
    )

# Add more extension routes here
# Example:
# @extensions_bp.route(route="extensions/custom-workflow", methods=["POST"])
# async def custom_workflow(req: func.HttpRequest) -> func.HttpResponse:
#     ...
