#!/usr/bin/env python3
"""
Test script to debug JQL and Jira connection.
"""

import json
import requests
import time

def test_jql_variations():
    """Test different JQL variations to debug the issue."""
    print("🔍 Testing JQL variations...")
    
    # Base URL for local development
    base_url = "http://localhost:7071/api/release-notes/custom"
    
    test_cases = [
        {
            "name": "Original JQL",
            "jql": "project = IP AND fixversion = \"PI08-2025-01\" AND issuetype = Bug",
            "issue_type": "Bug",
            "max_results": 10
        },
        {
            "name": "Simplified JQL - Project only",
            "jql": "project = IP",
            "issue_type": "Bug", 
            "max_results": 5
        },
        {
            "name": "Simplified JQL - Project and type only",
            "jql": "project = IP AND issuetype = Bug",
            "issue_type": "Bug",
            "max_results": 5
        },
        {
            "name": "Alternative fix version format",
            "jql": "project = IP AND fixversion = PI08-2025-01 AND issuetype = Bug",
            "issue_type": "Bug",
            "max_results": 10
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print(f"   JQL: {test_case['jql']}")
        
        try:
            response = requests.post(
                base_url,
                json=test_case,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                response_json = response.json()
                issue_count = response_json.get("issue_count", 0)
                print(f"   ✅ Success! Found {issue_count} issues")
                if issue_count > 0:
                    print(f"   🎯 This JQL works! Issue count: {issue_count}")
                    confluence_pages = response_json.get("confluence_pages", {})
                    print(f"   📄 Pages - Created: {len(confluence_pages.get('created', []))}, "
                          f"Updated: {len(confluence_pages.get('updated', []))}, "
                          f"Errors: {len(confluence_pages.get('errors', []))}")
                else:
                    print(f"   ⚠️  No issues found with this JQL")
            else:
                try:
                    error_json = response.json()
                    print(f"   ❌ Error: {error_json.get('message', 'Unknown error')}")
                except:
                    print(f"   ❌ Error: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        print("-" * 40)

def test_health_check():
    """Test the health check to verify basic connectivity."""
    print("\n🏥 Testing Health Check...")
    
    try:
        response = requests.get("http://localhost:7071/api/health", timeout=10)
        print(f"📊 Health Status: {response.status_code}")
        
        if response.status_code == 200:
            health_json = response.json()
            print(f"✅ Health check successful!")
            print(f"📝 Health response: {json.dumps(health_json, indent=2)}")
        else:
            print(f"❌ Health check failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check request failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting JQL debug tests...")
    print("=" * 60)
    
    # Test health first
    test_health_check()
    
    # Test JQL variations
    test_jql_variations()
    
    print("\n🏁 JQL debug tests completed!")
