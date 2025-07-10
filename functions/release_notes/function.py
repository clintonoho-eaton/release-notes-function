"""
Azure Functions HTTP triggers for release notes generation.
"""
import os
import re
import json
import time
import logging
import asyncio
from typing import Any
from unittest import result
from venv import logger

import azure.functions as func

from src.config.app_config import Config
from src.atlassian.jira_issue_ai_analyzer import JiraEnricher
from src.exceptions.api_exceptions import HttpUnauthorizedError, JiraFetchError
from src.utils.release_note_utils import generate_release_note_text

# Create blueprint
release_notes_bp = func.Blueprint()

# Initialize configuration
config_object = Config()

# Input validation function
def validate_input(proj: str, fixver: str, issuetype: str) -> tuple:
    """
    Validate input parameters.
    
    Args:
        proj: Project key
        fixver: Fix version
        issuetype: Issue type
        
    Returns:
        Tuple of (is_valid, errors)
    """
    errors = []
    if not re.match(r'^[A-Za-z0-9_]+$', proj):
        errors.append("Invalid project key format")
    
    if not fixver:
        errors.append("Fix version cannot be empty")
        
    valid_issue_types = ['Bug', 'Issue', 'Epic', 'Comp']
    if issuetype not in valid_issue_types:
        errors.append(f"Issue type must be one of: {', '.join(valid_issue_types)}")
    
    if errors:
        return False, errors
    return True, []

# Process with timeout function
async def process_with_timeout(config, timeout_seconds=900):  # Increased from 300 to 900 seconds (15 minutes)
    """
    Process with timeout to prevent hanging processes.
    Enhanced for concurrent processing with longer timeout.
    
    Args:
        config: Enricher configuration
        timeout_seconds: Timeout in seconds (default 15 minutes for concurrent processing)
        
    Returns:
        Result of the enricher
        
    Raises:
        TimeoutError: If the process takes too long
    """
    logger = logging.getLogger()
    start_time = time.time()
    
    try:
        # Log the start of processing with concurrency info
        logger.info(f"Starting JQL processing: {config.get('jql', 'None')}")
        logger.debug(f"Max results configured: {config.get('max_results', 'Not specified')}")
        logger.debug(f"Max concurrent AI calls: {config.get('max_concurrent_ai_calls', 5)}")
        logger.debug(f"AI batch size: {config.get('ai_batch_size', 10)}")
        logger.debug(f"Timeout set to: {timeout_seconds} seconds")
        
        # Log key configuration settings at debug level
        for key in ['jira_url', 'azure_openai_endpoint', 'create_local_files', 'create_confluence_pages']:
            if key in config:
                logger.debug(f"Config[{key}] = {config[key]}")
        
        # Ensure correct API version for o4-mini model
        if config.get('azure_openai_gpt_deployment') == 'o4-mini' and config.get('azure_openai_chat_completions_api_version') != '2024-12-01-preview':
            logger.warning("API version mismatch! Fixing API version for o4-mini model")
            config['azure_openai_chat_completions_api_version'] = '2024-12-01-preview'
        
        logger.info("Creating JiraEnricher instance with async support")
        enricher = JiraEnricher(config)
        logger.info("JiraEnricher instance created successfully")
        
        # Create a task with timeout (increased for concurrent processing)
        logger.info("Starting fetch_and_analyze_issues with concurrent processing and timeout")
        logger.debug("About to call enricher.fetch_and_analyze_issues() with async concurrency")
        result = await asyncio.wait_for(
            enricher.fetch_and_analyze_issues(),
            timeout=timeout_seconds
        )
        logger.info("fetch_and_analyze_issues completed successfully with concurrent processing")
        
        # Log the completion of processing
        elapsed_time = time.time() - start_time
        logger.info(f"Processing completed successfully in {elapsed_time:.2f} seconds for JQL: {config.get('jql', 'None')}")
        return result
        
    except asyncio.TimeoutError:
        elapsed_time = time.time() - start_time
        logger.error(f"Operation timed out after {timeout_seconds} seconds (elapsed: {elapsed_time:.2f}s)")
        raise TimeoutError(f"Processing timed out after {timeout_seconds} seconds. This may be due to high API load or too many concurrent requests. Please try with fewer issues or reduce concurrency settings.")
        
    except HttpUnauthorizedError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Authentication error during processing (elapsed: {elapsed_time:.2f}s): {str(e)}")
        raise
        
    except JiraFetchError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Jira fetch error during processing (elapsed: {elapsed_time:.2f}s): {str(e)}")
        raise
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error during processing (elapsed: {elapsed_time:.2f}s): {str(e)}")
        raise

@release_notes_bp.route(route="release-notes/{proj}/{fixver}/{issuetype}", methods=["PUT"])
async def release_notes_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to process release notes with default max_results from configuration.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger = logging.getLogger()
    
    # Extract route parameters
    proj = req.route_params.get('proj')
    fixver = req.route_params.get('fixver')
    issuetype = req.route_params.get('issuetype')
    
    logger.info(f"Processing request: /release-notes/{proj}/{fixver}/{issuetype}")
    
    # Validate input parameters
    valid, errors = validate_input(proj, fixver, issuetype)
    if not valid:
        logger.error(f"Input validation failed: {errors}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": errors}),
            mimetype="application/json",
            status_code=400
        )
    
    jql = f"project = {proj} AND fixversion = {fixver} AND issuetype = {issuetype}"
    logger.debug(f"Constructed JQL: {jql}")
    
    # Get configuration from Config class with fix version
    config = config_object.get_enricher_config(jql, issuetype, fixver)
    
    # Log the configuration being used
    logger.debug(f"Processing {issuetype}s for project {proj} and fixversion {fixver}")
    logger.debug(f"Using max_results value: {config.get('max_results', 'Not specified')}")
    
    try:
        # Use timeout function to prevent hanging processes
        result = await process_with_timeout(config)
        logger.info(f"Successfully processed request for {proj}/{fixver}/{issuetype}")
        
        response = {
            "status": "success",
            "project": proj,
            "fixVersion": fixver,
            "issueType": issuetype,
            "details": f"Successfully processed request for {proj}/{fixver}/{issuetype}",
            "confluence_pages": result.get("confluence_pages", {
                "created": [],
                "updated": [],
                "errors": []
            }) if result else {
                "created": [],
                "updated": [],
                "errors": []
            }
        }
        
        return func.HttpResponse(
            body=json.dumps(response),
            mimetype="application/json",
            status_code=200
        )
        
    except HttpUnauthorizedError:
        logger.error("Unauthorized access to Jira API")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Unauthorized"}),
            mimetype="application/json",
            status_code=401
        )
    except TimeoutError as e:
        logger.error(f"Request timed out: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=504  # Gateway Timeout
        )
    except JiraFetchError as e:
        logger.error(f"Jira fetch error: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Jira API error: {str(e)}"}),
            mimetype="application/json",
            status_code=502  # Bad Gateway
        )
    except Exception as e:
        logger.error(f"Error processing release notes: {str(e)}", exc_info=True)  # Include stack trace
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Internal Server Error"}),
            mimetype="application/json",
            status_code=500
        )

@release_notes_bp.route(route="release-notes/{proj}/{fixver}/{issuetype}/{max_results:int}", methods=["PUT"])
async def release_notes_with_limit_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to process release notes with specific max_results parameter.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger = logging.getLogger()
    
    # Extract route parameters
    proj = req.route_params.get('proj')
    fixver = req.route_params.get('fixver')
    issuetype = req.route_params.get('issuetype')
    max_results = int(req.route_params.get('max_results'))
    
    logger.info(f"Processing request: /release-notes/{proj}/{fixver}/{issuetype}/{max_results}")
    
    # Validate input parameters
    valid, errors = validate_input(proj, fixver, issuetype)
    if not valid:
        logger.error(f"Input validation failed: {errors}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": errors}),
            mimetype="application/json",
            status_code=400
        )
    
    # Validate max_results
    if max_results <= 0 or max_results > 1000:
        logger.error(f"Invalid max_results value: {max_results}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "max_results must be between 1 and 1000"}),
            mimetype="application/json",
            status_code=400
        )
        
    jql = f"project = {proj} AND fixversion = {fixver} AND issuetype = {issuetype}"
    logger.debug(f"Constructed JQL: {jql}")
    
    # Get configuration with custom max_results and fix version
    config = config_object.get_enricher_config_with_options(jql, issuetype, fixver, max_results=max_results)
    
    # Log the configuration being used
    logger.debug(f"Processing {issuetype}s for project {proj} and fixversion {fixver} with max_results: {max_results}")
    logger.debug(f"Using max_results value: {config.get('max_results', 'Not specified')}")
    
    try:
        # Use timeout function to prevent hanging processes
        result = await process_with_timeout(config)
        logger.info(f"Successfully processed request for {proj}/{fixver}/{issuetype} with max_results: {max_results}")
        
        response = {
            "status": "success",
            "project": proj,
            "fixVersion": fixver,
            "issueType": issuetype,
            "maxResults": max_results,
            "details": f"Successfully processed request for {proj}/{fixver}/{issuetype} with max_results: {max_results}",
            "confluence_pages": result.get("confluence_pages", {
                "created": [],
                "updated": [],
                "errors": []
            }) if result else {
                "created": [],
                "updated": [],
                "errors": []
            }
        }
        
        return func.HttpResponse(
            body=json.dumps(response),
            mimetype="application/json",
            status_code=200
        )
        
    except HttpUnauthorizedError:
        logger.error("Unauthorized access to Jira API")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Unauthorized"}),
            mimetype="application/json",
            status_code=401
        )
    except TimeoutError as e:
        logger.error(f"Request timed out: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=504  # Gateway Timeout
        )
    except JiraFetchError as e:
        logger.error(f"Jira fetch error: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Jira API error: {str(e)}"}),
            mimetype="application/json",
            status_code=502  # Bad Gateway
        )
    except Exception as e:
        logger.error(f"Error processing release notes: {str(e)}", exc_info=True)  # Include stack trace
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Internal Server Error"}),
            mimetype="application/json",
            status_code=500
        )

@release_notes_bp.route(route="release-notes/{proj}/{issue_key}", methods=["PUT"])
async def release_notes_single_issue_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to process release notes for a specific issue.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger = logging.getLogger()
    
    # Extract route parameters
    proj = req.route_params.get('proj')
    issue_key = req.route_params.get('issue_key')
    
    logger.info(f"Processing request: /release-notes/{proj}/{issue_key}")
    
    # Validate input parameters
    if not proj or not issue_key:
        logger.error("Missing required parameters: proj or issue_key")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Missing required parameters: proj or issue_key"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Basic validation of issue key format (PROJECT-NUMBER)
    if not re.match(r'^[A-Za-z0-9_]+-\d+$', issue_key):
        logger.error(f"Invalid issue key format: {issue_key}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Invalid issue key format: {issue_key}. Expected format: PROJECT-NUMBER (e.g., IP-51180)"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Validate that issue key starts with the project
    if not issue_key.upper().startswith(proj.upper() + '-'):
        logger.error(f"Issue key {issue_key} does not belong to project {proj}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Issue key {issue_key} does not belong to project {proj}"}),
            mimetype="application/json",
            status_code=400
        )
    
    logger.debug(f"Processing single issue: {issue_key} for project {proj}")
    
    # Get base configuration - we'll use minimal config since we're processing just one issue
    base_config = config_object.get_enricher_config("", "", "")
    
    # Override with single issue settings
    base_config['max_results'] = 1
    base_config['jql'] = f"key = {issue_key}"
    
    # Log the configuration being used
    logger.debug(f"Processing single issue {issue_key} for project {proj}")
    logger.debug(f"Using configuration for single issue processing")
    
    try:
        # Create enricher for single issue processing
        logger.info("Creating JiraEnricher instance for single issue processing")
        enricher = JiraEnricher(base_config)
        logger.info("JiraEnricher instance created successfully")
        
        # Process the single issue with timeout
        logger.info(f"Starting single issue analysis for {issue_key}")
        result = await asyncio.wait_for(
            enricher.fetch_and_analyze_single_issue(issue_key),
            timeout=300  # 5 minute timeout for single issue
        )
        logger.info(f"Single issue analysis completed for {issue_key}")
        
        if result.get("status") == "success":
            logger.info(f"Successfully processed single issue: {issue_key}")
            
            response = {
                "status": "success",
                "project": proj,
                "issue_key": issue_key,
                "processing_time": result.get("processing_time", 0),
                "details": result.get("details", []),
                "warnings": result.get("warnings", []),
                "confluence_pages": result.get("confluence_pages", {
                    "created": [],
                    "updated": [],
                    "errors": []
                })
            }
            
            return func.HttpResponse(
                body=json.dumps(response),
                mimetype="application/json",
                status_code=200
            )
        else:
            # Handle error response from the analyzer
            logger.error(f"Error processing issue {issue_key}: {result.get('message', 'Unknown error')}")
            return func.HttpResponse(
                body=json.dumps({
                    "status": "error", 
                    "project": proj,
                    "issue_key": issue_key,
                    "message": result.get('message', 'Failed to process issue'),
                    "warnings": result.get("warnings", [])
                }),
                mimetype="application/json",
                status_code=400 if "not found" in result.get('message', '').lower() else 500
            )
        
    except asyncio.TimeoutError:
        logger.error(f"Request timed out for issue: {issue_key}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Processing timed out for issue {issue_key}. Please try again."}),
            mimetype="application/json",
            status_code=504  # Gateway Timeout
        )
    except HttpUnauthorizedError:
        logger.error("Unauthorized access to Jira API")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Unauthorized"}),
            mimetype="application/json",
            status_code=401
        )
    except JiraFetchError as e:
        logger.error(f"Jira fetch error for issue {issue_key}: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Jira API error: {str(e)}"}),
            mimetype="application/json",
            status_code=502  # Bad Gateway
        )
    except Exception as e:
        logger.error(f"Error processing single issue {issue_key}: {str(e)}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Internal Server Error"}),
            mimetype="application/json",
            status_code=500
        )

@release_notes_bp.route(route="release-notes/custom", methods=["POST"])
async def release_notes_custom_config_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to process release notes with custom Atlassian configuration provided in request body.
    
    Expected JSON body:
    {
        "jql": "project = ABC AND fixversion = 1.0 AND issuetype = Bug",
        "issue_type": "Bug",
        "max_results": 10,
        "atlassian_config": {
            "username": "user@company.com",
            "api_key": "ATATT3xFfGF0...",
            "instance_url": "https://company.atlassian.net",
            "confluence_space": "PROJECT",
            "confluence_parent": "123456789"
        }
    }
    
    Args:
        req: HTTP request with JSON body containing configuration
        
    Returns:
        HTTP response
    """
    logger = logging.getLogger()
    
    logger.info("Processing request: /release-notes/custom with custom Atlassian configuration")
    
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            logger.error("Request body is empty or invalid JSON")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": "Request body must contain valid JSON"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Validate required fields
        required_fields = ["jql"]
        missing_fields = [field for field in required_fields if field not in req_body]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Get atlassian_config with fallback to environment variables for local development
        atlassian_config = req_body.get("atlassian_config", {})
        
        # For local development, fall back to environment variables if config not provided
        # Azure Functions sets WEBSITE_SITE_NAME when running in the cloud
        is_local_dev = not os.getenv("WEBSITE_SITE_NAME")
        
        logger.debug(f"Environment detection: local_development={is_local_dev}, WEBSITE_SITE_NAME={'present' if os.getenv('WEBSITE_SITE_NAME') else 'absent'}")
        
        def get_config_value(config_key: str, env_key: str, required: bool = True) -> str:
            """Get configuration value with fallback to environment for local development."""
            value = atlassian_config.get(config_key)
            if not value and is_local_dev:
                value = os.getenv(env_key)
                if value:
                    logger.debug(f"Using {env_key} from environment for local development")
            return value
        
        # Build effective configuration with fallbacks
        effective_config = {
            "username": get_config_value("username", "ATLASSIAN_USERNAME"),
            "api_key": get_config_value("api_key", "ATLASSIAN_API_KEY"),
            "instance_url": get_config_value("instance_url", "ATLASSIAN_INSTANCE_URL") or get_config_value("instance_url", "ATLASSIAN_URL"),
            "confluence_space": get_config_value("confluence_space", "CONFLUENCE_SPACE"),
            "confluence_parent": get_config_value("confluence_parent", "CONFLUENCE_PARENT")
        }
        
        # Validate that all required fields are now available
        required_atlassian_fields = ["username", "api_key", "instance_url", "confluence_space", "confluence_parent"]
        missing_atlassian_fields = [field for field in required_atlassian_fields if not effective_config[field]]
        if missing_atlassian_fields:
            error_msg = f"Missing required Atlassian configuration fields: {', '.join(missing_atlassian_fields)}"
            if is_local_dev:
                error_msg += ". For local development, provide values in request body or set environment variables in local.settings.json"
            else:
                error_msg += ". Please provide all required fields in the atlassian_config object"
            
            logger.error(error_msg)
            return func.HttpResponse(
                body=json.dumps({
                    "status": "error", 
                    "message": error_msg,
                    "required_fields": required_atlassian_fields,
                    "local_development": is_local_dev
                }),
                mimetype="application/json",
                status_code=400
            )
        
        # Use the effective configuration
        atlassian_config = effective_config
        
        # Extract parameters
        jql = req_body.get("jql")
        issue_type = req_body.get("issue_type", "")
        max_results = req_body.get("max_results", config_object.DEFAULT_MAX_RESULTS)
        
        # Validate max_results
        if not isinstance(max_results, int) or max_results <= 0 or max_results > 1000:
            logger.error(f"Invalid max_results value: {max_results}")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": "max_results must be an integer between 1 and 1000"}),
                mimetype="application/json",
                status_code=400
            )
        
        logger.debug(f"Processing JQL: {jql}")
        logger.debug(f"Using custom Atlassian configuration for user: {atlassian_config['username']}")
        
        # Get configuration using custom Atlassian config
        config = config_object.get_enricher_config_with_custom_atlassian(
            jql, issue_type, atlassian_config, None, max_results=max_results
        )
        
        # Log configuration being used (without sensitive data)
        logger.debug(f"Processing with max_results: {config.get('max_results')}")
        logger.debug(f"Confluence space: {config.get('confluence_space')}")
        logger.debug(f"Confluence parent: {config.get('confluence_parent')}")
        
        # Use timeout function to prevent hanging processes
        result = await process_with_timeout(config)
        logger.info(f"Successfully processed custom configuration request")
        
        # Get issue count from the result
        issue_count = result.get("issue_count", 0) if result else 0
        
        # Log the issue count for debugging
        logger.info(f"JQL '{jql}' returned {issue_count} issues")
        
        response = {
            "status": "success",
            "jql": jql,
            "issue_type": issue_type,
            "max_results": max_results,
            "issue_count": issue_count,
            "confluence_space": atlassian_config["confluence_space"],
            "confluence_parent": atlassian_config["confluence_parent"],
            "details": f"Successfully processed JQL query with custom Atlassian configuration. Found {issue_count} issues.",
            "confluence_pages": result.get("confluence_pages", {
                "created": [],
                "updated": [],
                "errors": []
            }) if result else {
                "created": [],
                "updated": [],
                "errors": []
            }
        }
        
        return func.HttpResponse(
            body=json.dumps(response),
            mimetype="application/json",
            status_code=200
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Invalid JSON in request body"}),
            mimetype="application/json",
            status_code=400
        )
    except HttpUnauthorizedError:
        logger.error("Unauthorized access to Jira API with provided credentials")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Unauthorized access to Jira/Confluence API. Please check your credentials."}),
            mimetype="application/json",
            status_code=401
        )
    except TimeoutError as e:
        logger.error(f"Request timed out: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=504  # Gateway Timeout
        )
    except JiraFetchError as e:
        logger.error(f"Jira fetch error: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Jira API error: {str(e)}"}),
            mimetype="application/json",
            status_code=502  # Bad Gateway
        )
    except Exception as e:
        logger.error(f"Error processing release notes with custom config: {str(e)}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Internal Server Error"}),
            mimetype="application/json",
            status_code=500
        )

@release_notes_bp.route(route="release-notes/single", methods=["POST"])
async def release_notes_single_custom_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to process a single issue with custom Atlassian configuration provided in request body.
    
    Expected JSON body:
    {
        "issue_key": "PROJECT-12345",
        "atlassian_config": {
            "username": "user@company.com",
            "api_key": "ATATT3xFfGF0...",
            "instance_url": "https://company.atlassian.net",
            "confluence_space": "PROJECT",
            "confluence_parent": "123456789"
        }
    }
    
    Args:
        req: HTTP request with JSON body containing configuration
        
    Returns:
        HTTP response
    """
    logger = logging.getLogger()
    
    logger.info("Processing request: /release-notes/single with custom Atlassian configuration")
    
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            logger.error("Request body is empty or invalid JSON")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": "Request body must contain valid JSON"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Validate required fields
        required_fields = ["issue_key"]
        missing_fields = [field for field in required_fields if field not in req_body]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Get atlassian_config with fallback to environment variables for local development
        atlassian_config = req_body.get("atlassian_config", {})
        
        # For local development, fall back to environment variables if config not provided
        # Azure Functions sets WEBSITE_SITE_NAME when running in the cloud
        is_local_dev = not os.getenv("WEBSITE_SITE_NAME")
        
        logger.debug(f"Environment detection: local_development={is_local_dev}, WEBSITE_SITE_NAME={'present' if os.getenv('WEBSITE_SITE_NAME') else 'absent'}")
        
        def get_config_value(config_key: str, env_key: str, required: bool = True) -> str:
            """Get configuration value with fallback to environment for local development."""
            value = atlassian_config.get(config_key)
            if not value and is_local_dev:
                value = os.getenv(env_key)
                if value:
                    logger.debug(f"Using {env_key} from environment for local development")
            return value
        
        # Build effective configuration with fallbacks
        effective_config = {
            "username": get_config_value("username", "ATLASSIAN_USERNAME"),
            "api_key": get_config_value("api_key", "ATLASSIAN_API_KEY"),
            "instance_url": get_config_value("instance_url", "ATLASSIAN_INSTANCE_URL") or get_config_value("instance_url", "ATLASSIAN_URL"),
            "confluence_space": get_config_value("confluence_space", "CONFLUENCE_SPACE"),
            "confluence_parent": get_config_value("confluence_parent", "CONFLUENCE_PARENT")
        }
        
        # Validate that all required fields are now available
        required_atlassian_fields = ["username", "api_key", "instance_url", "confluence_space", "confluence_parent"]
        missing_atlassian_fields = [field for field in required_atlassian_fields if not effective_config[field]]
        if missing_atlassian_fields:
            error_msg = f"Missing required Atlassian configuration fields: {', '.join(missing_atlassian_fields)}"
            if is_local_dev:
                error_msg += ". For local development, provide values in request body or set environment variables in local.settings.json"
            else:
                error_msg += ". Please provide all required fields in the atlassian_config object"
            
            logger.error(error_msg)
            return func.HttpResponse(
                body=json.dumps({
                    "status": "error", 
                    "message": error_msg,
                    "required_fields": required_atlassian_fields,
                    "local_development": is_local_dev
                }),
                mimetype="application/json",
                status_code=400
            )
        
        # Use the effective configuration
        atlassian_config = effective_config
        
        # Extract and validate issue key
        issue_key = req_body.get("issue_key")
        if not issue_key or not re.match(r'^[A-Za-z0-9_]+-\d+$', issue_key):
            logger.error(f"Invalid issue key format: {issue_key}")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": f"Invalid issue key format: {issue_key}. Expected format: PROJECT-NUMBER (e.g., IP-51180)"}),
                mimetype="application/json",
                status_code=400
            )
        
        logger.debug(f"Processing single issue: {issue_key}")
        logger.debug(f"Using custom Atlassian configuration for user: {atlassian_config['username']}")
        
        # Get configuration using custom Atlassian config
        base_config = config_object.get_enricher_config_with_custom_atlassian(
            f"key = {issue_key}", "", atlassian_config, None, max_results=1
        )
        
        # Log configuration being used (without sensitive data)
        logger.debug(f"Processing single issue with custom configuration")
        logger.debug(f"Confluence space: {base_config.get('confluence_space')}")
        logger.debug(f"Confluence parent: {base_config.get('confluence_parent')}")
        
        # Create enricher for single issue processing
        logger.info("Creating JiraEnricher instance for single issue processing with custom config")
        enricher = JiraEnricher(base_config)
        logger.info("JiraEnricher instance created successfully")
        
        # Process the single issue with timeout
        logger.info(f"Starting single issue analysis for {issue_key}")
        result = await asyncio.wait_for(
            enricher.fetch_and_analyze_single_issue(issue_key),
            timeout=300  # 5 minute timeout for single issue
        )
        logger.info(f"Single issue analysis completed for {issue_key}")
        
        if result.get("status") == "success":
            logger.info(f"Successfully processed single issue: {issue_key}")
            
            # Calculate issue count (should be 1 for success, 0 for errors)
            issue_count = 1
            
            response = {
                "status": "success",
                "issue_key": issue_key,
                "issue_count": issue_count,
                "confluence_space": atlassian_config["confluence_space"],
                "confluence_parent": atlassian_config["confluence_parent"],
                "processing_time": result.get("processing_time", 0),
                "details": result.get("details", []),
                "warnings": result.get("warnings", []),
                "confluence_pages": result.get("confluence_pages", {
                    "created": [],
                    "updated": [],
                    "errors": []
                })
            }
            
            return func.HttpResponse(
                body=json.dumps(response),
                mimetype="application/json",
                status_code=200
            )
        else:
            # Handle error response from the analyzer
            logger.error(f"Error processing issue {issue_key}: {result.get('message', 'Unknown error')}")
            return func.HttpResponse(
                body=json.dumps({
                    "status": "error", 
                    "issue_key": issue_key,
                    "message": result.get('message', 'Failed to process issue'),
                    "warnings": result.get("warnings", [])
                }),
                mimetype="application/json",
                status_code=400 if "not found" in result.get('message', '').lower() else 500
            )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Invalid JSON in request body"}),
            mimetype="application/json",
            status_code=400
        )
    except asyncio.TimeoutError:
        logger.error(f"Request timed out for issue: {req_body.get('issue_key', 'unknown')}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Processing timed out for issue {req_body.get('issue_key', 'unknown')}. Please try again."}),
            mimetype="application/json",
            status_code=504  # Gateway Timeout
        )
    except HttpUnauthorizedError:
        logger.error("Unauthorized access to Jira API with provided credentials")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Unauthorized access to Jira/Confluence API. Please check your credentials."}),
            mimetype="application/json",
            status_code=401
        )
    except JiraFetchError as e:
        logger.error(f"Jira fetch error for issue {req_body.get('issue_key', 'unknown')}: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": f"Jira API error: {str(e)}"}),
            mimetype="application/json",
            status_code=502  # Bad Gateway
        )
    except Exception as e:
        logger.error(f"Error processing single issue with custom config: {str(e)}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Internal Server Error"}),
            mimetype="application/json",
            status_code=500
        )
    ###
@release_notes_bp.route(
    route="release-notes/dynatrace-event",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS
)
async def release_notes_dynatrace_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to process a Dynatrace deployment event and generate release notes.
    """
    logger = logging.getLogger()

    # 1. Safely parse JSON body and check type
    try:
        data = req.get_json()
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        logger.error(f"Raw body: {req.get_body()}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "HTTP request does not contain valid JSON data"}),
            mimetype="application/json",
            status_code=400
        )

    if not data:
        logger.error("No JSON data received!")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "Missing JSON body"}),
            mimetype="application/json",
            status_code=400
        )

    if not isinstance(data, dict):
        logger.error(f"JSON body was not a dict: {data}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "JSON body must be an object/dict"}),
            mimetype="application/json",
            status_code=400
        )

    # 2. Extract fields safely
    release_name = data.get("release_name")
    repository = data.get("repository")
    tag = data.get("tag")
    deployment_status = data.get("deployment_status")
    jira_issue_keys = data.get("jira_issue_keys", [])

    # 3. Validate required fields
    if not jira_issue_keys or not isinstance(jira_issue_keys, list):
        logger.error(f"jira_issue_keys missing or not a list: {jira_issue_keys}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": "No Jira issue keys provided or jira_issue_keys is not a list."}),
            mimetype="application/json",
            status_code=400
        )

    # 4. Enrich all Jira issues in a batch
    try:
        # Build atlassian_config from environment variables
        atlassian_config = {
            "username": os.getenv("ATLASSIAN_USERNAME"),
            "api_key": os.getenv("ATLASSIAN_API_KEY"),
            "instance_url": os.getenv("ATLASSIAN_URL"),
            "confluence_space": os.getenv("CONFLUENCE_SPACE") or os.getenv("CONFLUENCE_SPACE_KEY"),
            "confluence_parent": os.getenv("CONFLUENCE_PARENT") or os.getenv("CONFLUENCE_PARENT_PAGE_ID"),
        }
        logger.info(f"jira_issue_keys: {jira_issue_keys}, type: {type(jira_issue_keys)}")
        logger.info(f"atlassian_config: {atlassian_config}, type: {type(atlassian_config)}")
        base_config = config_object.get_enricher_config_with_custom_atlassian(
            f"key in ({','.join(jira_issue_keys)})", "", atlassian_config, None, max_results=len(jira_issue_keys)
        )
        enricher = JiraEnricher(base_config)
        result = await asyncio.wait_for(
            enricher.fetch_and_analyze_issues(),
            timeout=900
        )
        logger.info(f"Result from fetch_and_analyze_issues: {result}, type: {type(result)}")

        if not result or not isinstance(result, dict):
            logger.error("No or invalid result from fetch_and_analyze_issues()")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": "No analysis result."}),
                mimetype="application/json",
                status_code=500
            )

        enriched_issues = result.get("enriched_issues", [])
        logger.info(f"enriched_issues: {enriched_issues}, type: {type(enriched_issues)}")

        if enriched_issues is None or not isinstance(enriched_issues, list):
            logger.error("enriched_issues is not a list!")
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": "enriched_issues is not a list"}),
                mimetype="application/json",
                status_code=500
            )

        # (Optional) GitHub commit fetching placeholder
        # commits = await fetch_commits(repository, tag) if you add this feature
        
        # Generate standardized release note
        logger.info("About to call generate_release_note_text")
        try:
            release_note = generate_release_note_text(
                release_name=release_name,
                repository=repository,
                tag=tag,
                deployment_status=deployment_status,
                jira_issues=enriched_issues,
                # commits=commits
            )
        except Exception as gen_note_exc:
            logger.error(f"Error inside generate_release_note_text: {gen_note_exc}")
            import traceback
            logger.error(traceback.format_exc())
            return func.HttpResponse(
                body=json.dumps({"status": "error", "message": f"generate_release_note_text failed: {gen_note_exc}"}),
                mimetype="application/json",
                status_code=500
            )

        response = {
            "status": "success",
            "release_note": release_note,
            "release_metadata": {
                "release_name": release_name,
                "repository": repository,
                "tag": tag,
                "deployment_status": deployment_status
            }
        }
        return func.HttpResponse(
            body=json.dumps(response),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        import traceback
        logger.error(f"Error in Dynatrace event handler: {str(e)}")
        logger.error(traceback.format_exc())
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )