#!/usr/bin/env python3
"""
Test script for Azure Functions locally.
This script tests the functions without requiring the Azure Functions runtime.
"""
import os
import sys
import json
import logging
from unittest.mock import Mock

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import azure.functions as func
        print("✅ azure.functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import azure.functions: {e}")
        return False
    
    try:
        import semantic_kernel
        print("✅ semantic_kernel imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import semantic_kernel: {e}")
        return False
    
    try:
        import openai
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import openai: {e}")
        return False
    
    try:
        from src.config.app_config import Config
        print("✅ app_config imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import app_config: {e}")
        return False
    
    return True

def test_config_initialization():
    """Test configuration initialization."""
    print("\n🔧 Testing configuration...")
    
    try:
        from src.config.app_config import Config
        config = Config()
        print("✅ Configuration initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration initialization failed: {e}")
        return False

def test_simple_function():
    """Test the simple test route function."""
    print("\n🚀 Testing simple function...")
    
    try:
        # Import the function app
        from function_app import test_route
        
        # Create a mock request
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = "http://localhost:7071/api/test"
        
        # Call the function
        response = test_route(mock_request)
        
        # Check response
        if hasattr(response, 'get_body'):
            body = response.get_body().decode('utf-8')
            result = json.loads(body)
            
            if result.get('status') == 'ok':
                print("✅ Test function executed successfully")
                print(f"   Message: {result.get('message')}")
                print(f"   Version: {result.get('app_version')}")
                return True
            else:
                print(f"❌ Test function returned unexpected status: {result.get('status')}")
                return False
        else:
            print("❌ Response object doesn't have expected structure")
            return False
            
    except Exception as e:
        print(f"❌ Test function failed: {e}")
        return False

def test_health_function():
    """Test the health check function."""
    print("\n💊 Testing health function...")
    
    try:
        # Import the health function
        from functions.health.function import health_check
        
        # Create a mock request
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = "http://localhost:7071/api/health"
        
        # Call the function
        response = health_check(mock_request)
        
        # Check response
        if hasattr(response, 'get_body'):
            body = response.get_body().decode('utf-8')
            result = json.loads(body)
            
            status = result.get('status', 'unknown')
            print(f"✅ Health check executed successfully")
            print(f"   Status: {status}")
            print(f"   Dependencies: {result.get('dependencies', {})}")
            
            if status in ['healthy', 'degraded']:
                return True
            else:
                print(f"❌ Health check returned unexpected status: {status}")
                return False
        else:
            print("❌ Response object doesn't have expected structure")
            return False
            
    except Exception as e:
        print(f"❌ Health function failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Starting Azure Functions Tests")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_config_initialization),
        ("Simple Function Test", test_simple_function),
        ("Health Function Test", test_health_function),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Azure Functions setup is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
