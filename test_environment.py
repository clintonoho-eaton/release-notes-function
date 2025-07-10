#!/usr/bin/env python3
"""
Simple test to check environment detection logic
"""
import os

def test_environment_detection():
    """Test the environment detection logic"""
    print("Environment Detection Test")
    print("=" * 30)
    
    # Check various environment variables
    env_vars = [
        "WEBSITE_SITE_NAME",
        "AZURE_FUNCTIONS_ENVIRONMENT", 
        "FUNCTIONS_WORKER_RUNTIME",
        "AzureWebJobsStorage",
        "ATLASSIAN_USERNAME",
        "ATLASSIAN_API_KEY",
        "CONFLUENCE_SPACE"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        print(f"{var}: {'SET' if value else 'NOT SET'}")
        if value and not var.startswith('ATLASSIAN') and not var.startswith('CONFLUENCE'):
            print(f"  Value: {value}")
    
    # Test our detection logic
    is_local_dev_website = not os.getenv("WEBSITE_SITE_NAME")
    is_local_dev_azure_env = not os.getenv("AZURE_FUNCTIONS_ENVIRONMENT")
    
    print(f"\nDetection Results:")
    print(f"Local Dev (WEBSITE_SITE_NAME method): {is_local_dev_website}")
    print(f"Local Dev (AZURE_FUNCTIONS_ENVIRONMENT method): {is_local_dev_azure_env}")
    
    print(f"\nRecommended detection: {is_local_dev_website}")

if __name__ == "__main__":
    test_environment_detection()
