#!/usr/bin/env python3
"""
Debug script to test IP-57837 processing and understand why content validation fails.
"""

import asyncio
import json
import logging
import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.config.app_config import Config
from src.atlassian.factories.context_manager import ClientContextManager

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def debug_ip57837():
    """Debug IP-57837 processing."""
    try:
        # Get configuration
        config_object = Config()
        config = config_object.get_enricher_config("", "", "")
        
        # Override for single issue
        config['max_results'] = 1
        config['jql'] = "key = IP-57837"
        
        print(f"Config loaded successfully")
        
        # Test direct issue fetch
        print("\n=== Fetching Issue ===")
        async with ClientContextManager(config, "jira") as jira_client:
            issue = jira_client.get_single_issue("IP-57837")
            if not issue:
                print("ERROR: Could not fetch issue IP-57837")
                return
                
            print(f"Issue Key: {issue.get('key')}")
            print(f"Issue Type: {issue.get('issuetype')}")
            print(f"Summary: {issue.get('summary')}")
            print(f"Description length: {len(issue.get('description', ''))}")
            
            # Print raw issue fields to understand structure
            print("\n=== Raw Issue Fields ===")
            important_fields = ['key', 'issuetype', 'summary', 'description', 'status', 'priority']
            for field in important_fields:
                value = issue.get(field, 'NOT_FOUND')
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {field}: {value[:100]}...")
                else:
                    print(f"  {field}: {value}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ip57837())
