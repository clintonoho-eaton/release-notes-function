"""
Jira client for interacting with Jira.

This module provides functionality for interacting with the Jira REST API.
"""

import json
import logging
import re
import requests
import os
import inspect
from typing import Any, Dict, List, Optional, ClassVar
from datetime import datetime
import urllib.parse

from pydantic import BaseModel
from urllib3.exceptions import InsecureRequestWarning
from src.exceptions.api_exceptions import HttpUnauthorizedError, JiraFetchError
from src.utils.api_utils import handle_api_response
from src.atlassian.base_client import BaseAtlassianClient
from src.atlassian.api_wrapper import AtlassianAPIWrapper

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class JiraClient(BaseAtlassianClient):
    """Client for interacting with Jira API."""
    
    def jql(self, query: str, limit: int = 10, startAt: int = 0) -> Dict[str, Any]:
        """Execute a JQL query using the REST API.
        
        Args:
            query: JQL query string
            limit: Maximum number of results to return
            startAt: Index of the first result to return (0-based)
            
        Returns:
            Dictionary with search results
        """
        search_endpoint = "/rest/api/2/search"
        params = {
            "jql": query,
            "maxResults": limit,
            "startAt": startAt,
            "fields": "*all"
        }
        return self._make_request("get", search_endpoint, params=params)
    
    def projects(self) -> List[Dict[str, Any]]:
        """Get all projects using the REST API.
        
        Returns:
            List of projects
        """
        projects_endpoint = "/rest/api/2/project"
        return self._make_request("get", projects_endpoint)
    
    def issue_get(self, issue_key: str) -> Dict[str, Any]:
        """Get a single issue by key using the REST API.
        
        Args:
            issue_key: The issue key (e.g., 'PROJ-123')
            
        Returns:
            Dictionary with issue data
            
        Raises:
            JiraFetchError: If the issue is not found or cannot be accessed
        """
        issue_endpoint = f"/rest/api/2/issue/{issue_key}"
        params = {
            "fields": "*all"
        }
        return self._make_request("get", issue_endpoint, params=params)
    
    def issue_create(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create an issue using the REST API.
        
        Args:
            fields: Dictionary of issue fields
            
        Returns:
            Created issue data
        """
        create_endpoint = "/rest/api/2/issue"
        return self._make_request("post", create_endpoint, json_data={"fields": fields})
    
    def myself(self) -> Dict[str, Any]:
        """Get current user information.
        
        Returns:
            User information
        """
        myself_endpoint = "/rest/api/2/myself"
        return self._make_request("get", myself_endpoint)

class JiraAPIWrapper(AtlassianAPIWrapper):
    """Wrapper for Jira API."""
    
    REQUIRED_CONFIG: ClassVar[List[str]] = ["jira_instance_url", "jira_username", "jira_api_token"]
    
    def initialize_jira_client(self) -> bool:
        """Initialize the JIRA client if it is not already initialized.
        
        Returns:
            bool: True if initialization was successful, False if required config is missing
            
        Raises:
            Exception: If initialization fails with an unexpected error
        """
        if self.jira is None:
            # Validate required configuration
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
        
        # Client already initialized
        return True
                


    def test_connection(self) -> bool:
        """Test connection to Jira API.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                return False
            
            # Test connection by fetching current user
            self.jira.myself()
            logging.info("Successfully connected to Jira API")
            return True
            
        except HttpUnauthorizedError:
            logging.error("Unauthorized access to Jira API. Check your credentials.")
            return False
        except Exception as e:
            logging.error(f"Error testing connection to Jira API: {str(e)}")
            return False
            
    def run_jql_search(self, jql: str, max_results: int = 10, 
                       fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Run a JQL search query against the Jira API.
        
        Args:
            jql: The JQL query to run
            max_results: Maximum number of results to return
            fields: List of fields to include in the response
            
        Returns:
            List of issues from the JQL search
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            JiraFetchError: For other API errors
        """
        try:
            logging.info(f"Running JQL search: {jql}")
            
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                raise JiraFetchError("Failed to initialize Jira client")
            
            # Execute the JQL query using custom client
            result = self.jira.jql(query=jql, limit=max_results)
            
            # Return just the issues array
            if result and "issues" in result:
                logging.info(f"Found {len(result['issues'])} issues")
                return result["issues"]
            
            logging.warning("No issues found in JQL search")
            return []
                
        except HttpUnauthorizedError:
            # Re-raise unauthorized errors
            raise
        except Exception as e:
            # Log and re-raise other errors
            logging.error(f"Error running JQL search: {str(e)}")
            raise JiraFetchError(f"Error running JQL search: {str(e)}")
            
    def get_single_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get a single issue by key and parse it.
        
        Args:
            issue_key: The issue key (e.g., 'PROJ-123')
            
        Returns:
            Parsed issue data or None if not found
            
        Raises:
            JiraFetchError: If there's an error fetching the issue
        """
        if not self.initialize_jira_client():
            logging.error("Cannot get single issue: Jira client initialization failed")
            return None
        
        try:
            logging.info(f"Fetching single issue: {issue_key}")
            
            # Get the issue
            result = self.jira.issue_get(issue_key)
            
            if result:
                # Parse the single issue - wrap in the expected format for parse_issues
                issues_wrapper = {"issues": [result]}
                parsed_issues = self.parse_issues(issues_wrapper)
                
                if parsed_issues:
                    logging.info(f"Successfully fetched and parsed issue: {issue_key}")
                    return parsed_issues[0]  # Return the single parsed issue
                else:
                    logging.warning(f"Issue {issue_key} could not be parsed")
                    return None
            else:
                logging.warning(f"Issue {issue_key} not found")
                return None
                
        except Exception as e:
            error_msg = f"Error fetching issue {issue_key}: {str(e)}"
            logging.error(error_msg)
            raise JiraFetchError(error_msg)
            
    def parse_issues(self, issues: Dict) -> List[dict]:
        """
        Parse issues from Jira response.
        
        Args:
            issues: Dictionary containing Jira issues
            
        Returns:
            List of parsed issues
        """
        # Input validation
        if not issues or not isinstance(issues, dict) or "issues" not in issues:
            logging.error("Invalid input to parse_issues: missing 'issues' key or not a dictionary")
            return []
        
        # Log the number of issues to parse
        issue_count = len(issues["issues"])
        logging.info(f"Parsing {issue_count} issues from Jira response")
        
        if issue_count == 0:
            logging.warning("No issues found to parse")
            return []
        
        # Regex patterns to clean up text
        patterns_to_remove = [  
            r"\[~accountid:[^\]]+\]"
        ]  
        
        # Collect parsed issues
        parsed = []  
        
        for issue_idx, issue in enumerate(issues["issues"]):
            try:
                # Extract basic issue information
                key = issue["key"]
                logging.debug(f"Parsing issue {key} ({issue_idx + 1}/{issue_count})")
                
                summary = issue["fields"]["summary"]
                created = issue["fields"]["created"]
                
                # Get status info
                status = issue["fields"]["status"]["name"]
                
                # Get assignee info (handling missing assignee)
                assignee = "Unassigned"
                if issue["fields"].get("assignee"):
                    assignee = issue["fields"]["assignee"]["displayName"]
                
                # Get priority (handling missing priority)
                priority = "None"
                if issue["fields"].get("priority"):
                    priority = issue["fields"]["priority"]["name"]
                
                # Get issue ID and description
                id = issue["id"]  
                description = issue["fields"].get("description", "")  
                issuetype = issue["fields"]["issuetype"]["name"]
                
                # Get WSJF value for epics
                wsjf = None
                if issuetype.lower() == "epic":
                    # Add epic-specific field extraction here if needed
                    pass
                    
                # Get reporter info
                reporter = issue["fields"]["reporter"]["displayName"]  
                
                # Collect image URLs from attachments
                imgURLs = []
                for attach in issue["fields"].get("attachment", []):
                    if attach.get("mimeType", "").startswith("image/"):
                        imgURLs.append(attach["content"])
                
                # Get parent information (if exists)
                parent = None
                try:
                    if "parent" in issue["fields"]:
                        parent = {
                            "key": issue["fields"]["parent"]["key"],
                            "summary": issue["fields"]["parent"]["fields"]["summary"]
                        }
                except Exception:
                    logging.warning(f"Error parsing parent for issue {key}", exc_info=True)
                
                # Get labels
                labels = issue['fields'].get('labels', [])
                
                # Get fix versions
                fixVersions = [version["name"] for version in issue["fields"].get("fixVersions", [])]
                
                # Parse comments
                comments = []  
                for comment in issue["fields"].get("comment", {}).get("comments", []):
                    comments.append({
                        "author": comment["author"]["displayName"],
                        "body": comment["body"],
                        "created": comment["created"],
                        "updated": comment["updated"]
                    })
                
                # Get components
                components = [component["name"] for component in issue["fields"].get("components", [])]
                
                # Parse issue links
                rel_issues = {}  
                for related_issue in issue["fields"].get("issuelinks", []):
                    relation_type = related_issue["type"]["name"]
                    
                    if "inwardIssue" in related_issue:
                        link_issue = related_issue["inwardIssue"]
                        link_direction = "inward"
                    elif "outwardIssue" in related_issue:
                        link_issue = related_issue["outwardIssue"]
                        link_direction = "outward"
                    else:
                        continue
                        
                    if relation_type not in rel_issues:
                        rel_issues[relation_type] = []
                        
                    rel_issues[relation_type].append({
                        "key": link_issue["key"],
                        "summary": link_issue["fields"]["summary"],
                        "direction": link_direction
                    })
                
                # Clean up description and other text fields using regex patterns
                if description:
                    for pattern in patterns_to_remove:
                        description = re.sub(pattern, "", description)
                
                # Collect all parsed details
                parsed.append({  
                    "key": key,  
                    "summary": summary,  
                    "created": created,  
                    "assignee": assignee,  
                    "priority": priority,
                    "status": status,  
                    "description": description,  
                    "id": id,  
                    "issuetype": issuetype,  
                    "components": components,  
                    "comments": comments,  
                    "related_issues": rel_issues,  
                    "fixVersions": fixVersions, 
                    "reporter": reporter,  
                    "labels": labels,  
                    "wsjf": wsjf,  
                    "imgURLs": imgURLs,  
                    "parent": parent
                })
                
            except Exception as e:
                logging.error(f"Error parsing issue at index {issue_idx}: {str(e)}")
                # Continue with next issue instead of failing
        
        logging.info(f"Successfully parsed {len(parsed)} issues")
        return parsed

    def parse_childs(self, childs: Dict) -> List[dict]:
        """
        Parse child issues into simpler snapshots.
        
        Args:
            childs: Dictionary containing child issues
            
        Returns:
            List of parsed child issues
        """
        if not childs or not isinstance(childs, dict) or "issues" not in childs:
            logging.error("Invalid input to parse_childs: missing 'issues' key or not a dictionary")
            return []
            
        parsed = []  
        for child in childs["issues"]:
            try:
                key = child["key"]
                summary = child["fields"]["summary"]
                description = child["fields"].get("description", "")
                
                parsed.append({
                    "key": key, 
                    "summary": summary, 
                    "description": description
                })
            except Exception as e:
                logging.error(f"Error parsing child issue: {str(e)}")
                
        return parsed

    def parse_projects(self, projects: List[dict]) -> List[dict]:
        """
        Parse projects into simpler snapshots.
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            List of parsed projects
        """
        if not projects or not isinstance(projects, list):
            logging.error("Invalid input to parse_projects: not a list")
            return []
            
        parsed = []
        for project in projects:
            try:
                id = project["id"]
                key = project["key"]
                name = project["name"]
                type = project["projectTypeKey"]
                style = project["style"]
                
                parsed.append({
                    "id": id,
                    "key": key,
                    "name": name,
                    "type": type,
                    "style": style
                })
            except Exception as e:
                logging.error(f"Error parsing project: {str(e)}")
                
        return parsed

    # execute jql and return up to the max results
    def search_new(self, query: str, max_results: int = 10) -> list:
        """
        Execute JQL and return up to the max results using pagination.
        
        Args:
            query: JQL query string
            max_results: Maximum number of results to return per page
            
        Returns:
            List of all issues
        """
        all_issues = []  
        start_at = 0  
        
        # Initialize JIRA client if needed
        if not self.initialize_jira_client():
            logging.error("Failed to initialize Jira client")
            return []
        
        try:
            while True:  
                # Execute JQL with pagination
                logging.info(f"Fetching issues with startAt={start_at}, max_results={max_results}")
                response = self.jira.jql(query=query, limit=max_results, startAt=start_at)  
                
                issues = response.get('issues', [])
                total = response.get('total', 0)
                batch_max_results = response.get('maxResults', max_results)
                
                # Log pagination progress
                logging.info(f"Fetched {len(issues)} issues (total: {total})")
        
                # Append the issues from the current batch to the all_issues list  
                all_issues.extend(issues)  
        
                # Calculate the next starting index for the query  
                start_at += batch_max_results  
        
                # If the number of issues fetched so far is equal to or greater than the total, stop fetching  
                if start_at >= total or not issues:
                    logging.info(f"Pagination complete. Retrieved {len(all_issues)} issues total.")
                    break  
                
            return all_issues
            
        except Exception as e:
            logging.error(f"Error in search_new: {str(e)}")
            return all_issues  # Return any issues collected so far

    def search(self, query: str, max_results: int = 10) -> Dict:
        """
        Execute JQL and return the raw result.
        
        Args:
            query: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results
            
        Raises:
            HttpUnauthorizedError: If authentication fails
            JiraFetchError: For other API errors
        """
        try:
            logging.info(f"Executing Jira JQL query: {query}")
            logging.info(f"Maximum results requested: {max_results}")
            
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                raise JiraFetchError("Failed to initialize Jira client")
                
            logging.info(f"Jira API URL: {self.jira_instance_url}")
            
            # Detailed debug logging before the actual call
            logging.debug("About to call JIRA API with the following parameters:")
            logging.debug(f"- JQL Query: {query}")
            logging.debug(f"- Max Results: {max_results}")
            logging.debug(f"- Username: {self.jira_username}")
            logging.debug(f"- URL: {self.jira_instance_url}")
            
            # Execute the JQL query
            issues = self.jira.jql(query=query, limit=max_results)  
            
            # Log the number of issues found
            if issues and "issues" in issues:
                logging.info(f"Found {len(issues['issues'])} issues out of {issues.get('total', 'unknown')} total")
            else:
                logging.warning("No issues found or unexpected response format")
            
            return issues
            
        except Exception as e:
            logging.error(f"JIRA search exception: {str(e)}", exc_info=True)  # Include complete stack trace
            logging.error(f"Error executing Jira JQL query: {str(e)}")
            
            if "401" in str(e):
                raise HttpUnauthorizedError("Authentication failed when executing JQL query")
            else:
                raise JiraFetchError(f"Error executing JQL query: {str(e)}")

    def search_oldest(self, query: str) -> str:
        """
        Search which executes JQL and attempts to parse all results then format as output.
        
        Args:
            query: JQL query string
            
        Returns:
            String representation of parsed issues
        """
        try:
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                return "Failed to initialize Jira client"
            
            issues = self.jira.jql(query=query)
            parsed_issues = self.parse_issues(issues)
            parsed_issues_str = (
                "Found " + str(len(parsed_issues)) + " issues:\n" + str(parsed_issues)
            )
            return parsed_issues_str
        except Exception as e:
            logging.error(f"Error in search_oldest: {str(e)}")
            return f"Error: {str(e)}"

    def project(self) -> str:
        """
        Get all projects and parse them.
        
        Returns:
            String representation of parsed projects
        """
        try:
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                return "Failed to initialize Jira client"
            
            projects = self.jira.projects()
            parsed_projects = self.parse_projects(projects)
            parsed_projects_str = (
                "Found " + str(len(parsed_projects)) + " projects:\n" + str(parsed_projects)
            )
            return parsed_projects_str
        except Exception as e:
            logging.error(f"Error in project: {str(e)}")
            return f"Error: {str(e)}"
    
    # create Jira issue
    def issue_create(self, query: str) -> Dict[str, Any]:
        """
        Create a Jira issue.
        
        Args:
            query: JSON string with issue fields
            
        Returns:
            Created issue data
            
        Raises:
            JsonDecodeError: If query is not valid JSON
            HttpUnauthorizedError: If authentication fails
            JiraFetchError: For other API errors
        """
        try:
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                raise JiraFetchError("Failed to initialize Jira client")
                
            # Parse the JSON query
            try:
                params = json.loads(query)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in issue_create: {str(e)}")
                raise
                
            # Create the issue
            result = self.jira.issue_create(fields=dict(params))
            logging.info(f"Successfully created issue: {result.get('key', 'unknown')}")
            return result
            
        except HttpUnauthorizedError:
            raise
        except json.JSONDecodeError:
            raise
        except Exception as e:
            logging.error(f"Error creating issue: {str(e)}")
            raise JiraFetchError(f"Error creating issue: {str(e)}")

    def get_issues_from_jql(self, jql: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get issues from JQL query and parse them.
        
        Args:
            jql: The JQL query to run
            max_results: Maximum number of results to return
            
        Returns:
            List of parsed issues
        """
        try:
            logging.info(f"Getting issues with JQL: {jql}")
            
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                raise JiraFetchError("Failed to initialize Jira client")
            
            # Execute the JQL query using custom client
            result = self.jira.jql(query=jql, limit=max_results)
            
            # Return just the issues array
            if result and "issues" in result:
                logging.info(f"Found {len(result['issues'])} issues")
                return result["issues"]
            
            logging.warning("No issues found in JQL query")
            return []
                
        except HttpUnauthorizedError:
            # Re-raise unauthorized errors
            raise
        except Exception as e:
            # Log and re-raise other errors
            logging.error(f"Error getting issues from JQL: {str(e)}")
            raise JiraFetchError(f"Error getting issues from JQL: {str(e)}")
            
    def other(self, query: str) -> Dict[str, Any]:
        """
        Execute alternative Jira API functions.
        
        Args:
            query: JSON string with function name and parameters
            
        Returns:
            Result of the API call
        """
        try:
            # Initialize JIRA client if needed
            if not self.initialize_jira_client():
                return {"error": "Failed to initialize Jira client"}
                
            # Parse the JSON query
            try:
                params = json.loads(query)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in other: {str(e)}")
                return {"error": f"Invalid JSON: {str(e)}"}
                
            # Get the function from the Jira client
            func_name = params.get("function")
            if not func_name:
                return {"error": "No function specified"}
                
            jira_function = getattr(self.jira, func_name, None)
            if not jira_function:
                return {"error": f"Function '{func_name}' not found in Jira client"}
                
            # Call the function with the provided arguments
            return jira_function(*params.get("args", []), **params.get("kwargs", {}))
            
        except Exception as e:
            logging.error(f"Error in other: {str(e)}")
            return {"error": str(e)}

    def run(self, mode: str, query: str) -> Any:
        """
        Run the Jira wrapper with the specified mode and query.
        
        Args:
            mode: Operation mode (jql, get_projects, create_issue, other)
            query: Query string
            
        Returns:
            Result of the operation
        """
        try:
            if mode == "jql":
                return self.search(query)
            elif mode == "get_projects":
                return self.project()
            elif mode == "create_issue":
                return self.issue_create(query)
            elif mode == "other":
                return self.other(query)
            else:
                error_msg = f"Unsupported mode: {mode}"
                logging.error(error_msg)
                return {"error": error_msg}
        except Exception as e:
            logging.error(f"Error in run: {str(e)}")
            return {"error": str(e)}
