"""
Service for analyzing Jira issues with AI.
"""
import json
import logging
import os
import time
import asyncio
from typing import Any, Dict, List, Optional, Union
import time
import re

from src.ai.azure_configurator import AzureAIConfigurator
from src.atlassian.factories import ClientContextManager
from src.models.jira_models import JiraIssueAnalysis, JiraBugAnalysis, JiraEpicAnalysis
from src.utils.decorators import async_retry_with_backoff, async_performance_monitor
from src.utils.file_utils import normalize_issue_data, create_file_path, save_issues_to_file
from src.exceptions.api_exceptions import HttpUnauthorizedError, JiraFetchError

class JiraAnalyzerService:
    """Service for analyzing Jira issues using AI."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the analyzer service with configuration."""
        self.config = config
        self.ai_configurator = AzureAIConfigurator(config)
        self.kernel = None
        self.plugin_functions = {}
        self.jira_client = None
        self.confluence_client = None

        # Concurrency control settings
        self.max_concurrent_ai_calls = config.get('max_concurrent_ai_calls', 5)
        self.batch_size = config.get('ai_batch_size', 10)
        self.ai_semaphore = asyncio.Semaphore(self.max_concurrent_ai_calls)

        # Initialize AI services
        self._initialize_ai_services()

    def _initialize_ai_services(self):
        """Initialize AI services and load plugins."""
        try:
            self.kernel = self.ai_configurator.initialize_kernel()
            self.plugin_functions = self.ai_configurator.load_plugins()
        except Exception as e:
            logging.error(f"Failed to initialize AI services: {str(e)}")
            raise

    def _has_meaningful_content(self, issue: Dict[str, Any]) -> bool:
        """
        Check if an issue has meaningful content from the AI enrichment.
        
        Args:
            issue: The issue dictionary
            
        Returns:
            bool: True if the issue has meaningful AI-generated content
        """
        # Check issue type and validate required fields
        issue_key = issue.get('key', 'UNKNOWN')
        issue_type = issue.get('issuetype', '').lower()
        
        # Get the AI analysis fields
        tech_summary = issue.get('technical_summary', '')
        exec_summary = issue.get('executive_summary', '')
        cause = issue.get('cause', '')
        fix = issue.get('fix', '')
        reasoning = issue.get('reasoning', '')
        categories = issue.get('inferredCategories', [])
        
        if issue_type == 'bug':
            # For bugs, check technical and executive summaries
            return bool(tech_summary.strip() and (cause.strip() or fix.strip()))
            
        elif issue_type == 'epic':
            # For epics, check both summaries
            return bool(tech_summary.strip() or exec_summary.strip())
            
        else:
            # For other types, check confidence and reasoning
            return bool(reasoning.strip() and categories)

    @async_retry_with_backoff(
        max_attempts=3,
        initial_backoff=1,
        backoff_multiplier=2,
        retry_exceptions=(ValueError, Exception),
        excluded_exceptions=(HttpUnauthorizedError,),
        logger=logging.getLogger()
    )
    async def analyze_issue_with_ai(
    self,
    issue_data: Dict[str, Any],
    is_type: str = "",
) -> Optional[Union[JiraIssueAnalysis, JiraEpicAnalysis, JiraBugAnalysis]]:
        """Analyze a Jira issue using AI and return typed analysis with concurrency control."""
        async with self.ai_semaphore:
            issue_key = issue_data.get('key', 'UNKNOWN')
        logging.debug(f"Starting AI analysis for {issue_key} (type: {is_type})")
        
        schema_cls = {
            'bug': JiraBugAnalysis,
            'epic': JiraEpicAnalysis,
        }.get(is_type.lower(), JiraIssueAnalysis)

        func = self.plugin_functions.get(
            is_type.lower(),
            self.plugin_functions.get('issue')
        )

        # Create model instance and get schema
        model_instance = schema_cls(**issue_data)
        output_schema = model_instance.model_dump()
        
        # Add prompt parameters
        prompt_params = {
            "issue_type": is_type.lower(),
            "issue_info": json.dumps(issue_data),
            "output_schema": json.dumps(output_schema),
            "json_only": True,
            "response_format": {"type": "json_object"}
        }

        # Get dynamic execution settings based on model
        execution_settings = self._get_dynamic_execution_settings()
        if execution_settings:
            prompt_params.update(execution_settings)

        try:
            logging.debug(f"Invoking AI kernel for {issue_key}")
            result = await self.kernel.invoke(func, **prompt_params)
            
            if not result or not result.value:
                raise ValueError(f"Empty result from AI service for {issue_key}")

            result_str = result.value[0].content

            # Strip Markdown code block wrappers if present
            code_block_match = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", result_str.strip())
            if code_block_match:
                result_str = code_block_match.group(1).strip()

            # Parse JSON so we can fix child_issues if it's a dict
            data = json.loads(result_str)

            # Fix child_issues if it is a dict instead of a list
            if isinstance(data.get("child_issues"), dict):
                data["child_issues"] = [
                    f"{k}: {v}" for k, v in data["child_issues"].items()
                ]

            # Validate using Pydantic
            analysis_result = schema_cls.model_validate_json(json.dumps(data))
            logging.debug(f"AI analysis completed for {issue_key}")
            return analysis_result
            
        except Exception as e:
            logging.error(f"Error during AI analysis for {issue_key}: {str(e)}")
            raise

    async def fetch_and_analyze_single_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Fetch and analyze a single issue by key.
        
        Args:
            issue_key: The issue key (e.g., 'PROJ-123')
            
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        result = {
            "status": "success",
            "issue_key": issue_key,
            "details": [],
            "warnings": [],
            "confluence_pages": {
                "created": [],
                "updated": [],
                "errors": []
            }
        }
        
        try:
            # Initialize Jira client to fetch the issue
            async with ClientContextManager(self.config, "jira") as jira_client:
                self.jira_client = jira_client
                if not self.jira_client:
                    result["status"] = "error"
                    result["message"] = "Failed to initialize Jira client"
                    return result
                
                # Fetch the single issue
                logging.info(f"Fetching single issue: {issue_key}")
                issue = self.jira_client.get_single_issue(issue_key)
                
                if not issue:
                    result["status"] = "error"
                    result["message"] = f"Issue {issue_key} not found or could not be accessed"
                    return result
                
                result["details"].append(f"Successfully fetched issue: {issue_key}")
                logging.info(f"Successfully fetched issue: {issue_key}")
                
                # Process the single issue
                processed_issue = await self._process_single_issue_with_context(issue)
                
                if isinstance(processed_issue, Exception):
                    result["status"] = "error"
                    result["message"] = f"Error processing issue {issue_key}: {str(processed_issue)}"
                    result["warnings"].append(f"Failed to process {issue_key}: {str(processed_issue)}")
                    return result
                
                # Update result with processing details
                result["details"].append(f"Successfully processed issue {issue_key}")
                
                # Save files if configured
                if self.config.get('create_local_files', False):
                    await self._save_issue_files([processed_issue])
                    result["details"].append(f"Saved files for {issue_key}")
            
            # Handle Confluence page creation if configured
            if self.config.get('create_confluence_pages', False):
                if not self._check_confluence_config():
                    result["warnings"].append("Invalid Confluence configuration, skipping page creation")
                else:
                    async with ClientContextManager(self.config, "confluence") as confluence_client:
                        self.confluence_client = confluence_client
                        if not self.confluence_client:
                            result["warnings"].append("Failed to initialize Confluence client, skipping page creation")
                        else:
                            confluence_result = await self._create_confluence_page(processed_issue)
                            
                            if confluence_result and confluence_result.get("status") == "success":
                                action = confluence_result.get('result', 'processed')
                                if action == "created":
                                    result["confluence_pages"]["created"].append({
                                        "issue_key": issue_key,
                                        "page_id": confluence_result.get('page_id'),
                                        "url": confluence_result.get('url'),
                                        "title": confluence_result.get('title'),
                                        "status": "success",
                                        "result": "created"
                                    })
                                elif action == "updated":
                                    result["confluence_pages"]["updated"].append({
                                        "issue_key": issue_key,
                                        "page_id": confluence_result.get('page_id'),
                                        "url": confluence_result.get('url'),
                                        "title": confluence_result.get('title'),
                                        "status": "success",
                                        "result": "updated"
                                    })
                                
                                result["details"].append(f"Confluence page {action} for {issue_key}")
                            else:
                                result["confluence_pages"]["errors"].append({
                                    "issue_key": issue_key,
                                    "status": "error",
                                    "message": confluence_result.get('message', 'Unknown error') if confluence_result else "Failed to create page"
                                })
                                result["warnings"].append(f"Failed to create Confluence page for {issue_key}")
                
                # Add processing time
                processing_time = time.time() - start_time
                result["processing_time"] = round(processing_time, 2)
                result["details"].append(f"Total processing time: {processing_time:.2f} seconds")
                
                return result
                
        except Exception as e:
            logging.error(f"Error in fetch_and_analyze_single_issue: {str(e)}")
            result["status"] = "error"
            result["message"] = str(e)
            return result

    @async_performance_monitor(logger=logging.getLogger())
    async def fetch_and_analyze_issues(self) -> Dict[str, Any]:
        """
        Fetch issues from Jira, analyze them with AI, and save results.
        
        Returns:
            Dict containing processing status and results
        """
        result = {
            "status": "success",
            "processing_time": 0,
            "details": [],
            "warnings": [],
            "issue_count": 0,  # Add issue count field
            "confluence_pages": {
                "created": [],
                "updated": [],
                "errors": []
            }
        }

        try:
            # Log configuration for debugging
            logging.debug(f"Starting fetch_and_analyze_issues with configuration:")
            logging.debug(f"- create_local_files: {self.config.get('create_local_files', True)}")
            logging.debug(f"- create_confluence_pages: {self.config.get('create_confluence_pages', False)}")
            logging.debug(f"- release_version: {self.config.get('release_version', 'unknown')}")
            logging.debug(f"- max_results: {self.config.get('max_results', 10)}")

            # Initialize Jira client and fetch issues
            async with ClientContextManager(self.config, "jira") as jira_client:
                self.jira_client = jira_client
                if not self.jira_client:
                    error_msg = "Failed to initialize Jira client"
                    logging.error(error_msg)
                    result["status"] = "error"
                    result["details"].append(error_msg)
                    return result
                    
                logging.info("Fetching issues from Jira")
                issues, total_issue_count = await self._fetch_issues()
                fetched_count = len(issues)
                logging.info(f"Fetched {fetched_count} issues from Jira")
                result["issue_count"] = total_issue_count  # Use total count, not just fetched
                result["details"].append(f"Found {total_issue_count} total issues, fetched {fetched_count} issues from Jira")

            # Process the issues - with or without Confluence
            if self.config.get('create_confluence_pages', False):
                logging.info("Confluence page creation is enabled")
                
                # Check Confluence configuration
                if not self._check_confluence_config():
                    error_msg = "Invalid Confluence configuration, skipping page creation"
                    logging.error(error_msg)
                    result["warnings"].append(error_msg)
                    # Process without Confluence client
                    await self._process_issues(issues, result)
                else:
                    # Process with Confluence client
                    try:
                        async with ClientContextManager(self.config, "confluence") as confluence_client:
                            if not confluence_client:
                                error_msg = "Failed to initialize Confluence client"
                                logging.error(error_msg)
                                result["warnings"].append(error_msg)
                                # Process without Confluence client
                                await self._process_issues(issues, result)
                            else:
                                logging.info("Successfully initialized Confluence client")
                                self.confluence_client = confluence_client
                                await self._process_issues(issues, result)
                    except Exception as conf_e:
                        error_msg = f"Error initializing Confluence client: {str(conf_e)}"
                        logging.error(error_msg)
                        result["warnings"].append(error_msg)
                        # Process without Confluence client
                        self.confluence_client = None
                        await self._process_issues(issues, result)
            else:
                logging.info("Confluence page creation is disabled")
                await self._process_issues(issues, result)

        except Exception as e:
            import traceback
            error_msg = f"Error in fetch_and_analyze_issues: {str(e)}"
            trace = traceback.format_exc()
            logging.error(error_msg)
            logging.error(f"Traceback: {trace}")
            result["status"] = "error"
            result["details"].append(error_msg)

        return result

    async def _fetch_issues(self) -> tuple:
        """Fetch issues from Jira and return both parsed issues and total count."""
        if not self.jira_client:
            raise RuntimeError("Jira client not initialized")

        try:
            issues_raw = self.jira_client.search(
                self.config['jql'],
                max_results=self.config['max_results']
            )
            parsed_issues = self.jira_client.parse_issues(issues_raw)
            total_count = issues_raw.get('total', len(parsed_issues))
            return parsed_issues, total_count
        except Exception as e:
            logging.error(f"Error fetching issues: {str(e)}")
            raise JiraFetchError(f"Error fetching issues: {str(e)}")

    async def _process_issues(self, issues: List[Dict[str, Any]], result: Dict[str, Any]):
        enriched_issues = [] # added
        """Process fetched issues with AI analysis using concurrent batches."""
        total_issues = len(issues)
        processed_count = 0
        successful_count = 0
        
        logging.info(f"Processing {total_issues} issues with max {self.max_concurrent_ai_calls} concurrent AI calls")
        
        # Process issues in batches to manage memory and rate limits
        for batch_start in range(0, total_issues, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_issues)
            batch = issues[batch_start:batch_end]
            batch_num = (batch_start // self.batch_size) + 1
            total_batches = (total_issues + self.batch_size - 1) // self.batch_size
            
            logging.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} issues)")
            
            # Create tasks for concurrent processing within the batch
            tasks = []
            for issue in batch:
                task = asyncio.create_task(self._process_single_issue_with_context(issue))
                tasks.append(task)
            
            # Wait for all tasks in the batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process batch results
            for i, batch_result in enumerate(batch_results):
                issue = batch[i]
                issue_key = issue.get('key', 'UNKNOWN')
                processed_count += 1
                
                if isinstance(batch_result, Exception):
                    logging.error(f"Error processing issue {issue_key}: {str(batch_result)}")
                    result["warnings"].append(f"Failed to process {issue_key}: {str(batch_result)}")
                elif batch_result:
                    successful_count += 1
                    enriched_issues.append(issue)  # <-- ADD THIS LINE INSIDE THE success CASE #added
                    logging.info(f"Successfully processed issue {issue_key} ({processed_count}/{total_issues})")
                    
                    # Handle file saving and Confluence page creation from the result
                    if batch_result.get('files_saved'):
                        result["details"].append(f"Saved files for {issue_key}")
                    if batch_result.get('confluence_page_created'):
                        confluence_result = batch_result.get('confluence_result', {})
                        if confluence_result.get('result') == 'created':
                            result["confluence_pages"]["created"].append({
                                "issue_key": issue_key,
                                "title": confluence_result.get('page', {}).get('title', 'Unknown'),
                                "url": confluence_result.get('url', 'Unknown URL'),
                                "page_id": confluence_result.get('page', {}).get('id', 'Unknown')
                            })
                        elif confluence_result.get('result') == 'updated':
                            result["confluence_pages"]["updated"].append({
                                "issue_key": issue_key,
                                "title": confluence_result.get('page', {}).get('title', 'Unknown'),
                                "url": confluence_result.get('url', 'Unknown URL'),
                                "page_id": confluence_result.get('page', {}).get('id', 'Unknown')
                            })
                        result["details"].append(f"Confluence page {confluence_result.get('result', 'processed')} for {issue_key}")
                    elif batch_result.get('confluence_failed'):
                        confluence_error = batch_result.get('confluence_error', 'Unknown error')
                        result["confluence_pages"]["errors"].append({
                            "issue_key": issue_key,
                            "error": confluence_error
                        })
                        result["warnings"].append(f"Failed to create Confluence page for {issue_key}: {confluence_error}")
                else:
                    result["warnings"].append(f"No AI analysis results for {issue_key}")
            
            # Add small delay between batches to be gentle on the API
            if batch_end < total_issues:
                await asyncio.sleep(0.5)
        
        logging.info(f"Completed processing: {successful_count}/{total_issues} issues processed successfully")
        result["details"].append(f"Processed {successful_count}/{total_issues} issues successfully")

        result["enriched_issues"] = enriched_issues  # <-- ADD THIS HERE

    async def _process_single_issue_with_context(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single issue with AI analysis and handle file/Confluence operations.
        
        Returns:
            Dict with processing results or None if failed
        """
        issue_key = issue.get('key', 'UNKNOWN')
        issue_type = issue.get('issuetype', 'UNKNOWN')
        
        try:
            logging.debug(f"Starting processing for issue {issue_key} of type {issue_type}")
            
            # Analyze with AI
            analysis_result = await self.analyze_issue_with_ai(issue, is_type=issue_type)
            
            if not analysis_result:
                logging.warning(f"No AI analysis results for issue {issue_key}")
                return None
                
            # Convert pydantic model to dict and update the issue
            analysis_dict = analysis_result.model_dump()
            issue.update(analysis_dict)
            logging.info(f"Successfully analyzed issue {issue_key} with AI")
            
            # Log ticket number specifically for debugging
            ticket_number = analysis_dict.get('ticket_number', '')
            if ticket_number:
                logging.info(f"Found ticket number '{ticket_number}' for issue {issue_key}")
            else:
                logging.debug(f"No ticket number found for issue {issue_key}")
            
            # Log the analysis fields for debugging
            log_fields = {k: v for k, v in analysis_dict.items() 
                        if k in ['technical_summary', 'executive_summary', 'cause', 'fix', 'impact']}
            logging.debug(f"AI analysis for {issue_key}: {log_fields}")
            
            # Check if this issue has meaningful content for Confluence
            has_meaningful = self._has_meaningful_content(issue)
            logging.info(f"Issue {issue_key} meaningful content check: {has_meaningful}")
            if not has_meaningful:
                tech_summary = issue.get('technical_summary', '')
                cause = issue.get('cause', '')
                fix = issue.get('fix', '')
                logging.warning(f"Issue {issue_key} failed meaningful content check - tech_summary: '{tech_summary[:50]}...', cause: '{cause[:50]}...', fix: '{fix[:50]}...'")
            
            result_info = {}
            
            # Save to files if configured
            if self.config.get('create_local_files', True):
                try:
                    logging.debug(f"Saving issue {issue_key} to local files")
                    self._save_to_files(issue)
                    result_info['files_saved'] = True
                except Exception as e:
                    logging.error(f"Error saving files for {issue_key}: {str(e)}")
                    result_info['files_saved'] = False

            # Create Confluence pages if configured
            if self.config.get('create_confluence_pages', False):
                try:
                    logging.debug(f"Creating Confluence page for issue {issue_key}")
                    confluence_result = await self._create_confluence_page(issue)
                    if confluence_result and confluence_result.get('status') == 'success':
                        result_info['confluence_page_created'] = True
                        result_info['confluence_result'] = confluence_result
                    else:
                        result_info['confluence_failed'] = True
                        result_info['confluence_error'] = confluence_result.get('message', 'Unknown error') if confluence_result else 'No result returned'
                except Exception as e:
                    logging.error(f"Error creating Confluence page for {issue_key}: {str(e)}")
                    result_info['confluence_failed'] = True
                    result_info['confluence_error'] = str(e)
            
            return result_info
            
        except Exception as e:
            logging.error(f"Error processing issue {issue_key}: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def add_ai_analysis_to_issue(self, issue: Dict[str, Any]) -> bool:
        """
        Add AI analysis to a single issue with optimized async processing.
        
        Args:
            issue: Issue dictionary to enrich
            
        Returns:
            bool: True if enrichment was successful, False otherwise
        """
        try:
            issue_key = issue.get('key', 'UNKNOWN')
            issue_type = issue.get('issuetype', 'UNKNOWN')
            
            logging.info(f"Adding AI analysis to issue {issue_key} (type: {issue_type})")
            
            # Use the concurrent AI analysis method
            analysis_result = await self.analyze_issue_with_ai(issue, is_type=issue_type)
            
            if analysis_result:
                # Convert pydantic model to dict and update the issue
                analysis_dict = analysis_result.model_dump()
                issue.update(analysis_dict)
                logging.info(f"Successfully added AI analysis to issue {issue_key}")
                return True
            else:
                logging.warning(f"No AI analysis results for issue {issue_key}")
                return False
                
        except Exception as e:
            logging.error(f"Error adding AI analysis to issue {issue.get('key', 'UNKNOWN')}: {str(e)}")
            return False

    def _save_to_files(self, issue: Dict[str, Any]):
        """Save processed issue to files."""
        try:
            file_path = self._get_output_path(issue)
            file_types = self.config.get('file_types_to_save', ['json'])
            
            for file_type in file_types:
                save_issues_to_file([issue], file_path, file_type, issue.get('issuetype', 'Issue'))
                
        except Exception as e:
            logging.error(f"Error saving files for {issue.get('key')}: {str(e)}")
            raise

    def _get_output_path(self, issue: Dict[str, Any]) -> str:
        """Get the output path for saving files."""
        base_path = self.config.get('file_path', 'output')
        issue_type = issue.get('issuetype', 'UNKNOWN')
        version = self.config.get('release_version', 'unknown')
        
        return os.path.join(base_path, issue_type, version)

    async def _create_confluence_page(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a Confluence page for the issue.
        
        Args:
            issue: The issue dictionary
            
        Returns:
            Dict with page creation results or None if failed
        """
        if not self.confluence_client:
            logging.error("Confluence client not initialized")
            return {"status": "error", "message": "Confluence client not initialized"}
            
        try:
            # Check if the issue has meaningful content for a Confluence page
            if not self._has_meaningful_content(issue):
                logging.warning(f"Skipping Confluence page creation for {issue.get('key')}: Issue lacks meaningful content from AI analysis")
                return {"status": "error", "message": "Issue lacks meaningful content from AI analysis"}
                
            # Format title and content
            issue_key = issue.get('key', 'UNKNOWN')
            issue_summary = issue.get('summary', 'No Summary')
            fix_version = self.config.get('release_version', '')
            
            # Add fix version as prefix to the page title if available
            logging.debug(f"Fix version from config: '{fix_version}'")
            if fix_version:
                title = f"{fix_version} - {issue_key} - {issue_summary}"
                logging.info(f"Using title with fix version: {title}")
            else:
                title = f"{issue_key} - {issue_summary}"
                logging.warning(f"No fix version found in config, using title without fix version: {title}")
            
            # Log Confluence configuration
            parent_id_value = (self.config.get('confluence_parent_id') or 
                              self.config.get('confluence_parent_page_id') or 
                              self.config.get('confluence_parent'))
            logging.debug(f"Confluence configuration: space={self.config.get('confluence_space') or self.config.get('confluence_space_key')}, parent_id={parent_id_value}")
            
            # Log ticket number for debugging
            ticket_number = issue.get('ticket_number', '')
            if ticket_number:
                logging.info(f"Including ticket number '{ticket_number}' in Confluence page for {issue_key}")
            else:
                logging.debug(f"No ticket number to include in Confluence page for {issue_key}")
            
            logging.debug(f"Config keys checked for parent_id: confluence_parent_id={self.config.get('confluence_parent_id')}, confluence_parent_page_id={self.config.get('confluence_parent_page_id')}, confluence_parent={self.config.get('confluence_parent')}")
            
            # Create page parameters with all necessary issue data for proper formatting
            page_params = {
                "space": self.config.get('confluence_space') or self.config.get('confluence_space_key'),
                "title": title,
                "key": issue_key,
                "summary": issue_summary,
                "issue_type": issue.get('issuetype', ''),
                "fix_version": self.config.get('release_version', ''),
                "components": issue.get('components', []),
                "labels": issue.get('labels', []),
                "ticket_number": issue.get('ticket_number', ''),  # Add ticket number from AI analysis
                "parent_id": (self.config.get('confluence_parent_id') or 
                             self.config.get('confluence_parent_page_id') or 
                             self.config.get('confluence_parent')),
                
                # Analysis fields that might be present in the issue
                "executive_summary": issue.get('executive_summary', ''),
                "technical_summary": issue.get('technical_summary', ''),
                "cause": issue.get('cause', ''),
                "fix": issue.get('fix', ''),
                "impact": issue.get('impact', ''),
                "reasoning": issue.get('reasoning', ''),
                "inferredCategories": issue.get('inferredCategories', []),
                "confidence": issue.get('confidence', '')
            }
            
            # Validate required parameters
            if not page_params["space"]:
                error_msg = "Confluence space not configured. Check 'confluence_space' or 'confluence_space_key' in configuration."
                logging.error(error_msg)
                return {"status": "error", "message": error_msg}
                
            logging.info(f"Attempting to create Confluence page for {issue_key} in space {page_params['space']}")
            
            # Create or update the page
            result = self.confluence_client.page_create(page_params)
            
            logging.debug(f"Confluence page creation result: {result}")
            
            if result.get("status") == "success":
                action = result.get('result', 'processed')
                url = result.get('url', 'Unknown URL')
                logging.info(f"Successfully {action} Confluence page for {issue_key} with URL: {url}")
                return result
            else:
                error_msg = result.get('message', 'Unknown error')
                logging.error(f"Failed to create/update Confluence page for {issue_key}: {error_msg}")
                return result
                
        except Exception as e:
            error_msg = f"Error creating Confluence page for {issue.get('key')}: {str(e)}"
            logging.error(error_msg)
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": error_msg}

    def _check_confluence_config(self) -> bool:
        """
        Check if the Confluence configuration is valid.
        
        Returns:
            bool: True if the configuration is valid, False otherwise
        """
        required_configs = [
            'confluence_space', 
            'confluence_instance_url', 
            'confluence_username', 
            'confluence_api_token'
        ]
        
        # Allow fallbacks to Jira config
        alternates = {
            'confluence_space': ['confluence_space_key'],
            'confluence_instance_url': ['confluence_url', 'confluence_base_url', 'jira_instance_url'],
            'confluence_username': ['jira_username'],
            'confluence_api_token': ['jira_api_token', 'confluence_api_key']
        }
        
        missing = []
        for config_key in required_configs:
            # Check primary key
            if not self.config.get(config_key):
                # Check alternate keys
                alt_keys = alternates.get(config_key, [])
                if not any(self.config.get(alt) for alt in alt_keys):
                    missing.append(config_key)
        
        if missing:
            logging.error(f"Missing Confluence configuration: {', '.join(missing)}")
            return False
            
        logging.info("Confluence configuration is valid")
        return True

    def _get_dynamic_execution_settings(self) -> Dict[str, Any]:
        """
        Get dynamic execution settings based on the current Azure OpenAI model.
        
        Returns:
            Dict containing model-appropriate execution settings
        """
        deployment = self.config.get("azure_openai_gpt_deployment", "").lower()
        
        # Load external model-specific configurations first
        external_configs = self._load_model_specific_configs()
        
        # Define built-in model-specific configurations as fallback
        builtin_configs = {
            "o4-mini": {
                # o4-mini only supports default parameters
                "max_completion_tokens": 800,
                # No temperature, top_p, presence_penalty, frequency_penalty supported
            },
            "gpt-4": {
                # gpt-4, gpt-4o, and gpt-4.1 all support full parameters
                "max_completion_tokens": 800,
                "temperature": 0.3,
                "top_p": 0.9,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.2
            }
        }
        
        # Try external configurations first
        for model_name, config in external_configs.items():
            if model_name in deployment:
                logging.info(f"Using external execution settings for model: {model_name}")
                return config
        
        # Fall back to built-in configurations
        # Check for o4-mini first (most specific)
        if "o4-mini" in deployment:
            logging.info(f"Using built-in execution settings for model: o4-mini")
            return builtin_configs["o4-mini"]
        
        # Check for any GPT-4 variant (gpt-4, gpt-4o, gpt-4.1, etc.)
        if any(gpt4_variant in deployment for gpt4_variant in ["gpt-4", "gpt4"]):
            logging.info(f"Using built-in execution settings for GPT-4 variant: {deployment}")
            return builtin_configs["gpt-4"]
        
        # Default configuration for unknown models (conservative approach)
        logging.warning(f"Unknown model '{deployment}', using conservative default settings")
        return {
            "max_completion_tokens": 800,
            "temperature": 0.7  # Most models support temperature
        }

    def _load_model_specific_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load model-specific configurations from environment or config.
        This allows for external configuration of model parameters.
        
        Returns:
            Dict mapping model names to their execution settings
        """
        import os
        
        # Check if model-specific config is provided via environment variables or config
        model_configs = {}
        
        # Example: AZURE_OPENAI_O4_MINI_TEMPERATURE=1.0
        # Example: AZURE_OPENAI_GPT4O_TEMPERATURE=0.3
        for key, value in os.environ.items():
            if key.startswith("AZURE_OPENAI_") and "_" in key:
                parts = key.split("_")
                if len(parts) >= 4:
                    # Extract model name and parameter
                    model_part = "_".join(parts[2:-1]).lower().replace("_", "-")
                    param_name = parts[-1].lower()
                    
                    if model_part not in model_configs:
                        model_configs[model_part] = {}
                    
                    # Convert string values to appropriate types
                    try:
                        if param_name in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]:
                            model_configs[model_part][param_name] = float(value)
                        elif param_name in ["max_completion_tokens", "max_tokens"]:
                            model_configs[model_part][param_name] = int(value)
                        else:
                            model_configs[model_part][param_name] = value
                    except ValueError:
                        logging.warning(f"Invalid value for {key}: {value}")
        
        # Also check application config for model-specific settings
        app_model_configs = self.config.get("model_execution_settings", {})
        for model_name, settings in app_model_configs.items():
            if model_name.lower() not in model_configs:
                model_configs[model_name.lower()] = settings
            else:
                # Merge with environment variables taking precedence
                model_configs[model_name.lower()].update(settings)
        
        return model_configs
