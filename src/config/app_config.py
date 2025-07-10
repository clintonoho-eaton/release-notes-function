"""Configuration management for the Jira Enrichment application."""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from src.exceptions.api_exceptions import ConfigurationError

class Config:
    """Configuration manager for the application."""
    
    # Default configuration values
    # Maximum number of Jira issues to process - adjust this value as needed
    DEFAULT_MAX_RESULTS = 2
    
    # Required environment variables for the application
    # Format: [list of alternative variable names that can satisfy each requirement]
    REQUIRED_ENV_VARS_ALTERNATIVES = [
        ['AZURE_OPENAI_KEY'],
        ['AZURE_OPENAI_CHAT_COMPLETIONS_API_VERSION'],
        ['AZURE_OPENAI_GPT_DEPLOYMENT'],
        ['AZURE_OPENAI_ENDPOINT'],
        ['ATLASSIAN_URL', 'ATLASSIAN_INSTANCE_URL', 'CONFLUENCE_URL'],
        ['ATLASSIAN_USERNAME'],
        ['ATLASSIAN_API_KEY'],
    ]
    
    # For backward compatibility
    REQUIRED_ENV_VARS = [
        'AZURE_OPENAI_KEY',
        'AZURE_OPENAI_CHAT_COMPLETIONS_API_VERSION',
        'AZURE_OPENAI_GPT_DEPLOYMENT',
        'AZURE_OPENAI_ENDPOINT',
        'ATLASSIAN_URL',
        'ATLASSIAN_USERNAME',
        'ATLASSIAN_API_KEY',
    ]
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Detect Azure Functions environment
        is_azure_functions = "FUNCTIONS_WORKER_RUNTIME" in os.environ
        
        if is_azure_functions:
            logging.info("Running in Azure Functions environment, using system environment variables")
            # Azure Functions environment variables are already loaded
            # No need to load from .env file
        else:
            # Running locally, try to load from .env file
            loaded = False
            
            # Check if local.settings.json exists in project root and extract values
            local_settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'local.settings.json')
            if os.path.exists(local_settings_path):
                try:
                    import json
                    with open(local_settings_path, 'r') as f:
                        settings = json.load(f)
                        
                    # Extract Values section from local.settings.json
                    if 'Values' in settings:
                        for key, value in settings['Values'].items():
                            # Don't override existing environment variables
                            if key not in os.environ:
                                os.environ[key] = value
                                logging.info(f"Loaded setting {key} from local.settings.json")
                        loaded = True
                        logging.info(f"Successfully loaded environment from {local_settings_path}")
                except Exception as e:
                    logging.error(f"Error loading local.settings.json: {str(e)}")
            
            if not loaded:
                # Try multiple potential locations for the .env file
                # First try: Project root (two levels up from config dir)
                root_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
                loaded = load_dotenv(dotenv_path=root_path, override=True)
                
                if loaded:
                    logging.info(f"Successfully loaded environment from {root_path}")
                else:
                    # Second try: One level up (src directory)
                    src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
                    loaded = load_dotenv(dotenv_path=src_path, override=True)
                    
                    if loaded:
                        logging.info(f"Successfully loaded environment from {src_path}")
                    else:
                        # Third try: Current working directory
                        cwd_path = os.path.join(os.getcwd(), '.env')
                        loaded = load_dotenv(dotenv_path=cwd_path, override=True)
                        
                        if loaded:
                            logging.info(f"Successfully loaded environment from {cwd_path}")
                        else:
                            # Last try: Just .env (relative to current directory)
                            fallback_path = '.env'
                            loaded = load_dotenv(dotenv_path=fallback_path, override=True)
                            
                            if loaded:
                                logging.info(f"Successfully loaded environment from fallback path {fallback_path}")
                            else:
                                logging.warning("Could not find .env file or local.settings.json. Using environment variables only.")
                                logging.info(f"Expected config file locations (in order of preference):")
                                logging.info(f"  1. {local_settings_path}")
                                logging.info(f"  2. {root_path}")
                                logging.info(f"  3. {src_path}")
                                logging.info(f"  4. {cwd_path}")
                                logging.info(f"  5. {os.path.abspath(fallback_path)}")
        
        # Validate required environment variables
        self._validate_env_vars()
    
    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_requirements = []
        
        # Check each requirement group using the alternatives
        for alt_vars in self.REQUIRED_ENV_VARS_ALTERNATIVES:
            # Check if any of the alternatives is set
            if not any(os.getenv(var) for var in alt_vars):
                if len(alt_vars) == 1:
                    missing_requirements.append(alt_vars[0])
                else:
                    missing_requirements.append(f"any of [{', '.join(alt_vars)}]")
        
        if missing_requirements:
            msg = f"Missing required environment variables: {', '.join(missing_requirements)}"
            logging.error(msg)
            
            # Log additional details about what variables are found
            found_vars = []
            for var_name, var_value in os.environ.items():
                if any(req_var in var_name for group in self.REQUIRED_ENV_VARS_ALTERNATIVES for req_var in group):
                    masked_value = "********" if "API_KEY" in var_name else var_value
                    found_vars.append(f"{var_name}={masked_value}")
            
            if found_vars:
                logging.info(f"Found these related environment variables: {', '.join(found_vars)}")
            
            raise ConfigurationError(msg)
    
    def is_production(self) -> bool:
        """Check if the application is running in production mode."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_enricher_config(self, jql: str, issuetype: str, fix_version: str = None) -> Dict[str, Any]:
        """
        Get configuration for the JiraEnricher.
        
        Args:
            jql: JQL query to fetch issues
            issuetype: Type of issue to analyze
            fix_version: Optional fix version to include in config
            
        Returns:
            Dictionary with configuration values
        """
        config = self._get_base_config(jql, issuetype)
        if fix_version:
            config['release_version'] = fix_version
        return config
    
    def get_enricher_config_with_options(self, jql: str, issuetype: str, fix_version: str = None, **options) -> Dict[str, Any]:
        """
        Get configuration for the JiraEnricher with additional options.
        
        Args:
            jql: JQL query to fetch issues
            issuetype: Type of issue to analyze
            fix_version: Optional fix version to include in config
            options: Additional configuration options
            
        Returns:
            Dictionary with configuration values
        """
        config = self._get_base_config(jql, issuetype)
        # Add fix version if provided
        if fix_version:
            config['release_version'] = fix_version
        # Override with custom options
        for key, value in options.items():
            config[key] = value
        return config
    
    def get_enricher_config_with_custom_atlassian(self, jql: str, issuetype: str, atlassian_config: Dict[str, str], fix_version: str = None, **options) -> Dict[str, Any]:
        """
        Get enricher configuration with custom Atlassian configuration provided by user.
        
        Args:
            jql: JQL query to fetch issues
            issuetype: Type of issue to analyze
            atlassian_config: Dictionary containing Atlassian configuration
                - username: Atlassian username
                - api_key: Atlassian API key
                - instance_url: Atlassian instance URL
                - confluence_space: Confluence space key
                - confluence_parent: Confluence parent page ID
            fix_version: Fix version (optional)
            **options: Additional configuration options
            
        Returns:
            Dictionary with configuration values using custom Atlassian settings
        """
        # Get base configuration (which uses Azure OpenAI from environment)
        config = {
            "jql": jql,
            "issue_type": issuetype,
            "max_results": int(options.get("max_results", self.DEFAULT_MAX_RESULTS)),
            
            # Use provided Atlassian configuration instead of environment variables
            "jira_username": atlassian_config.get("username"),
            "jira_api_key": atlassian_config.get("api_key"),
            "jira_url": atlassian_config.get("instance_url"),
            
            # Confluence configuration using the same credentials
            "confluence_username": atlassian_config.get("username"),
            "confluence_api_key": atlassian_config.get("api_key"),
            "confluence_url": atlassian_config.get("instance_url"),
            "confluence_base_url": atlassian_config.get("instance_url"),
            "confluence_space": atlassian_config.get("confluence_space"),
            "confluence_space_key": atlassian_config.get("confluence_space"),
            "confluence_parent": atlassian_config.get("confluence_parent"),
            "confluence_parent_id": atlassian_config.get("confluence_parent"),
            "confluence_parent_page_id": atlassian_config.get("confluence_parent"),
            
            # Azure OpenAI configuration - still from environment variables
            "azure_openai_key": os.getenv("AZURE_OPENAI_KEY"),
            "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "azure_openai_chat_completions_api_version": os.getenv("AZURE_OPENAI_CHAT_COMPLETIONS_API_VERSION"),
            "azure_openai_gpt_deployment": os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
            
            # Async performance configuration
            "max_concurrent_ai_calls": int(os.getenv("MAX_CONCURRENT_AI_CALLS", "5")),
            "ai_batch_size": int(os.getenv("AI_BATCH_SIZE", "10")),
            "azure_openai_max_connections": int(os.getenv("AZURE_OPENAI_MAX_CONNECTIONS", "20")),
            "azure_openai_max_connections_per_host": int(os.getenv("AZURE_OPENAI_MAX_CONNECTIONS_PER_HOST", "10")),
            "azure_openai_request_timeout": int(os.getenv("AZURE_OPENAI_REQUEST_TIMEOUT", "60")),
            
            # Output settings
            "create_local_files": os.getenv("CREATE_LOCAL_FILES", "True").lower() == "true",
            "ssl_verify": os.getenv("SSL_VERIFY", "False").lower() == "true",
            "file_path": os.getenv("OUTPUT_FILE_PATH", "output"),
            
            # Confluence settings
            "create_confluence_pages": os.getenv("CREATE_CONFLUENCE_PAGES", "True").lower() == "true",  # Default to True when using custom config
        }
        
        # Add fix version if provided
        if fix_version:
            config['fix_version'] = fix_version
            config['release_version'] = fix_version
            
        # Override with custom options
        for key, value in options.items():
            config[key] = value
            
        return config
    
    def _get_base_config(self, jql: str, issuetype: str) -> Dict[str, Any]:
        """
        Get base configuration for the JiraEnricher.
        
        Args:
            jql: JQL query to fetch issues
            issuetype: Type of issue to analyze
            
        Returns:
            Dictionary with base configuration values
        """
        # Base configuration settings
        config = {
            "jql": jql,
            "issue_type": issuetype,
            "max_results": int(os.getenv("MAX_RESULTS", self.DEFAULT_MAX_RESULTS)),
            
            # Jira configuration
            "jira_username": os.getenv("ATLASSIAN_USERNAME"),
            "jira_api_key": os.getenv("ATLASSIAN_API_KEY"),
            "jira_url": os.getenv("ATLASSIAN_URL"),
            
            # Confluence configuration - explicitly include confluence_api_key
            "confluence_username": os.getenv("ATLASSIAN_USERNAME"),
            "confluence_api_key": os.getenv("ATLASSIAN_API_KEY"),
            
            # Azure OpenAI configuration
            "azure_openai_key": os.getenv("AZURE_OPENAI_KEY"),
            "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "azure_openai_chat_completions_api_version": os.getenv("AZURE_OPENAI_CHAT_COMPLETIONS_API_VERSION"),
            "azure_openai_gpt_deployment": os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
            
            # Async performance configuration
            "max_concurrent_ai_calls": int(os.getenv("MAX_CONCURRENT_AI_CALLS", "5")),
            "ai_batch_size": int(os.getenv("AI_BATCH_SIZE", "10")),
            "azure_openai_max_connections": int(os.getenv("AZURE_OPENAI_MAX_CONNECTIONS", "20")),
            "azure_openai_max_connections_per_host": int(os.getenv("AZURE_OPENAI_MAX_CONNECTIONS_PER_HOST", "10")),
            "azure_openai_request_timeout": int(os.getenv("AZURE_OPENAI_REQUEST_TIMEOUT", "60")),
            
            # Output settings
            "create_local_files": os.getenv("CREATE_LOCAL_FILES", "True").lower() == "true",
            "ssl_verify": os.getenv("SSL_VERIFY", "False").lower() == "true",
            "file_path": os.getenv("OUTPUT_FILE_PATH", "output"),
            
            # Confluence settings if available
            "create_confluence_pages": os.getenv("CREATE_CONFLUENCE_PAGES", "False").lower() == "true",
            "confluence_space_key": os.getenv("CONFLUENCE_SPACE_KEY") or os.getenv("CONFLUENCE_SPACE"),
            "confluence_space": os.getenv("CONFLUENCE_SPACE") or os.getenv("CONFLUENCE_SPACE_KEY"),  # Add both naming variants
            "confluence_parent_page_id": os.getenv("CONFLUENCE_PARENT_PAGE_ID") or os.getenv("CONFLUENCE_PARENT_ID") or os.getenv("CONFLUENCE_PARENT"),
            "confluence_parent_id": os.getenv("CONFLUENCE_PARENT_ID") or os.getenv("CONFLUENCE_PARENT_PAGE_ID") or os.getenv("CONFLUENCE_PARENT"),  # Add both naming variants
            "confluence_parent": os.getenv("CONFLUENCE_PARENT") or os.getenv("CONFLUENCE_PARENT_ID") or os.getenv("CONFLUENCE_PARENT_PAGE_ID"),  # Direct mapping
            "confluence_base_url": os.getenv("CONFLUENCE_BASE_URL") or os.getenv("ATLASSIAN_URL"),
            "confluence_url": os.getenv("CONFLUENCE_URL") or os.getenv("ATLASSIAN_URL"),
        }
        
        return config
