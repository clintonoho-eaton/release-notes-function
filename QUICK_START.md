# Quick Start Guide

## Prerequisites

1. **Python 3.10+** with virtual environment support
2. **Azure Functions Core Tools v4** 
3. **Node.js** (for Azure Functions Core Tools)

## Setup in 3 Steps

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create `local.settings.json` with your credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "FUNCTIONS_EXTENSION_VERSION": "~4",
    
    "AZURE_OPENAI_KEY": "your-azure-openai-key-here",
    "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
    "AZURE_OPENAI_GPT_DEPLOYMENT": "gpt-4o",
    
    "ATLASSIAN_USERNAME": "your-email@company.com",
    "ATLASSIAN_API_KEY": "your-api-key-here",
    "ATLASSIAN_URL": "https://your-company.atlassian.net",
    
    "CONFLUENCE_SPACE": "YourSpace",
    "CONFLUENCE_PARENT": "123456789",
    
    "SSL_VERIFY": "false",
    "LOG_LEVEL": "DEBUG"
  }
}
```

### 3. Test & Run
```bash
# Quick test (no config needed)
python test_enhanced.py

# Full test (requires config)
python test_functions.py

# Start Azure Functions
source .venv/bin/activate
func start
```

## Quick Test

Once running, test with:
```bash
# Health check
curl http://localhost:7071/api/health

# Generate release notes for bugs
curl -X PUT http://localhost:7071/api/release-notes/PROJECT/1.0.0/Bug/5
```

## What's Available

- **Environment Configuration**: Traditional endpoints using `local.settings.json`
- **Custom Configuration**: New endpoints accepting credentials in request body
- **Local Development Fallback**: Simplified API calls for local testing

## Need Help?

- **Detailed Setup**: See `SETUP_GUIDE.md`
- **API Usage**: See `API_USAGE_CUSTOM_CONFIG.md` 
- **Performance**: See `ASYNC_PERFORMANCE_GUIDE.md`
- **Examples**: See `EXAMPLE_RESPONSES.md`
- **Troubleshooting**: See main `README.md`
