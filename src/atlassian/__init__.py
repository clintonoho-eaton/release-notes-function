"""
Atlassian integration package.

This package provides functionality for interacting with Atlassian products like Jira and Confluence.
"""

from src.atlassian.base_client import BaseAtlassianClient
from src.atlassian.api_wrapper import AtlassianAPIWrapper
from src.atlassian.jira_client import JiraAPIWrapper, JiraClient
from src.atlassian.confluence_client import ConfluenceClient
from src.atlassian.confluence_api_wrapper import ConfluenceAPIWrapper
from src.atlassian.jira_issue_ai_analyzer import JiraEnricher

__all__ = [
    "BaseAtlassianClient",
    "AtlassianAPIWrapper",
    "JiraAPIWrapper",
    "JiraClient", 
    "ConfluenceClient",
    "ConfluenceAPIWrapper",
    "JiraEnricher"
]
