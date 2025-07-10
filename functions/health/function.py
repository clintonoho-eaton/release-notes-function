"""
Azure Functions HTTP triggers for health monitoring.
"""
import os
import json
import time
import logging

import azure.functions as func

from src.config.app_config import Config
from src.atlassian.jira_client import JiraAPIWrapper

# Create blueprint
health_bp = func.Blueprint()

# Initialize configuration
config_object = Config()

@health_bp.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint for monitoring.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger = logging.getLogger()
    logger.info("Health check requested")
    
    # Check if we can connect to dependencies
    health = {
        "status": "healthy",
        "timestamp": time.time(),
        "dependencies": {
            "jira_api": "unknown",
            "azure_openai": "unknown"
        },
        "diagnostics": {
            "jira_api": {},
            "azure_openai": {}
        }
    }
    
    # Check Jira connectivity
    try:
        logger.info("Health check: Testing JIRA API connection")
        
        # Extract config
        enricher_config = config_object.get_enricher_config("project = TEST", "Bug")
        
        # Add diagnostic information
        health["diagnostics"]["jira_api"] = {
            "url": enricher_config.get("jira_url", "Not configured"),
            "username": enricher_config.get("jira_username", "Not configured"),
            "ssl_verify": enricher_config.get("ssl_verify", True),
            "request_time": time.time()
        }
        
        # Create wrapper and test connection
        jira = JiraAPIWrapper(
            jira_username=enricher_config.get('jira_username'),
            jira_api_token=enricher_config.get('jira_api_key'),
            jira_instance_url=enricher_config.get('jira_url')
        )
        
        connection_result = jira.test_connection()
        health["dependencies"]["jira_api"] = "healthy" if connection_result else "unhealthy"
        
        if not connection_result:
            health["status"] = "degraded"
            health["diagnostics"]["jira_api"]["error"] = "Empty response from JIRA API"
            logger.warning("Health check: Empty response from JIRA API")
            
    except Exception as e:
        health["dependencies"]["jira_api"] = "unhealthy"
        health["status"] = "degraded"
        health["diagnostics"]["jira_api"]["error"] = str(e)
        health["diagnostics"]["jira_api"]["error_type"] = type(e).__name__
        logger.error(f"Health check for Jira failed: {str(e)}")
    
    health["diagnostics"]["jira_api"]["response_time"] = time.time()
    
    # Azure OpenAI health check would go here - omitting for brevity
    # In production, we would add a check for OpenAI connectivity
    
    # Return health status
    return func.HttpResponse(
        body=json.dumps(health),
        mimetype="application/json",
        status_code=200 if health["status"] == "healthy" else 207  # Multi-status
    )
