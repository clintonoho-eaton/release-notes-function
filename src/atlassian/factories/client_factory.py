"""
Client factories for Atlassian products.
"""
import logging
import os
from typing import Any, Dict, Optional, Union

from ..jira_client import JiraAPIWrapper
from ..confluence_api_wrapper import ConfluenceAPIWrapper
from ..confluence_client import ConfluenceClient

class ClientFactory:
    """Base class for client factories."""
    
    @classmethod
    def create(cls, config: Dict[str, Any]) -> Any:
        """Create a client instance."""
        raise NotImplementedError("Subclasses must implement create()")
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate configuration for client creation.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dict of missing configuration items and their descriptions
        """
        raise NotImplementedError("Subclasses must implement validate_config()")


class JiraClientFactory(ClientFactory):
    """Factory for creating Jira clients."""
    
    @classmethod
    def create(cls, config: Dict[str, Any]) -> Optional[JiraAPIWrapper]:
        """
        Create a JiraAPIWrapper instance.
        
        Args:
            config: Configuration dictionary with Jira settings
            
        Returns:
            JiraAPIWrapper instance or None if validation fails
        """
        # Check for ATLASSIAN_API_KEY in env if jira_api_key is not in config
        if not config.get('jira_api_key') and os.environ.get('ATLASSIAN_API_KEY'):
            logging.debug("Using ATLASSIAN_API_KEY from environment for Jira authentication")
            config['jira_api_key'] = os.environ.get('ATLASSIAN_API_KEY')
            
        missing_configs = cls.validate_config(config)
        if missing_configs:
            for key, message in missing_configs.items():
                logging.error(f"{message}: {key}")
            return None
        
        try:
            return JiraAPIWrapper(
                username=config['jira_username'],
                api_key=config['jira_api_key'],
                base_url=config['jira_url']
            )
        except Exception as e:
            logging.error(f"Error creating JiraAPIWrapper: {str(e)}")
            return None
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate Jira configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dict of missing configuration items and their descriptions
        """
        missing = {}
        required_configs = {
            'jira_username': 'Missing Jira username',
            'jira_url': 'Missing Jira URL',
            'jql': 'Missing JQL query'
        }
        
        # Check for API key in config or environment
        if not config.get('jira_api_key') and not os.environ.get('ATLASSIAN_API_KEY'):
            missing['jira_api_key'] = 'Missing Jira API key (Check ATLASSIAN_API_KEY env var)'
        
        for key, message in required_configs.items():
            if not config.get(key):
                missing[key] = message
        
        return missing


class ConfluenceClientFactory(ClientFactory):
    """Factory for creating Confluence clients."""
    
    @classmethod
    def create(cls, config: Dict[str, Any]) -> Optional[Union[ConfluenceClient, ConfluenceAPIWrapper]]:
        """
        Create a Confluence client instance.
        
        Args:
            config: Configuration dictionary with Confluence settings
            
        Returns:
            ConfluenceClient or ConfluenceAPIWrapper instance or None if validation fails
        """
        import traceback
        
        # Check for ATLASSIAN_API_KEY in env if confluence_api_key is not in config
        if not config.get('confluence_api_key') and os.environ.get('ATLASSIAN_API_KEY'):
            logging.debug("Using ATLASSIAN_API_KEY from environment for Confluence authentication")
            config['confluence_api_key'] = os.environ.get('ATLASSIAN_API_KEY')
        
        # Debug log all relevant config keys
        logging.debug(f"Confluence configuration keys: {list(k for k in config.keys() if 'confluence' in k or 'jira' in k)}")
        
        missing_configs = cls.validate_config(config)
        if missing_configs:
            for key, message in missing_configs.items():
                logging.error(f"{message}: {key}")
            if 'confluence_api_key' in missing_configs:
                logging.error("Missing Confluence configuration: confluence_api_token")
                logging.error("Please ensure ATLASSIAN_API_KEY or CONFLUENCE_API_TOKEN environment variable is set or confluence_api_key is provided in configuration")
                logging.debug(f"Environment has ATLASSIAN_API_KEY: {'Yes' if os.environ.get('ATLASSIAN_API_KEY') else 'No'}")
                logging.debug(f"Environment has CONFLUENCE_API_TOKEN: {'Yes' if os.environ.get('CONFLUENCE_API_TOKEN') else 'No'}")
            return None
        
        try:
            # Use consistent key naming, but fall back to alternate keys
            username = config.get('confluence_username') or config.get('jira_username') or os.environ.get('ATLASSIAN_USERNAME')
            api_key = config.get('confluence_api_key') or config.get('jira_api_key') or os.environ.get('ATLASSIAN_API_KEY')
            
            # For base URL, check multiple possible configurations
            base_url = (config.get('confluence_url') or 
                        config.get('confluence_base_url') or 
                        config.get('jira_instance_url') or
                        os.environ.get('ATLASSIAN_URL') or
                        os.environ.get('CONFLUENCE_URL'))
                        
            space_key = config.get('confluence_space') or config.get('confluence_space_key') or os.environ.get('CONFLUENCE_SPACE')
            
            # Log the configuration being used
            logging.info(f"Creating Confluence client with URL: {base_url}")
            logging.debug(f"Confluence configuration: username={username}, space={space_key}")
            
            if not base_url:
                logging.error("No Confluence URL found in configuration. Cannot create client.")
                return None
            
            if not api_key:
                logging.error("No Confluence API key found in configuration. Cannot create client.")
                logging.error("Please check your configuration for confluence_api_key or jira_api_key")
                return None
                
            # First try to create a ConfluenceClient
            try:
                client = ConfluenceClient(
                    instance_url=base_url,
                    username=username,
                    api_token=api_key
                )
                logging.info("Successfully created ConfluenceClient")
                
                # Test the connection if possible
                try:
                    if space_key:
                        logging.debug(f"Testing Confluence connection with space: {space_key}")
                        client.get_space(space_key)
                        logging.info(f"Successfully connected to Confluence space: {space_key}")
                except Exception as test_e:
                    logging.warning(f"Confluence connection test failed: {str(test_e)}")
                    # Continue despite the test failure
                    
                return client
            except Exception as e:
                logging.warning(f"Failed to create ConfluenceClient, falling back to ConfluenceAPIWrapper: {str(e)}")
                logging.warning(f"Traceback: {traceback.format_exc()}")
                
                wrapper = ConfluenceAPIWrapper(
                    confluence_username=username,
                    confluence_api_token=api_key,
                    confluence_instance_url=base_url
                )
                logging.info("Successfully created ConfluenceAPIWrapper")
                return wrapper
                
        except Exception as e:
            logging.error(f"Error creating Confluence client: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate Confluence configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dict of missing configuration items and their descriptions
        """
        missing = {}
        
        # Check username (confluence_username or jira_username or env var)
        if (not config.get('confluence_username') and 
            not config.get('jira_username') and 
            not os.environ.get('ATLASSIAN_USERNAME')):
            missing['confluence_username'] = 'Missing Confluence username (Check ATLASSIAN_USERNAME env var)'
        
        # Check API key (confluence_api_key, jira_api_key or env var)
        if (not config.get('confluence_api_key') and 
            not config.get('jira_api_key') and 
            not os.environ.get('ATLASSIAN_API_KEY')):
            missing['confluence_api_key'] = 'Missing Confluence API key (Check ATLASSIAN_API_KEY env var)'
        
        # Check URL (confluence_url, confluence_base_url, jira_instance_url or env var)
        if (not config.get('confluence_url') and 
            not config.get('confluence_base_url') and 
            not config.get('jira_instance_url') and
            not os.environ.get('ATLASSIAN_URL') and
            not os.environ.get('CONFLUENCE_URL')):
            missing['confluence_url'] = 'Missing Confluence URL (Check ATLASSIAN_URL env var)'
        
        # Check space key (confluence_space or confluence_space_key or env var)
        if (not config.get('confluence_space') and 
            not config.get('confluence_space_key') and
            not os.environ.get('CONFLUENCE_SPACE')):
            missing['confluence_space'] = 'Missing Confluence space key (Check CONFLUENCE_SPACE env var)'
        
        # Log the validation results
        if missing:
            logging.warning(f"Confluence configuration validation failed with {len(missing)} issues")
            for key, message in missing.items():
                logging.debug(f"Validation issue: {message}")
        else:
            logging.debug("Confluence configuration validation passed")
            
        return missing
