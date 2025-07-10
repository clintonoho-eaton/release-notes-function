#!/usr/bin/env python3
"""
Test script to debug the custom API endpoint with the specific JQL.
"""

import json
import requests
import time

def test_custom_api():
    """Test the custom API endpoint with the user's JQL."""
    print("🔍 Testing Custom API with user's JQL...")
    
    # Base URL for local development
    base_url = "http://localhost:7071/api/release-notes/custom"
    
    # Test data with the user's JQL
    test_data = {
        "jql": "project = IP AND fixversion = \"PI08-2025-01\" AND issuetype = Bug",
        "issue_type": "Bug",
        "max_results": 10
        # No atlassian_config provided - should fall back to local.settings.json
    }
    
    print(f"📡 Making POST request to: {base_url}")
    print(f"📋 Request body: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(
            base_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"📝 Response Body: {json.dumps(response_json, indent=2)}")
            
            # Check if we got issue count information
            if response.status_code == 200:
                print("✅ Request successful!")
                if "issue_count" in response_json:
                    print(f"📊 Issues returned: {response_json['issue_count']}")
                else:
                    print("⚠️  Issue count not found in response")
            else:
                print(f"❌ Request failed with status {response.status_code}")
                
        except json.JSONDecodeError:
            print(f"📄 Raw Response Body: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        
    print("-" * 60)

def test_single_api():
    """Test the single issue API for comparison."""
    print("🔍 Testing Single API for comparison...")
    
    # Base URL for local development  
    base_url = "http://localhost:7071/api/release-notes/single"
    
    # Test data with a single issue
    test_data = {
        "issue_key": "IP-51180"
        # No atlassian_config provided - should fall back to local.settings.json
    }
    
    print(f"📡 Making POST request to: {base_url}")
    print(f"📋 Request body: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(
            base_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"📝 Response Body: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Single API working correctly!")
            else:
                print(f"❌ Single API failed with status {response.status_code}")
                
        except json.JSONDecodeError:
            print(f"📄 Raw Response Body: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting API debug tests...")
    print("=" * 60)
    
    # Test both APIs
    test_custom_api()
    test_single_api()
    
    print("🏁 Debug tests completed!")
