# Troubleshooting Guide

## Common Setup Issues

### 1. Virtual Environment Problems

#### "No module named 'pydantic'" Error
**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Verify activation (should show .venv in path)
which python

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep pydantic
```

#### Virtual Environment Not Found
**Cause**: Virtual environment wasn't created properly

**Solution**:
```bash
# Remove existing broken environment
rm -rf .venv

# Create new virtual environment
python3 -m venv .venv

# Activate and install dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Azure Functions Core Tools Issues

#### "func: command not found"
**Cause**: Azure Functions Core Tools not installed or not in PATH

**Solution**:
```bash
# Check if installed
which func

# Install Core Tools (Linux)
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Install via npm (alternative)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Verify installation
func --version
```

#### "Permission denied" for func
**Cause**: Executable permissions missing

**Solution**:
```bash
# Find func location and fix permissions
which func
chmod +x $(which func)

# For npm global installation
chmod +x ~/.npm-global/lib/node_modules/azure-functions-core-tools/lib/main.js
```

### 3. Port and Process Issues

#### "Port 7071 is unavailable"
**Cause**: Previous function instance still running

**Solution**:
```bash
# Find processes using port 7071
lsof -ti:7071

# Kill all processes using the port
lsof -ti:7071 | xargs kill -9

# Alternative: kill specific process by PID
kill -9 <PID>

# Then restart functions
func start
```

#### Multiple Python Processes
**Cause**: Multiple function instances running

**Solution**:
```bash
# Find all Python processes
ps aux | grep python

# Kill Azure Functions related processes
pkill -f "azure-functions-worker"
pkill -f "func start"

# Clean restart
source .venv/bin/activate
func start
```

---

## Configuration Issues

### 1. local.settings.json Problems

#### File Format Errors
**Cause**: Invalid JSON syntax

**Solution**:
```bash
# Validate JSON format
cat local.settings.json | python -m json.tool

# Common issues to check:
# - Missing commas between properties
# - Trailing commas (not allowed in JSON)
# - Unescaped quotes in values
# - Missing closing braces
```

#### Missing Required Fields
**Cause**: Essential configuration missing

**Solution**:
```bash
# Check for required fields
grep -E "(AZURE_OPENAI_KEY|ATLASSIAN_USERNAME|ATLASSIAN_API_KEY)" local.settings.json

# If missing, add to local.settings.json:
{
  "Values": {
    "AZURE_OPENAI_KEY": "your-key-here",
    "ATLASSIAN_USERNAME": "your-email@company.com",
    "ATLASSIAN_API_KEY": "your-api-key-here"
  }
}
```

### 2. Credential Issues

#### Invalid Azure OpenAI Key
**Symptoms**: Health endpoint fails, AI analysis errors

**Solution**:
```bash
# Test Azure OpenAI connection
curl -H "api-key: YOUR_KEY" \
  "https://YOUR_ENDPOINT.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT/chat/completions?api-version=2024-12-01-preview" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"max_tokens":5}'

# Should return valid response, not 401/403
```

#### Invalid Atlassian Credentials
**Symptoms**: Jira API failures, authentication errors

**Solution**:
```bash
# Test Jira API access
curl -u "EMAIL:API_TOKEN" \
  "https://YOUR_COMPANY.atlassian.net/rest/api/3/myself"

# Should return user information, not authentication error
```

---

## Function Loading Issues

### 1. "0 functions found"

#### Import Errors
**Cause**: Python package import failures

**Solution**:
```bash
# Check for import errors manually
python -c "import azure.functions; print('Azure Functions OK')"
python -c "import src.config.app_config; print('App Config OK')"
python -c "import src.ai.azure_configurator; print('AI Config OK')"

# Start with verbose output to see errors
func start --verbose
```

#### Missing Dependencies
**Cause**: Required packages not installed

**Solution**:
```bash
# Verify all key packages are installed
pip list | grep -E "(azure-functions|semantic-kernel|openai|atlassian|pydantic)"

# If missing, reinstall everything
pip install -r requirements.txt

# Check for version conflicts
pip check
```

### 2. Plugin Loading Warnings

#### Semantic Kernel Plugin Warnings
**Symptoms**: Warnings about `__init__.py` files during startup

**This is Normal**: Semantic Kernel tries to load all Python files as plugins, including package markers. The warnings don't affect functionality.

**Example Warning** (can be ignored):
```
Failed to create function from Python file: src/plugins/semantic_kernel/__init__.py
```

#### Missing Plugin Directory
**Cause**: Plugin directory structure not correct

**Solution**:
```bash
# Verify plugin directory exists
ls -la src/plugins/semantic_kernel/

# Should contain plugin directories, not just __init__.py files
```

---

## Runtime Issues

### 1. API Endpoint Errors

#### 500 Internal Server Error
**Cause**: Unhandled exception in function code

**Solution**:
```bash
# Check function logs for detailed error
func start --verbose

# Look for stack traces in output
# Common causes:
# - Missing configuration
# - Invalid credentials  
# - Network connectivity issues
```

#### 401 Unauthorized
**Cause**: Invalid credentials for external APIs

**Solution**:
1. Verify Azure OpenAI key and endpoint
2. Check Atlassian username and API token
3. Ensure API tokens have necessary permissions

#### 502 Bad Gateway
**Cause**: External API (Jira/Confluence) errors

**Solution**:
1. Check Atlassian service status
2. Verify API rate limits not exceeded
3. Test direct API access outside function

### 2. AI Analysis Issues

#### Empty AI Responses
**Cause**: Model parameter incompatibility or quota limits

**Solution**:
```bash
# Check Azure OpenAI deployment status
az cognitiveservices account deployment list \
  --name YOUR_OPENAI_RESOURCE \
  --resource-group YOUR_RESOURCE_GROUP

# Verify quota and usage
# Check for model parameter errors in logs
```

#### Token Limit Exceeded
**Cause**: Input text too large for model

**Solution**:
- Reduce batch size for processing
- Check issue description lengths
- Increase max_completion_tokens if needed

---

## Performance Issues

### 1. Slow Response Times

#### Large Batch Processing
**Cause**: Processing too many issues simultaneously

**Solution**:
```bash
# Reduce concurrent operations in local.settings.json
"MAX_CONCURRENT_AI_CALLS": "3"
"AI_BATCH_SIZE": "5"

# Increase timeout if needed
"AZURE_OPENAI_REQUEST_TIMEOUT": "120"
```

#### Network Connectivity
**Cause**: Slow network to external APIs

**Solution**:
- Test network connectivity to Atlassian and Azure OpenAI
- Consider using Azure region closer to your location
- Check for proxy or firewall restrictions

### 2. Memory Issues

#### Function App Running Out of Memory
**Cause**: Processing too many large issues

**Solution**:
- Reduce AI_BATCH_SIZE
- Process fewer issues per request
- Consider using Premium hosting plan

---

## Debug Mode and Logging

### Enable Detailed Debugging

#### Local Development
```bash
# Set debug environment variables
export FUNCTIONS_WORKER_LOG_LEVEL=DEBUG
export PYTHONPATH=$PWD

# Start with maximum verbosity
func start --verbose

# Check specific logs
tail -f ~/.azure-functions-core-tools/logs/*.log
```

#### Configuration Debugging
```bash
# Test configuration loading
python -c "
from src.config.app_config import AppConfig
config = AppConfig()
print('Config loaded successfully')
print(f'Azure OpenAI Endpoint: {config.azure_openai_endpoint}')
print(f'Atlassian URL: {config.atlassian_url}')
"
```

### Production Debugging

#### Azure Portal Logs
1. Go to Function App in Azure Portal
2. Select "Functions" → Choose function → "Monitor"
3. View recent executions and errors
4. Check "Invocations" and "Logs" tabs

#### Application Insights
1. Function App → Application Insights
2. Go to "Live Metrics" for real-time monitoring
3. Check "Failures" for error analysis
4. Use "Performance" for timing analysis

---

## Network and Connectivity

### SSL/TLS Issues

#### SSL Verification Errors
**Cause**: Corporate firewall or proxy issues

**Solution**:
```bash
# For development only - disable SSL verification
# In local.settings.json:
"SSL_VERIFY": "false"

# For production - fix certificate issues
# Ensure proper certificate chain
# Check corporate proxy configuration
```

### Firewall and Proxy Issues

#### Corporate Network Restrictions
**Cause**: Blocked access to external APIs

**Solution**:
1. Whitelist required domains:
   - `*.atlassian.net`
   - `*.openai.azure.com`
   - `management.azure.com`
2. Configure proxy settings if required
3. Test connectivity outside corporate network

---

## Data and Content Issues

### 1. Confluence Page Creation Failures

#### Invalid Parent Page ID
**Cause**: Parent page doesn't exist or no permission

**Solution**:
```bash
# Test parent page access
curl -u "EMAIL:API_TOKEN" \
  "https://YOUR_COMPANY.atlassian.net/wiki/rest/api/content/PARENT_PAGE_ID"

# Should return page information
# If 404, page doesn't exist
# If 403, insufficient permissions
```

#### Space Permission Issues
**Cause**: User doesn't have write access to Confluence space

**Solution**:
1. Verify space permissions in Confluence
2. Request write access from space administrator
3. Test with a different space where you have permissions

### 2. Jira Access Issues

#### JQL Query Errors
**Cause**: Invalid JQL syntax or insufficient permissions

**Solution**:
```bash
# Test JQL query in Jira web interface first
# Verify project access permissions
# Simplify query to isolate issues

# Example test:
project = TEST AND issuetype = Bug
```

#### Missing Issue Fields
**Cause**: Custom fields not accessible or don't exist

**Solution**:
1. Check field permissions in Jira
2. Verify field names are correct
3. Test with standard fields only first

---

## Getting Help

### Diagnostic Commands

#### Full System Check
```bash
# Run comprehensive diagnostics
python test_enhanced.py  # Basic functionality
python test_functions.py  # Full configuration test

# Check specific components
curl http://localhost:7071/api/health
curl http://localhost:7071/api/test
```

#### Environment Information
```bash
# Gather environment details
echo "Python version: $(python --version)"
echo "Azure Functions version: $(func --version)"
echo "Virtual environment: $VIRTUAL_ENV"
echo "Current directory: $(pwd)"
ls -la local.settings.json
```

### Log Collection

#### Collect Relevant Logs
```bash
# Function logs
func start --verbose > function_logs.txt 2>&1

# Configuration test
python test_functions.py > test_output.txt 2>&1

# System information
pip list > installed_packages.txt
```

When seeking help, include:
1. Error messages (full stack traces)
2. Configuration (sanitized - remove credentials)
3. Steps to reproduce the issue
4. Environment information
5. Recent changes made
