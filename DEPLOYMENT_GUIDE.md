# Deployment Guide

## Prerequisites for Deployment

### VS Code Extensions (Required)
Install these extensions in VS Code:
- [Azure Functions](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
- [Azure Account](https://marketplace.visualstudio.com/items?itemName=ms-vscode.azure-account)  
- [Azure Resources](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureresourcegroups)

### Azure CLI (Optional but Recommended)
```bash
# Install Azure CLI (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login
```

---

## Step-by-Step Deployment

### Step 1: Sign in to Azure in VS Code

1. Open VS Code
2. Press `Ctrl+Shift+P` to open Command Palette
3. Type `Azure: Sign In` and select it
4. Follow the browser authentication flow
5. Verify you're signed in by checking the Azure icon in the Activity Bar

### Step 2: Prepare Your Project

1. **Ensure your project is ready**:
   ```bash
   # Make sure you're in the project directory
   cd /path/to/Ai4ReleaseNotes-FunctionApp
   
   # Activate virtual environment
   source .venv/bin/activate
   
   # Test locally one more time
   func start
   ```

2. **Verify all functions load correctly** (should see 6 functions)

3. **Stop local functions**: `Ctrl+C`

### Step 3: Create Azure Function App

1. **Open Azure Functions Extension**:
   - Click the Azure icon in VS Code Activity Bar
   - Expand the "Functions" section

2. **Create Function App**:
   - Click the `+` icon next to your subscription
   - Select "Create Function App in Azure... (Advanced)"

3. **Configure Function App**:
   - **Function App Name**: `ai4releasenotes-func-[yourname]` (must be globally unique)
   - **Runtime Stack**: `Python 3.10`
   - **Region**: `East US 2` (same as your Azure OpenAI)
   - **Resource Group**: Create new or select existing
   - **Storage Account**: Create new or select existing
   - **Application Insights**: Create new or select existing
   - **Hosting Plan**: `Consumption (Serverless)`

### Step 4: Configure Application Settings

1. **Upload Local Settings**:
   - Right-click your newly created Function App in VS Code
   - Select "Upload Local Settings..."
   - This uploads your `local.settings.json` settings

2. **Configure Production Settings**:
   - Right-click Function App → "Open in Portal"
   - Go to "Configuration" → "Application Settings"
   - Add/verify these settings:

```
AZURE_OPENAI_KEY = your-production-openai-key
AZURE_OPENAI_ENDPOINT = https://your-endpoint.openai.azure.com/
AZURE_OPENAI_CHAT_COMPLETIONS_API_VERSION = 2024-12-01-preview
AZURE_OPENAI_GPT_DEPLOYMENT = gpt-4o

ATLASSIAN_URL = https://your-company.atlassian.net
ATLASSIAN_INSTANCE_URL = https://your-company.atlassian.net
ATLASSIAN_USERNAME = your-email@company.com
ATLASSIAN_API_KEY = your-production-api-key

CONFLUENCE_SPACE = YourSpace
CONFLUENCE_PARENT = 123456789
CREATE_CONFLUENCE_PAGES = true
CREATE_LOCAL_FILES = false

SSL_VERIFY = true
LOG_LEVEL = INFO
ENVIRONMENT = Production
```

3. **Optional Model-Specific Parameters**:
```
AZURE_OPENAI_MODEL_GPT4O_TEMPERATURE = 0.3
AZURE_OPENAI_MODEL_GPT4O_TOP_P = 0.9
AZURE_OPENAI_MODEL_GPT4O_PRESENCE_PENALTY = 0.1
AZURE_OPENAI_MODEL_GPT4O_FREQUENCY_PENALTY = 0.2
```

⚠️ **Production Security Notes**:
- Use production API keys (different from development)
- Enable SSL verification (`SSL_VERIFY = true`)
- Set appropriate log level (`LOG_LEVEL = INFO`)
- Verify Confluence permissions for page creation

### Step 5: Deploy Your Code

1. **Right-click your Function App** in VS Code
2. **Select "Deploy to Function App..."**
3. **Select your project folder** when prompted
4. **Confirm overwrite** when prompted
5. **Wait for deployment** to complete (2-5 minutes)

### Step 6: Verify Deployment

1. **Test Basic Endpoints**:
```bash
# Replace with your actual function app name
FUNCTION_APP_NAME="ai4releasenotes-func-yourname"

# Test health endpoint
curl "https://${FUNCTION_APP_NAME}.azurewebsites.net/api/health"

# Test basic functionality
curl "https://${FUNCTION_APP_NAME}.azurewebsites.net/api/test"
```

2. **Test Release Notes Generation**:
```bash
# Small test with 2 issues
curl -X PUT "https://${FUNCTION_APP_NAME}.azurewebsites.net/api/release-notes/TEST/1.0.0/Bug/2" \
  -H "Content-Type: application/json"
```

3. **Verify AI Model Configuration**:
   - Check health endpoint response includes model configuration
   - Look for dynamic execution settings in logs
   - Confirm appropriate parameters are being used

4. **Test Confluence Integration** (if enabled):
   - Run test with 1-2 issues
   - Verify pages created in correct Confluence space
   - Check ticket numbers are displayed prominently

5. **View Logs in Azure Portal**:
   - Right-click Function App → "Open in Portal"
   - Go to "Functions" → Select a function → "Monitor"
   - Look for successful model detection and parameter application

### Step 7: Configure CORS (if needed)

If calling functions from a web application:

1. **In Azure Portal**:
   - Go to your Function App
   - Select "CORS" under "API"
   - Add allowed origins or use `*` for development

---

## Post-Deployment Checklist

- [ ] All 6 functions visible in Azure Portal
- [ ] Health endpoint returns model configuration details
- [ ] Application settings match local configuration
- [ ] Function logs show successful model detection
- [ ] Test release notes generation completes successfully
- [ ] Confluence pages created if integration enabled
- [ ] Ticket numbers properly extracted and displayed
- [ ] No parameter compatibility errors in logs

---

## Monitoring Production

### Key Metrics to Monitor
- Function execution success rate
- AI model response times and token usage
- Confluence page creation success rate
- Error rates and types in Application Insights

### Important Log Messages
- `"Using dynamic execution settings for model: [model-name]"` - Confirms model detection
- `"Found ticket number '[number]' for issue [key]"` - Verifies ticket extraction
- `"Successfully created/updated Confluence page"` - Confirms page creation
- `"Using built-in execution settings for GPT-4 variant"` - Shows fallback configuration

### Monitoring Tools
1. **Application Insights** (if configured):
   - Azure Portal → Function App → Application Insights
   - View performance, failures, and custom telemetry

2. **Function-specific Logs**:
   - Azure Portal → Function App → Functions → [Function Name] → Monitor

3. **Live Log Streaming**:
   - Right-click Function App in VS Code → "Start Streaming Logs"

---

## Cost Optimization

### For o4-mini Deployments
- Lower cost per token with limited parameters
- Suitable for high-volume, straightforward analysis
- Automatically uses minimal parameter set

### For GPT-4 Family Deployments
- Higher cost but more sophisticated analysis
- Full parameter control for fine-tuning quality
- Consider setting token limits via environment variables

### Cost Monitoring
- Monitor Azure OpenAI usage in Azure Portal
- Set up budget alerts for unexpected usage spikes
- Review token consumption patterns in Application Insights

---

## Updating Your Deployment

For future updates:

1. **Make changes locally**
2. **Test with `test_functions.py`**
3. **Right-click Function App in VS Code**
4. **Select "Deploy to Function App..."**
5. **Confirm overwrite when prompted**

---

## Troubleshooting Deployment

### Common Deployment Issues

#### 1. "Deployment failed" Error
**Causes**: Package size, timeout, or permissions
**Solutions**:
- Check deployment logs in VS Code output panel
- Verify Function App has sufficient resources
- Try deploying again (sometimes transient)

#### 2. Functions Not Loading After Deployment
**Causes**: Missing dependencies or configuration errors
**Solutions**:
```bash
# Check function logs in Azure Portal
# Look for import errors or missing packages

# Verify requirements.txt includes all dependencies
pip freeze > requirements.txt

# Redeploy with updated requirements
```

#### 3. "Internal Server Error" on API Calls
**Causes**: Configuration missing or invalid
**Solutions**:
- Verify all Application Settings are configured
- Check Azure OpenAI endpoint and key are correct
- Verify Atlassian credentials have necessary permissions

#### 4. AI Model Parameter Errors
**Causes**: Unsupported parameters for specific models
**Solutions**:
- Check logs for "parameter not supported" messages
- Verify model-specific configuration is correct
- Remove unsupported parameters from environment variables

### Debug Mode in Production

Enable detailed logging temporarily:
1. Go to Function App → Configuration
2. Set `LOG_LEVEL = DEBUG`
3. Save and restart Function App
4. Monitor logs for detailed information
5. Set back to `INFO` when debugging complete

---

## Security Best Practices

### Production Security
- Never use development credentials in production
- Store sensitive values in Azure Key Vault (advanced)
- Enable HTTPS only (automatically enforced)
- Use managed identity where possible (advanced)
- Regularly rotate API keys and tokens

### Network Security
- Configure private endpoints for enhanced security (enterprise)
- Use VNet integration if required (premium plans)
- Implement IP restrictions if needed

### Monitoring Security
- Enable audit logging for configuration changes
- Monitor for failed authentication attempts
- Set up alerts for unusual usage patterns

---

## Scaling and Performance

### Automatic Scaling
- Consumption plan automatically scales based on demand
- No configuration needed for basic scaling
- Monitor scaling metrics in Azure Portal

### Performance Optimization
- Configure async processing settings via environment variables
- Monitor token usage and adjust batch sizes
- Use Application Insights to identify bottlenecks

### Premium Plans (for Enterprise)
- Consider Premium or Dedicated plans for:
  - Predictable performance
  - VNet connectivity
  - Longer timeout limits
  - Pre-warmed instances
