"""
Main entry point for the Azure Functions application.
This file registers all function blueprints and configures the application.
"""
import os
import sys
import json
import time
import logging
import azure.functions as func

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import configuration and security utilities
from src.utils.security_utils import disable_ssl_verification
from src.config.app_config import Config

# Configure logging
def configure_func_logging():
    """Configure logging for Azure Functions environment."""
    # Get the Azure Functions logger
    logger = logging.getLogger()
    
    # Set level based on environment
    is_production = os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT") == "Production"
    logger.setLevel(logging.INFO if is_production else logging.DEBUG)
    
    # Set up handlers if not already configured
    if not logger.handlers:
        # Add stream handler (will be captured by Azure Functions)
        logger.addHandler(logging.StreamHandler())
        
    # Configure specific module loggers
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("semantic_kernel").setLevel(logging.INFO)
    
    logging.info("Function logging configured")
    logging.info(f"Log level: {'INFO' if is_production else 'DEBUG'}")
    logging.debug("Debug logging is enabled")

# Configure logging
configure_func_logging()

# Initialize config
try:
    config_object = Config()
    logging.info("Config initialized")
except Exception as ex:
    logging.error(f"Failed to initialize config: {str(ex)}")
    raise

# Configure SSL
disable_ssl_verification()
logging.info("SSL verification configured")

# Import function blueprints
from functions.release_notes.function import release_notes_bp
from functions.diagnostics.function import diagnostics_bp
from functions.health.function import health_bp
from functions.extensions.function import extensions_bp
from functions.release_notes import function as release_notes_function

# Create the function app
app = func.FunctionApp()


# Register blueprints with the app
app.register_blueprint(release_notes_bp)
app.register_blueprint(diagnostics_bp)
app.register_blueprint(health_bp)
app.register_blueprint(extensions_bp)

# Add a simple test route
@app.route(route="test", methods=["GET"])
def test_route(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test endpoint to verify function app is working."""
    logging.info("Test route called successfully")
    
    response = {
        "status": "ok",
        "message": "Azure Functions app is running correctly",
        "timestamp": time.time(),
        "app_version": "1.0.0"
    }
    
    return func.HttpResponse(json.dumps(response), mimetype="application/json")
