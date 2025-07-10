# Ai4ReleaseNotes Azure Functions

AI-powered Azure Functions application that automatically generates structured release notes from Jira issues and creates Confluence pages.

## ✨ Key Features

- **🤖 AI-Powered Analysis**: Using Azure OpenAI with automatic model adaptation (GPT-4, o4-mini)
- **📝 Confluence Integration**: Automated page creation with structured formatting
- **⚡ High Performance**: Concurrent processing with configurable batch sizes
- **🔧 Flexible Configuration**: Environment-based or request-based credentials
- **📊 Smart Analysis**: Issue categorization, root cause analysis, and impact assessment
- **🚀 Serverless**: Azure Functions v2 with auto-scaling and pay-per-use

## 🚀 Quick Start

> **💡 Development Note**: This project was developed using WSL (Windows Subsystem for Linux). All command examples use Bash syntax. Windows users should adapt commands to PowerShell or Command Prompt as needed.

### 1. Setup (5 minutes)
```bash
# Clone and enter directory
cd Ai4ReleaseNotes-FunctionApp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure
Create `local.settings.json` with your credentials:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_KEY": "your-key-here",
    "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
    "ATLASSIAN_USERNAME": "your-email@company.com",
    "ATLASSIAN_API_KEY": "your-api-key",
    "ATLASSIAN_URL": "https://your-company.atlassian.net",
    "CONFLUENCE_SPACE": "YourSpace",
    "CONFLUENCE_PARENT": "123456789"
  }
}
```

### 3. Test & Run
```bash
# Quick test (no config needed)
python test_enhanced.py

# Start Azure Functions
func start
```

🧪 **Need comprehensive testing?** See **[TESTING.md](TESTING.md)** for complete test suite guide

### 4. Try It Out
```bash
# Health check
curl http://localhost:7071/api/health

# Generate release notes
curl -X PUT http://localhost:7071/api/release-notes/PROJECT/1.0.0/Bug/5
```

🎉 **Done!** You should see AI-generated release notes and Confluence pages created.

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| **[QUICK_START.md](QUICK_START.md)** | 5-minute setup guide |
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Detailed installation and configuration |
| **[TESTING.md](TESTING.md)** | 🧪 Comprehensive testing guide with 7 test suites |
| **[API_ENDPOINTS.md](API_ENDPOINTS.md)** | Complete API reference |
| **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** | Deploy to Azure step-by-step |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Fix common issues |

> **💻 Windows Users**: See [Platform Compatibility](#-platform-compatibility) section for PowerShell/CMD command adaptations

### Specialized Guides
- **[API_USAGE_CUSTOM_CONFIG.md](API_USAGE_CUSTOM_CONFIG.md)** - Custom configuration API
- **[ASYNC_PERFORMANCE_GUIDE.md](ASYNC_PERFORMANCE_GUIDE.md)** - Performance optimization
- **[EXAMPLE_RESPONSES.md](EXAMPLE_RESPONSES.md)** - API response examples
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Latest features

---

## 🔌 Available Endpoints

Once running (`func start`), your functions are available at:

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/health` | GET | Health check with model configuration |
| `/api/test` | GET | Basic functionality test |
| `/api/release-notes/{proj}/{fixver}/{issuetype}` | PUT | Generate release notes by issue type |
| `/api/release-notes/{proj}/{issue_key}` | PUT | Generate release notes for specific issue |
| `/api/release-notes/custom` | POST | Custom configuration batch processing |
| `/api/release-notes/single` | POST | Custom configuration single issue |

### Example Usage

```bash
# Health check
curl http://localhost:7071/api/health

# Generate release notes for bugs (environment config)
curl -X PUT http://localhost:7071/api/release-notes/PROJECT/1.0.0/Bug/5

# Custom configuration (local development - no credentials needed)
curl -X POST http://localhost:7071/api/release-notes/custom \
  -H "Content-Type: application/json" \
  -d '{"jql": "project = PROJECT AND issuetype = Bug", "max_results": 5}'
```

📖 **See [API_ENDPOINTS.md](API_ENDPOINTS.md) for complete API reference**

---
## 🤖 AI Models & Configuration

### Dynamic Model Support
The system automatically detects your Azure OpenAI model and applies appropriate parameters:

- **🎯 GPT-4 Family** (gpt-4, gpt-4o, gpt-4.1): Full parameter support for sophisticated analysis
- **💰 o4-mini**: Cost-optimized with limited parameters for high-volume processing
- **⚙️ Custom Parameters**: Override via environment variables (e.g., `AZURE_OPENAI_MODEL_GPT4O_TEMPERATURE=0.3`)

### Configuration Modes

#### 🌍 Environment Configuration
Traditional mode using `local.settings.json` or Azure App Settings:
```bash
# All credentials from environment
curl -X PUT http://localhost:7071/api/release-notes/PROJECT/1.0.0/Bug
```

#### 🔐 Custom Configuration  
Enhanced security with credentials in request body:
```bash
# Production: Full credentials required
curl -X POST http://localhost:7071/api/release-notes/custom \
  -d '{"jql": "...", "atlassian_config": {"username": "...", "api_key": "..."}}'

# Local development: Credentials optional (falls back to local.settings.json)
curl -X POST http://localhost:7071/api/release-notes/custom \
  -d '{"jql": "project = PROJECT AND issuetype = Bug"}'
```

---

## 🏗️ Project Structure

```
Ai4ReleaseNotes-FunctionApp/
├── 📄 Quick Start & Documentation
│   ├── README.md              # This file - main overview
│   ├── QUICK_START.md         # 5-minute setup guide  
│   ├── SETUP_GUIDE.md         # Detailed installation
│   └── API_ENDPOINTS.md       # Complete API reference
│
├── 🔧 Configuration & Examples  
│   ├── local.settings.json    # Local development config (create this)
│   ├── EXAMPLE_RESPONSES.md   # API response examples
│   └── API_USAGE_CUSTOM_CONFIG.md  # Custom config API guide
│
├── 🚀 Deployment & Operations
│   ├── DEPLOYMENT_GUIDE.md    # Deploy to Azure step-by-step
│   ├── TROUBLESHOOTING.md     # Fix common issues
│   └── ASYNC_PERFORMANCE_GUIDE.md  # Performance optimization
│
├── ⚡ Core Application
│   ├── function_app.py        # Main Azure Functions entry point
│   ├── host.json              # Azure Functions configuration
│   ├── requirements.txt       # Python dependencies
│   └── functions/             # Function definitions
│       ├── release_notes/     # Release notes HTTP functions
│       ├── health/            # Health check functions
│       ├── diagnostics/       # Diagnostic functions
│       └── extensions/        # Extension functions
│
└── 🧠 Source Code
    └── src/                   # Business logic
        ├── ai/                # Azure OpenAI integration
        ├── atlassian/         # Jira/Confluence clients
        ├── config/            # Configuration management
        ├── services/          # Application services
        └── utils/             # Utility functions
```

---

## 🆕 Recent Updates

### v2.3.0 - Local Development Fallback (January 2025)
✅ **IMPLEMENTATION COMPLETE**: Custom configuration endpoints now support automatic fallback to `local.settings.json` for local development

- **🔧 Simplified Local Development**: No need to include credentials in API requests when running locally
- **🔀 Automatic Environment Detection**: Detects local vs production automatically
- **⚙️ Partial Configuration Support**: Mix request and environment configuration as needed
- **🔒 Enhanced Security**: Full credential control in production environments

### v2.2.0 - Async Performance Optimization (July 2025)
- **⚡ Concurrent Processing**: 3-5x faster for large batches with configurable concurrency
- **📦 Intelligent Batching**: Optimized memory usage and API rate limits
- **⏱️ Adaptive Timeouts**: Smart timeout handling for different workload sizes

### v2.1.0 - Dynamic AI Model Configuration
- **🤖 Automatic Model Detection**: Adapts to GPT-4 family vs o4-mini automatically
- **⚙️ Model-Specific Parameters**: Optimized settings per model type
- **🔧 External Configuration**: Override parameters via environment variables

📖 **See [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) for complete feature details**

---

## 🎯 Configuration Options

### Two Configuration Modes

#### 🌍 Environment Configuration (Traditional)
- Reads credentials from `local.settings.json` or Azure App Settings
- Simple setup for single-user scenarios
- Existing endpoints: `PUT /api/release-notes/{proj}/{fixver}/{issuetype}`

#### 🔐 Custom Configuration (Enhanced Security)
- Accepts credentials in request body
- **Local Development**: Automatic fallback to environment variables
- **Production**: Full credential control per request
- New endpoints: `POST /api/release-notes/custom`, `POST /api/release-notes/single`

### Local Development Benefits
- **No credentials in requests**: Automatically uses `local.settings.json`
- **Simplified testing**: Minimal request bodies for API calls
- **Mixed configuration**: Partial config in request + environment fallback

📖 **See [API_USAGE_CUSTOM_CONFIG.md](API_USAGE_CUSTOM_CONFIG.md) for detailed examples**

---

📖 **See [API_USAGE_CUSTOM_CONFIG.md](API_USAGE_CUSTOM_CONFIG.md) for detailed examples**

---

## ❗ Common Issues & Solutions

### Virtual Environment Issues
```bash
# "No module named 'pydantic'" Error
source .venv/bin/activate  # Always activate first
pip install -r requirements.txt

# "func: command not found"
sudo apt-get install azure-functions-core-tools-4

# "Port 7071 is unavailable"
lsof -ti:7071 | xargs kill -9  # Kill existing processes
```

### Platform Compatibility (Windows Users)
Since this project was developed in WSL, Windows users may need to adapt commands:

```powershell
# PowerShell equivalents
.venv\Scripts\Activate.ps1     # Instead of: source .venv/bin/activate
python -m venv .venv           # Instead of: python3 -m venv .venv
Get-Process -Name func | Stop-Process  # Instead of: lsof -ti:7071 | xargs kill -9

# Command Prompt equivalents  
.venv\Scripts\activate.bat     # Instead of: source .venv/bin/activate
python -m venv .venv           # Instead of: python3 -m venv .venv
taskkill /F /IM func.exe       # Instead of: lsof -ti:7071 | xargs kill -9
```

### Configuration Issues
```bash
# Validate JSON format
cat local.settings.json | python -m json.tool

# Check required fields exist
grep -E "(AZURE_OPENAI_KEY|ATLASSIAN_USERNAME)" local.settings.json
```

### Function Loading Issues
```bash
# Check imports manually
python -c "import azure.functions; print('Azure Functions OK')"

# Start with verbose output
func start --verbose
```

🛠️ **For detailed troubleshooting see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## 📈 Performance & Scaling

### Async Performance Features
- **⚡ Concurrent Processing**: 3-5x faster for large batches
- **📦 Intelligent Batching**: Optimized memory and API usage
- **⏱️ Adaptive Timeouts**: Smart scaling based on workload size
- **🛡️ Rate Limiting**: Built-in API protection with exponential backoff

### Configuration Variables
```bash
# Optimize for your workload
MAX_CONCURRENT_AI_CALLS=5      # Concurrent Azure OpenAI calls
AI_BATCH_SIZE=10               # Issues per batch
AZURE_OPENAI_REQUEST_TIMEOUT=60 # Request timeout in seconds
```

📊 **See [ASYNC_PERFORMANCE_GUIDE.md](ASYNC_PERFORMANCE_GUIDE.md) for optimization details**

---

## 🚀 Deployment

### Quick Deploy to Azure
1. **Install VS Code Azure Extensions**
2. **Sign in to Azure in VS Code** (`Ctrl+Shift+P` → `Azure: Sign In`)
3. **Create Function App** (Right-click subscription → Create Function App)
4. **Deploy Code** (Right-click Function App → Deploy to Function App)
5. **Configure Production Settings** in Azure Portal

🚀 **See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions**

---

## 🤝 Contributing

### Development Workflow
1. **Setup**: Virtual environment + dependencies
2. **Configure**: Create `local.settings.json`
3. **Test**: Run test suite - see **[TESTING.md](TESTING.md)** for complete guide
4. **Develop**: Make changes
5. **Deploy**: Test locally then deploy to Azure

### Testing Quick Reference
```bash
# No configuration required - start here
python test_enhanced.py

# Full test suite (requires local.settings.json)
python test_functions.py
python test_ai_analysis.py

# VS Code Test Explorer: Click flask icon → run tests
# See TESTING.md for 7 comprehensive test suites
```

🧪 **Complete testing guide**: **[TESTING.md](TESTING.md)** covers all 7 test files, VS Code integration, and troubleshooting

### Best Practices
- Always work in virtual environments
- Test with both AI models (GPT-4 and o4-mini) if available
- Validate Confluence integration in test space
- Monitor token usage and costs
- Update documentation for new features

---

## 📞 Support

### Getting Help
- **📖 Documentation**: Check the relevant guide above
- **🐛 Issues**: File issues with detailed error messages and environment info
- **💡 Features**: Suggest improvements via issues or PRs

### Useful Commands
```bash
# Full diagnostics
python test_enhanced.py && python test_functions.py

# Check environment
echo "Python: $(python --version)"
echo "Azure Functions: $(func --version)"
echo "Virtual Env: $VIRTUAL_ENV"
```

---

**🎉 Ready to get started? See [QUICK_START.md](QUICK_START.md) for 5-minute setup!**
