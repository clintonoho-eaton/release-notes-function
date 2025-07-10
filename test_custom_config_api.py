"""
Test script for the new custom configuration API endpoints.
This script demonstrates how to use the new API endpoints with custom Atlassian configuration.
"""

import json
import requests
import os
from typing import Dict, Any

# Configuration for testing
API_BASE_URL = "http://localhost:7071/api"  # Local development URL
# For production, use: "https://your-function-app.azurewebsites.net/api"

def test_custom_config_batch_endpoint():
    """Test the custom configuration batch processing endpoint."""
    
    # Example configuration - replace with your actual values
    test_payload = {
        "jql": "project = IP AND fixversion = 'Test Version' AND issuetype = Bug",
        "issue_type": "Bug",
        "max_results": 5,
        "atlassian_config": {
            "username": "your-email@company.com",
            "api_key": "your-atlassian-api-key-here",
            "instance_url": "https://your-company.atlassian.net",
            "confluence_space": "TESTSPACE",
            "confluence_parent": "123456789"
        }
    }
    
    print("Testing Custom Configuration Batch Endpoint")
    print("=" * 50)
    print(f"URL: {API_BASE_URL}/release-notes/custom")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/release-notes/custom",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED - Batch endpoint working correctly")
        else:
            print("❌ Test FAILED - Check error message above")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test FAILED - Request error: {e}")
    except json.JSONDecodeError:
        print(f"❌ Test FAILED - Invalid JSON response: {response.text}")
    
    print("\n" + "=" * 50 + "\n")

def test_custom_config_single_endpoint():
    """Test the custom configuration single issue processing endpoint."""
    
    # Example configuration - replace with your actual values
    test_payload = {
        "issue_key": "IP-12345",  # Replace with a real issue key
        "atlassian_config": {
            "username": "your-email@company.com",
            "api_key": "your-atlassian-api-key-here",
            "instance_url": "https://your-company.atlassian.net",
            "confluence_space": "TESTSPACE",
            "confluence_parent": "123456789"
        }
    }
    
    print("Testing Custom Configuration Single Issue Endpoint")
    print("=" * 50)
    print(f"URL: {API_BASE_URL}/release-notes/single")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/release-notes/single",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED - Single issue endpoint working correctly")
        else:
            print("❌ Test FAILED - Check error message above")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test FAILED - Request error: {e}")
    except json.JSONDecodeError:
        print(f"❌ Test FAILED - Invalid JSON response: {response.text}")
    
    print("\n" + "=" * 50 + "\n")

def test_validation_errors():
    """Test validation error handling."""
    
    print("Testing Validation Error Handling")
    print("=" * 50)
    
    # Test missing required fields
    invalid_payloads = [
        {
            "name": "Missing JQL",
            "payload": {
                "issue_type": "Bug",
                "atlassian_config": {
                    "username": "test@example.com",
                    "api_key": "test-key",
                    "instance_url": "https://test.atlassian.net",
                    "confluence_space": "TEST",
                    "confluence_parent": "123"
                }
            }
        },
        {
            "name": "Missing Atlassian Config",
            "payload": {
                "jql": "project = TEST",
                "issue_type": "Bug"
            }
        },
        {
            "name": "Incomplete Atlassian Config",
            "payload": {
                "jql": "project = TEST",
                "issue_type": "Bug",
                "atlassian_config": {
                    "username": "test@example.com"
                    # Missing other required fields
                }
            }
        }
    ]
    
    for test_case in invalid_payloads:
        print(f"Testing: {test_case['name']}")
        try:
            response = requests.post(
                f"{API_BASE_URL}/release-notes/custom",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 400:
                print(f"  ✅ Validation working correctly")
            else:
                print(f"  ❌ Expected 400, got {response.status_code}")
                
            response_data = response.json()
            print(f"  Message: {response_data.get('message', 'No message')}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    print("=" * 50 + "\n")

def test_local_development_fallback():
    """Test the local development fallback to environment variables."""
    
    # Example request without atlassian_config - should use local.settings.json
    test_payload = {
        "jql": "project = IP AND fixversion = 'Test Version' AND issuetype = Bug",
        "issue_type": "Bug",
        "max_results": 5
        # No atlassian_config - should fall back to environment variables
    }
    
    print("Testing Local Development Fallback (No atlassian_config)")
    print("=" * 50)
    print(f"URL: {API_BASE_URL}/release-notes/custom")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print("Note: This should use values from local.settings.json")
    print()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/release-notes/custom",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED - Local development fallback working correctly")
        elif response.status_code == 400:
            response_data = response.json()
            if "local.settings.json" in response_data.get("message", ""):
                print("⚠️  Test EXPECTED - Missing config in local.settings.json")
                print("   Configure your local.settings.json with Atlassian credentials")
            else:
                print("❌ Test FAILED - Unexpected validation error")
        else:
            print("❌ Test FAILED - Check error message above")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test FAILED - Request error: {e}")
    except json.JSONDecodeError:
        print(f"❌ Test FAILED - Invalid JSON response: {response.text}")
    
    print("\n" + "=" * 50 + "\n")

def test_partial_config_with_fallback():
    """Test partial configuration with fallback to environment variables."""
    
    # Example with partial config - should merge with environment variables
    test_payload = {
        "jql": "project = IP AND fixversion = 'Test Version' AND issuetype = Bug",
        "issue_type": "Bug",
        "max_results": 5,
        "atlassian_config": {
            "confluence_space": "CUSTOM_SPACE"
            # Other fields should fall back to environment variables
        }
    }
    
    print("Testing Partial Configuration with Fallback")
    print("=" * 50)
    print(f"URL: {API_BASE_URL}/release-notes/custom")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print("Note: Missing fields should use values from local.settings.json")
    print()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/release-notes/custom",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED - Partial configuration with fallback working")
        elif response.status_code == 400:
            response_data = response.json()
            if "local.settings.json" in response_data.get("message", ""):
                print("⚠️  Test EXPECTED - Missing config in local.settings.json")
                print("   Configure your local.settings.json with Atlassian credentials")
            else:
                print("❌ Test FAILED - Unexpected validation error")
        else:
            print("❌ Test FAILED - Check error message above")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test FAILED - Request error: {e}")
    except json.JSONDecodeError:
        print(f"❌ Test FAILED - Invalid JSON response: {response.text}")
    
    print("\n" + "=" * 50 + "\n")

def main():
    """Run all tests."""
    print("Azure Function API - Custom Configuration Tests")
    print("=" * 60)
    print("Make sure the Azure Function is running locally on port 7071")
    print("For local development tests, configure local.settings.json with Atlassian credentials")
    print("=" * 60)
    print()
    
    # Test validation errors first (these should work without real credentials)
    test_validation_errors()
    
    # Test local development fallback behavior
    print("Local Development Tests:")
    print("These tests check the fallback to local.settings.json")
    print()
    test_local_development_fallback()
    test_partial_config_with_fallback()
    
    # Test actual endpoints (these require real credentials)
    print("Full Configuration Tests:")
    print("The following tests require real Atlassian credentials in the request body")
    print("Update the test payloads before running these tests")
    print()
    
    # Uncomment these when you have real credentials to test with
    # test_custom_config_batch_endpoint()
    # test_custom_config_single_endpoint()
    
    print("Testing complete!")
    print("\nLocal Development Usage:")
    print("- Configure local.settings.json with your Atlassian credentials")
    print("- Use simplified API calls without atlassian_config in request body")
    print("- System will automatically fall back to environment variables")

if __name__ == "__main__":
    main()
