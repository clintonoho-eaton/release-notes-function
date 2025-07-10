"""
Azure OpenAI service configurator with async support.
"""
import logging
from typing import Any, Dict

# Updated imports for SK 1.x with async support
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments

class AzureAIConfigurator:
    """Configure and manage Azure OpenAI services with async support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kernel = None
        
        # Configure concurrent connection limits for better async performance
        self._setup_http_client_config()
    
    def _setup_http_client_config(self) -> None:
        """
        Configure HTTP client settings for optimal async performance.
        Note: These settings are stored for reference but HTTP client configuration
        is handled internally by the semantic-kernel library.
        """
        # Set reasonable defaults for concurrent requests (for reference)
        self.max_connections = self.config.get('azure_openai_max_connections', 20)
        self.max_connections_per_host = self.config.get('azure_openai_max_connections_per_host', 10)
        self.request_timeout = self.config.get('azure_openai_request_timeout', 60)
        
        logging.info(f"HTTP client settings (for reference): max_connections={self.max_connections}, "
                    f"max_per_host={self.max_connections_per_host}, timeout={self.request_timeout}s")
        logging.info("Note: HTTP client configuration is handled internally by semantic-kernel")
    
    def validate_config(self) -> Dict[str, str]:
        """
        Validate Azure OpenAI configuration.
        
        Returns:
            Dict of missing configuration items and their descriptions
        """
        missing = {}
        
        # Required Azure OpenAI configuration keys
        azure_config_keys = [
            "azure_openai_key", 
            "azure_openai_gpt_deployment",
            "azure_openai_endpoint", 
            "azure_openai_chat_completions_api_version"
        ]
        
        for key in azure_config_keys:
            if not self.config.get(key):
                missing[key] = f"Missing required Azure OpenAI configuration: {key}"
        
        return missing
    
    def adjust_config_for_model(self) -> None:
        """
        Adjust configuration parameters based on the specific model being used.
        Each model may have different requirements for API version, parameters, etc.
        """
        deployment = self.config.get("azure_openai_gpt_deployment", "")
        logging.info(f"Adjusting configuration for model: {deployment}")
        
        # Map of model-specific configurations
        model_configs = {
            "o4-mini": {
                "api_version": "2024-12-01-preview",
                "param_mapping": {"max_tokens": "max_completion_tokens"},
                "enforce_params": {"temperature": 1.0},
                "unsupported_params": ["top_p", "presence_penalty", "frequency_penalty"]
            }
            # Add more models here with their specific configurations
        }
        
        # Apply model-specific configuration if available
        if deployment in model_configs:
            model_config = model_configs[deployment]
            
            # Set appropriate API version
            if "api_version" in model_config:
                required_api_version = model_config["api_version"]
                current_api_version = self.config.get("azure_openai_chat_completions_api_version")
                
                if current_api_version != required_api_version:
                    logging.warning(f"Setting correct API version for {deployment} model: {required_api_version}")
                    self.config["azure_openai_chat_completions_api_version"] = required_api_version
                
                logging.info(f"Using API version: {self.config.get('azure_openai_chat_completions_api_version')}")
            
            # Remap parameter names (e.g., max_tokens -> max_completion_tokens)
            if "param_mapping" in model_config:
                for old_param, new_param in model_config["param_mapping"].items():
                    if old_param in self.config:
                        logging.warning(f"Converting {old_param} to {new_param} in config for {deployment} compatibility")
                        self.config[new_param] = self.config.pop(old_param)
                        logging.info(f"Note: Using {new_param} instead of {old_param} for {deployment}")
            
            # Enforce specific parameter values
            if "enforce_params" in model_config:
                for param, value in model_config["enforce_params"].items():
                    if param in self.config and self.config[param] != value:
                        logging.warning(f"Setting {param} to {value} for {deployment} compatibility")
                        self.config[param] = value
                        logging.info(f"Note: {deployment} only supports {param}={value}")
            
            # Remove unsupported parameters
            if "unsupported_params" in model_config:
                for param in model_config["unsupported_params"]:
                    if param in self.config:
                        logging.warning(f"Removing unsupported parameter {param} for {deployment}")
                        self.config.pop(param)
                        
            logging.info(f"Configuration adjusted successfully for {deployment} model")

    def initialize_kernel(self) -> Kernel:
        """Initialize and configure the semantic kernel with Azure OpenAI for async operations."""
        try:
            logging.info("Initializing Azure OpenAI service with async support...")
            
            # Handle model-specific configuration adjustments
            self.adjust_config_for_model()
            
            # Validate required configuration
            missing_configs = self.validate_config()
            if missing_configs:
                error_messages = [f"{message}: {key}" for key, message in missing_configs.items()]
                raise ValueError("\n".join(error_messages))
            
            # Create new kernel
            self.kernel = Kernel()
            
            # Configure Azure OpenAI service without unsupported http_client parameter
            # Note: HTTP client settings are handled internally by the semantic-kernel library
            service = AzureChatCompletion(
                service_id="Chat",
                api_key=self.config["azure_openai_key"],
                deployment_name=self.config["azure_openai_gpt_deployment"],
                endpoint=self.config["azure_openai_endpoint"],
                api_version=self.config["azure_openai_chat_completions_api_version"]
            )
            
            # Add the service to the kernel
            self.kernel.add_service(service)
            logging.info("Azure OpenAI service initialized successfully with async support")
            
            return self.kernel
            
        except Exception as e:
            logging.error(f"Failed to initialize Azure OpenAI service: {str(e)}")
            raise RuntimeError(f"Azure OpenAI initialization failed: {str(e)}")
    
    def load_plugins(self) -> Dict[str, Any]:
        """Load and verify semantic kernel plugins."""
        if not self.kernel:
            raise RuntimeError("Kernel must be initialized before loading plugins")
            
        try:
            logging.info("Loading ReleaseNotes plugins...")
            
            # Updated plugin loading method for SK 1.x
            # When plugin=None and parent_directory is provided, it calls KernelPlugin.from_directory
            release_notes_plugin = self.kernel.add_plugin(
                plugin=None,
                plugin_name="ReleaseNotes",
                parent_directory="./src/plugins/semantic_kernel"
            )
            
            # Verify plugin functions exist
            if "Bug" not in release_notes_plugin:
                raise ValueError("Bug function not found in ReleaseNotes plugin")
            if "Issue" not in release_notes_plugin:
                raise ValueError("Issue function not found in ReleaseNotes plugin") 
            if "Epic" not in release_notes_plugin:
                raise ValueError("Epic function not found in ReleaseNotes plugin")
                
            plugin_functions = {
                "bug": release_notes_plugin["Bug"],
                "issue": release_notes_plugin["Issue"],
                "epic": release_notes_plugin["Epic"]
            }
            
            logging.info("ReleaseNotes plugins loaded successfully")
            return plugin_functions
            
        except Exception as e:
            logging.error(f"Failed to load ReleaseNotes plugins: {str(e)}")
            raise RuntimeError(f"Plugin initialization failed: {str(e)}")
