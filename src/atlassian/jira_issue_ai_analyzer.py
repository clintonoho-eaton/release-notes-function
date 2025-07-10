"""
Main module for analyzing Jira issues with AI enrichment.
"""
from typing import Dict, Any, Optional, Union
from src.models.jira_models import JiraIssueAnalysis, JiraBugAnalysis, JiraEpicAnalysis
from src.services import JiraAnalyzerService

class JiraEnricher:
    """
    Enrich Jira issues by fetching them via Jira API, analyzing with Azure OpenAI, and saving results.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the Jira enricher.
        
        Args:
            config: Configuration dictionary
        """
        self.analyzer_service = JiraAnalyzerService(config)

    async def fetch_and_analyze_issues(self) -> Dict[str, Any]:
        """
        Fetch issues from Jira, enrich them with AI analysis, and save results.
        
        Returns:
            Dict containing processing status and results
        """
        return await self.analyzer_service.fetch_and_analyze_issues()

    async def fetch_and_analyze_single_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Fetch and analyze a single issue by key.
        
        Args:
            issue_key: The issue key (e.g., 'PROJ-123')
        
        Returns:
            Dict containing processing status and results
        """
        return await self.analyzer_service.fetch_and_analyze_single_issue(issue_key)

    async def analyze_issue_with_ai(
        self,
        issue_data: Dict[str, Any],
        is_type: str = "",
    ) -> Optional[Union[JiraIssueAnalysis, JiraEpicAnalysis, JiraBugAnalysis]]:
        """
        Analyze a single issue with AI.
        
        Args:
            issue_data: Issue data dictionary
            is_type: Type of issue (bug, epic, etc.)
            
        Returns:
            Analyzed issue data
        """
        return await self.analyzer_service.analyze_issue_with_ai(issue_data, is_type)

    async def add_ai_analysis_to_issue(self, issue: Dict[str, Any]) -> bool:
        """
        Add AI analysis to a single issue.
        
        Args:
            issue: Issue dictionary to enrich
            
        Returns:
            bool: True if enrichment was successful, False otherwise
        """
        return await self.analyzer_service.add_ai_analysis_to_issue(issue)