# Testing Guide

Comprehensive testing setup and execution guide for the Ai4ReleaseNotes Azure Functions application.

> **💡 Platform Note**: This project was developed using WSL (Windows Subsystem for Linux). All command examples use Bash syntax. Windows users should adapt commands to PowerShell or Command Prompt - see [Platform Compatibility](#-platform-compatibility) section below.

## 🧪 Test Overview

The project includes 7 comprehensive test files covering different aspects of functionality:

| Test File | Purpose | Dependencies | Runtime |
|-----------|---------|--------------|---------|
| **[`test_enhanced.py`](test_enhanced.py)** | Core functionality tests | ✅ None required | ~30s |
| **[`test_functions.py`](test_functions.py)** | Full Azure Functions tests | ⚙️ Requires config | ~2-3min |
| **[`test_custom_config_api.py`](test_custom_config_api.py)** | Custom configuration API | ⚙️ Requires config | ~1-2min |
| **[`test_ai_analysis.py`](test_ai_analysis.py)** | AI analysis functionality | ⚙️ Requires config | ~30s |
| **[`test_environment.py`](test_environment.py)** | Environment detection | ✅ None required | ~10s |
| **[`test_jql_debug.py`](test_jql_debug.py)** | JQL query debugging | ⚙️ Requires config | ~1min |
| **[`test_custom_debug.py`](test_custom_debug.py)** | Custom debugging | ⚙️ Requires config | ~30s |

---

## 🚀 Quick Start Testing

### 1. Prerequisites

```bash
# Ensure virtual environment is active
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio

# Verify installation
python --version
pytest --version
```

### 2. Quick Test (No Configuration Required)

```bash
# Start with the enhanced test - works without any configuration
python test_enhanced.py
```

Expected output:
```
✅ Environment setup successful
✅ Azure Functions imports working
✅ Core modules accessible
✅ Configuration system functional
```

### 3. Full Configuration Testing

After setting up `local.settings.json`:

```bash
# Test full Azure Functions functionality
python test_functions.py

# Test AI analysis with real API calls
python test_ai_analysis.py
```

---

## 🛠️ VS Code Test Setup

### Test Explorer Configuration

VS Code is configured for optimal testing experience:

1. **Test Discovery**: Automatic detection of pytest tests
2. **Individual Test Running**: Click to run specific tests
3. **Debug Support**: Set breakpoints and debug tests
4. **Task Integration**: Pre-configured test tasks

### Running Tests in VS Code

#### Method 1: Test Explorer (Recommended)
1. **Open Test Explorer**: Click the flask icon in sidebar
2. **Refresh**: Click refresh if tests don't appear
3. **Run**: Click play button next to any test
4. **Debug**: Click debug button to set breakpoints

#### Method 2: VS Code Tasks
1. **Command Palette**: `Ctrl+Shift+P`
2. **Tasks: Run Task**
3. **Select test**:
   - `Test: Enhanced (Quick)` - No config needed
   - `Test: Functions (Full)` - Requires config
   - `Test: AI Analysis` - AI functionality
   - `Test: Custom Config API` - API testing

#### Method 3: Debug Configuration
1. **Run and Debug**: `Ctrl+Shift+D`
2. **Select configuration**:
   - `Debug: Enhanced Tests`
   - `Debug: Functions Tests`
   - `Debug: AI Analysis Tests`
   - etc.
3. **Start debugging**: `F5`

#### Method 4: Terminal
```bash
# Individual test files
python test_enhanced.py
python test_functions.py

# Using pytest
pytest test_enhanced.py -v
pytest test_ai_analysis.py -v -s

# Run all tests
pytest test_*.py -v
```

---

## 📋 Test Categories

### 🟢 No Configuration Tests

These tests work immediately without any setup:

```bash
# Core functionality without external dependencies
python test_enhanced.py

# Environment detection and validation
python test_environment.py
```

**What they test:**
- ✅ Module imports and dependencies
- ✅ Environment variable detection
- ✅ Configuration system structure
- ✅ Basic Azure Functions compatibility

### 🟡 Configuration Required Tests

These tests need `local.settings.json` with valid credentials:

```bash
# Full Azure Functions integration
python test_functions.py

# AI analysis with real API calls
python test_ai_analysis.py

# Custom configuration endpoints
python test_custom_config_api.py
```

**What they test:**
- 🔗 Jira/Confluence API connectivity
- 🤖 Azure OpenAI integration
- 📊 End-to-end analysis workflow
- 🔧 Configuration validation

### 🔴 Debug & Troubleshooting Tests

For specific issue investigation:

```bash
# JQL query debugging
python test_jql_debug.py

# Custom debugging scenarios
python test_custom_debug.py
```

---

## ⚙️ Configuration for Testing

### Minimal Configuration

For basic testing, create `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_KEY": "your-key-here",
    "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
    "AZURE_OPENAI_GPT_DEPLOYMENT": "gpt-4o",
    "ATLASSIAN_USERNAME": "your-email@company.com",
    "ATLASSIAN_API_KEY": "your-api-key",
    "ATLASSIAN_URL": "https://your-company.atlassian.net"
  }
}
```

### Test-Specific Configuration

```json
{
  "Values": {
    // Required for all tests
    "AZURE_OPENAI_KEY": "your-key",
    "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
    "AZURE_OPENAI_GPT_DEPLOYMENT": "gpt-4o",
    
    // Required for Jira/Confluence tests
    "ATLASSIAN_USERNAME": "your-email@company.com",
    "ATLASSIAN_API_KEY": "your-api-key",
    "ATLASSIAN_URL": "https://your-company.atlassian.net",
    
    // Optional: For Confluence integration tests
    "CONFLUENCE_SPACE": "YourTestSpace",
    "CONFLUENCE_PARENT": "123456789",
    "CREATE_CONFLUENCE_PAGES": "false",
    
    // Optional: Performance testing
    "MAX_CONCURRENT_AI_CALLS": "5",
    "AI_BATCH_SIZE": "10"
  }
}
```

---

## 🔍 Test Execution Patterns

### Development Workflow

```bash
# 1. Start with quick tests
python test_enhanced.py

# 2. Setup configuration
# Create/update local.settings.json

# 3. Test connectivity
python test_functions.py

# 4. Test specific functionality
python test_ai_analysis.py
python test_custom_config_api.py

# 5. Debug issues if needed
python test_jql_debug.py
```

### CI/CD Pipeline Testing

```bash
# Stage 1: No-config tests (fast)
pytest test_enhanced.py test_environment.py -v

# Stage 2: Integration tests (requires secrets)
pytest test_functions.py test_ai_analysis.py -v

# Stage 3: Full suite (comprehensive)
pytest test_*.py -v --tb=short
```

### Performance Testing

```bash
# Test with different batch sizes
AI_BATCH_SIZE=5 python test_functions.py
AI_BATCH_SIZE=20 python test_functions.py

# Test concurrent processing
MAX_CONCURRENT_AI_CALLS=10 python test_functions.py
```

---

## 🐛 Troubleshooting Tests

### Common Test Issues

#### "Module not found" errors
```bash
# Ensure virtual environment is active
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### "Config validation failed" errors
```bash
# Validate JSON format
cat local.settings.json | python -m json.tool

# Check required environment variables
python test_environment.py
```

#### "Azure OpenAI connection failed"
```bash
# Test AI configuration specifically
python test_ai_analysis.py

# Check endpoint and key format
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_KEY | head -c 20
```

#### "Jira connection failed"
```bash
# Test Jira connection specifically
python -c "from src.config.app_config import Config; print(Config()._validate_env_vars())"

# Verify API key format
echo $ATLASSIAN_API_KEY | head -c 30
```

### Test Environment Validation

```bash
# Check all test dependencies
python -c "
import azure.functions
import pytest
import asyncio
import openai
print('✅ All test dependencies available')
"

# Validate configuration structure
python -c "
from src.config.app_config import Config
config = Config().get_enricher_config('', '')
print(f'✅ Configuration loaded: {len(config)} settings')
"
```

---

## 📊 Test Results Interpretation

### Successful Test Output

```bash
✅ test_enhanced.py
✓ Environment setup successful
✓ Azure Functions imports working
✓ Core modules accessible

✅ test_functions.py  
✓ Configuration validated
✓ Jira connection established
✓ AI analysis completed
✓ 5/5 issues processed successfully

✅ test_ai_analysis.py
✓ Issue fetched: IP-57837 - Bug
✓ AI Analysis completed successfully
✓ Content validation passed
```

### Failed Test Patterns

```bash
❌ Configuration Error
ERROR: Missing required environment variables: AZURE_OPENAI_KEY
→ Action: Update local.settings.json

❌ Connection Error  
ERROR: Failed to connect to Jira API
→ Action: Check ATLASSIAN_URL and credentials

❌ AI Analysis Error
ERROR: Azure OpenAI request failed (401)
→ Action: Verify AZURE_OPENAI_KEY and endpoint
```

---

## 🚀 Advanced Testing

### Pytest Integration

```bash
# Run with verbose output
pytest test_*.py -v -s

# Run specific test functions
pytest test_ai_analysis.py::test_config_validation -v

# Run with coverage (if installed)
pytest test_*.py --cov=src --cov-report=html

# Parallel execution (if pytest-xdist installed)
pytest test_*.py -n auto
```

### Custom Test Scenarios

```bash
# Test with specific issue types
JQL_OVERRIDE="project = PROJECT AND issuetype = Story" python test_functions.py

# Test with custom batch sizes
AI_BATCH_SIZE=1 python test_functions.py  # Sequential processing
AI_BATCH_SIZE=50 python test_functions.py # Large batch processing

# Test different AI models (if available)
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4o-mini python test_ai_analysis.py
```

### Load Testing

```bash
# Test multiple concurrent requests
for i in {1..5}; do
  python test_ai_analysis.py &
done
wait

# Test with large datasets
MAX_RESULTS=100 python test_functions.py
```

---

## 📈 Performance Benchmarks

### Expected Performance

| Test | Expected Duration | Criteria |
|------|------------------|----------|
| `test_enhanced.py` | < 30 seconds | Module loading and basic validation |
| `test_functions.py` | 2-5 minutes | Full integration with 5 issues |
| `test_ai_analysis.py` | 30-60 seconds | Single issue AI analysis |
| `test_custom_config_api.py` | 1-3 minutes | API endpoint testing |

### Performance Optimization

```bash
# Optimize for speed
MAX_CONCURRENT_AI_CALLS=10
AI_BATCH_SIZE=20
AZURE_OPENAI_REQUEST_TIMEOUT=30

# Optimize for reliability  
MAX_CONCURRENT_AI_CALLS=3
AI_BATCH_SIZE=5
AZURE_OPENAI_REQUEST_TIMEOUT=120
```

---

## 🤝 Contributing Tests

### Adding New Tests

1. **Create test file**: `test_your_feature.py`
2. **Use pytest patterns**: `@pytest.mark.asyncio` for async functions
3. **Add to VS Code tasks**: Update `.vscode/tasks.json`
4. **Document in this guide**: Add to test overview table

### Test Best Practices

- ✅ **Use descriptive test names**: `test_ai_analysis_with_valid_config()`
- ✅ **Include assertions**: `assert result is not None`
- ✅ **Clean output**: Use print statements for progress
- ✅ **Handle errors gracefully**: Meaningful error messages
- ✅ **Test isolation**: Each test should be independent

### Example Test Structure

```python
#!/usr/bin/env python3
"""Test description."""

import asyncio
import pytest
import sys
import os

# Standard project setup
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

@pytest.mark.asyncio
async def test_your_feature():
    """Test your feature functionality."""
    # Test implementation
    assert True, "Test should pass"
    print("✓ Feature tested successfully")

if __name__ == "__main__":
    asyncio.run(test_your_feature())
```

---

## 📞 Testing Support

### Getting Help

1. **Check test output**: Look for specific error messages
2. **Run environment validation**: `python test_environment.py`
3. **Validate configuration**: `python test_enhanced.py`
4. **Check logs**: Enable verbose logging in tests

### Useful Debugging Commands

```bash
# Check Python environment
python --version
pip list | grep -E "(azure|pytest|openai)"  # Windows: findstr instead of grep

# Validate virtual environment  
echo $VIRTUAL_ENV  # Windows PowerShell: $env:VIRTUAL_ENV, CMD: echo %VIRTUAL_ENV%
which python       # Windows PowerShell: Get-Command python, CMD: where python

# Test specific imports
python -c "from src.config.app_config import Config; print('✅ Config OK')"
python -c "import azure.functions; print('✅ Azure Functions OK')"
```

---

**🎯 Ready to test? Start with `python test_enhanced.py` - no configuration required!**

---

## 🖥️ Platform Compatibility

### Command Adaptations for Windows

Since this project was developed in WSL, Windows users need to adapt Bash commands:

#### Virtual Environment Management

| Operation | Linux/WSL/macOS | Windows PowerShell | Windows Command Prompt |
|-----------|-----------------|-------------------|----------------------|
| **Activate venv** | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` | `.venv\Scripts\activate.bat` |
| **Create venv** | `python3 -m venv .venv` | `python -m venv .venv` | `python -m venv .venv` |
| **Check activation** | `echo $VIRTUAL_ENV` | `$env:VIRTUAL_ENV` | `echo %VIRTUAL_ENV%` |

#### Process Management

| Operation | Linux/WSL/macOS | Windows PowerShell | Windows Command Prompt |
|-----------|-----------------|-------------------|----------------------|
| **Kill port 7071** | `lsof -ti:7071 \| xargs kill -9` | `Get-Process -Name func \| Stop-Process` | `taskkill /F /IM func.exe` |
| **Find Python process** | `ps aux \| grep python` | `Get-Process python` | `tasklist \| findstr python` |
| **Check port usage** | `netstat -tulpn \| grep 7071` | `netstat -an \| Select-String 7071` | `netstat -an \| findstr 7071` |

#### File Operations

| Operation | Linux/WSL/macOS | Windows PowerShell | Windows Command Prompt |
|-----------|-----------------|-------------------|----------------------|
| **View file** | `cat local.settings.json` | `Get-Content local.settings.json` | `type local.settings.json` |
| **Find files** | `find . -name "test_*.py"` | `Get-ChildItem -Recurse -Name "test_*.py"` | `dir /s test_*.py` |
| **Check path** | `which python` | `Get-Command python` | `where python` |

### Windows-Specific Testing Setup

#### PowerShell Setup
```powershell
# Set execution policy (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Run tests
python test_enhanced.py
pytest test_*.py -v
```

#### Command Prompt Setup
```cmd
:: Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate.bat

:: Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

:: Run tests
python test_enhanced.py
pytest test_*.py -v
```

### Azure Functions Core Tools Installation

#### Linux/WSL
```bash
# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

#### Windows
```powershell
# Using Chocolatey
choco install azure-functions-core-tools

# Using npm (if Node.js installed)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Manual download from:
# https://github.com/Azure/azure-functions-core-tools/releases
```

### Platform-Specific Test Commands

#### Running Tests Across Platforms

**Linux/WSL/macOS:**
```bash
# Activate environment and run tests
source .venv/bin/activate
python test_enhanced.py
pytest test_ai_analysis.py -v -s
```

**Windows PowerShell:**
```powershell
# Activate environment and run tests
.venv\Scripts\Activate.ps1
python test_enhanced.py
pytest test_ai_analysis.py -v -s
```

**Windows Command Prompt:**
```cmd
:: Activate environment and run tests
.venv\Scripts\activate.bat
python test_enhanced.py
pytest test_ai_analysis.py -v -s
```

### IDE Configuration for Windows

#### VS Code on Windows
```json
// .vscode/settings.json for Windows
{
    "python.defaultInterpreterPath": "./.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["."]
}
```

#### VS Code Tasks for Windows
```json
// .vscode/tasks.json - Windows version
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Test: Enhanced (Windows)",
            "type": "shell",
            "command": "${config:python.defaultInterpreterPath}",
            "args": ["test_enhanced.py"],
            "group": "test",
            "options": {
                "shell": {
                    "executable": "powershell.exe",
                    "args": ["-Command"]
                }
            }
        }
    ]
}
```
