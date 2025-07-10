# Detailed Setup Guide

## Prerequisites

### Required Software
1. **Python 3.10+** with virtual environment support
2. **Azure Functions Core Tools v4** 
3. **Node.js** (for Azure Functions Core Tools)

### Installation Commands
```bash
# Install Azure Functions Core Tools (Linux)
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## Virtual Environment Setup

### Create and Activate
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# Verify activation (should show .venv in path)
which python
```

### Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "(azure-functions|semantic-kernel|openai|atlassian|pydantic)"
```

## Configuration Setup

### Create local.settings.json

Create this file in the project root with your actual credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "FUNCTIONS_EXTENSION_VERSION": "~4",
    
    "# Azure OpenAI Configuration": "",
    "AZURE_OPENAI_KEY": "your-azure-openai-key-here",
    "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
    "AZURE_OPENAI_CHAT_COMPLETIONS_API_VERSION": "2024-12-01-preview",
    "AZURE_OPENAI_GPT_DEPLOYMENT": "gpt-4o",
    
    "# Atlassian Configuration": "",
    "ATLASSIAN_URL": "https://your-company.atlassian.net",
    "ATLASSIAN_INSTANCE_URL": "https://your-company.atlassian.net",
    "ATLASSIAN_USERNAME": "your-email@company.com",
    "ATLASSIAN_API_KEY": "your-atlassian-api-key",
    
    "# Confluence Settings": "",
    "CONFLUENCE_SPACE": "YourProjectSpace",
    "CONFLUENCE_PARENT": "123456789",
    "CREATE_CONFLUENCE_PAGES": "true",
    "CREATE_LOCAL_FILES": "false",
    
    "# Development Settings": "",
    "SSL_VERIFY": "false",
    "LOG_LEVEL": "DEBUG",
    "ENVIRONMENT": "Development"
  },
  "Host": {
    "LocalHttpPort": 7071,
    "CORS": "*",
    "CORSCredentials": false
  }
}
```

### Required Credentials

#### Azure OpenAI
- **Key**: Get from Azure Portal → Your OpenAI Resource → Keys and Endpoint
- **Endpoint**: Should end with `.openai.azure.com/`
- **Deployment**: Name of your GPT model deployment

#### Atlassian API
- **Username**: Your email address for Atlassian access
- **API Key**: Create at: https://id.atlassian.com/manage-profile/security/api-tokens
- **Instance URL**: Your organization's Atlassian URL

#### Confluence
- **Space**: The key (not name) of your Confluence space
- **Parent**: Page ID where release notes will be created (found in page URL)

### Security Notes

⚠️ **Important**: Never commit `local.settings.json` to version control
- File is already in `.gitignore`
- Use different credentials for development vs production
- Store production credentials securely (Azure Key Vault recommended)

## Testing Your Setup

### 1. Quick Test (No External APIs)
```bash
# Activate virtual environment
source .venv/bin/activate

# Run basic tests
python test_enhanced.py
```

**Expected output:**
```
✅ Package imports successful
✅ Azure Functions compatibility verified
✅ Core functionality working
✅ Basic tests completed successfully
```

### 2. Full Test (Requires Configuration)
```bash
# Run comprehensive tests
python test_functions.py
```

**Expected output:**
```
✅ Configuration loaded successfully
✅ Health endpoint working
✅ External service connectivity verified
✅ All functions registered correctly
✅ Full test suite completed successfully
```

### 3. Test Azure Functions Locally
```bash
# Start Azure Functions (ensure virtual environment is active)
source .venv/bin/activate
func start
```

**Expected output:**
```
Found Python version 3.10.x (python3).

Azure Functions Core Tools
Core Tools Version:       4.x.x
Function Runtime Version: 4.x.x

Functions:
  health: [GET] http://localhost:7071/api/health
  test: [GET] http://localhost:7071/api/test
  release_notes_batch: [PUT] http://localhost:7071/api/release-notes/{proj}/{fixver}/{issuetype}
  release_notes_single: [PUT] http://localhost:7071/api/release-notes/{proj}/{issue_key}
  diagnostics: [PUT] http://localhost:7071/api/diagnostics/release-notes/{proj}/{fixver}/{issuetype}
  extensions_sample: [GET] http://localhost:7071/api/extensions/sample

For detailed output, run func with --verbose flag.
```

### 4. Test API Endpoints
```bash
# Test health endpoint
curl http://localhost:7071/api/health

# Test basic functionality
curl http://localhost:7071/api/test

# Test release notes generation (replace with your project details)
curl -X PUT "http://localhost:7071/api/release-notes/TEST/1.0.0/Bug/2"
```

## Troubleshooting Setup Issues

### Common Problems

#### 1. "No module named 'pydantic'" Error
**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep pydantic
```

#### 2. "func: command not found"
**Cause**: Azure Functions Core Tools not installed or not in PATH

**Solution**:
```bash
# Install Core Tools (Linux)
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Verify installation
func --version

# If still not found, check PATH
echo $PATH
```

#### 3. "Permission denied" for func
**Cause**: Executable permissions missing

**Solution**:
```bash
# Find and fix permissions
which func
chmod +x $(which func)

# Or for npm global installation
chmod +x ~/.npm-global/lib/node_modules/azure-functions-core-tools/lib/main.js
```

#### 4. "Port 7071 is unavailable"
**Cause**: Previous function instance still running

**Solution**:
```bash
# Find and kill process using port 7071
lsof -ti:7071 | xargs kill -9

# Then restart functions
func start
```

#### 5. "0 functions found"
**Cause**: Package import errors or configuration issues

**Solution**:
```bash
# Check virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should be 3.10+

# Check for import errors
python -c "import azure.functions; print('Azure Functions OK')"
python -c "import src.config.app_config; print('App Config OK')"

# Start with verbose output
func start --verbose
```

#### 6. Configuration Loading Errors
**Cause**: Missing or incorrect `local.settings.json`

**Solution**:
```bash
# Verify file exists and has correct format
cat local.settings.json | python -m json.tool

# Check required fields are present
grep -E "(AZURE_OPENAI_KEY|ATLASSIAN_USERNAME|ATLASSIAN_API_KEY)" local.settings.json
```

### Debug Mode

For detailed debugging:

```bash
# Start with maximum verbosity
func start --verbose

# Check logs in detail
tail -f ~/.azure-functions-core-tools/logs/*.log

# Enable Python debug logging
export PYTHONPATH=$PWD
export FUNCTIONS_WORKER_LOG_LEVEL=DEBUG
func start
```

### Verification Checklist

Before proceeding to development:

- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] `local.settings.json` created with actual credentials
- [ ] `test_enhanced.py` passes all tests
- [ ] `test_functions.py` passes all tests
- [ ] `func start` shows 6 functions loaded
- [ ] Health endpoint returns model configuration
- [ ] Basic API call completes successfully

## Next Steps

Once setup is complete:

1. **Read API Documentation**: See `API_USAGE_CUSTOM_CONFIG.md`
2. **Review Examples**: See `EXAMPLE_RESPONSES.md`
3. **Optimize Performance**: See `ASYNC_PERFORMANCE_GUIDE.md`
4. **Deploy to Azure**: See deployment section in main README
5. **Monitor Production**: Configure Application Insights for monitoring
