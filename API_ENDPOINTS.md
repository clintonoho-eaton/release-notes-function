# Available API Endpoints

## Overview

The Azure Functions API provides multiple endpoints for generating AI-powered release notes from Jira issues.

## Endpoint Categories

### 1. Environment Configuration Endpoints
Uses credentials from `local.settings.json` or Azure Function App Settings.

### 2. Custom Configuration Endpoints  
Accepts credentials in request body for enhanced security and flexibility.

### 3. Utility Endpoints
Health checks and diagnostics.

---

## Environment Configuration Endpoints

### Batch Processing by Issue Type
**Endpoint**: `PUT /api/release-notes/{proj}/{fixver}/{issuetype}`
**Endpoint**: `PUT /api/release-notes/{proj}/{fixver}/{issuetype}/{max_results}`

**Parameters**:
- `proj`: Project key (e.g., "IP", "PLATFORM")
- `fixver`: Fix version (e.g., "1.0.0", "Release 2.1")
- `issuetype`: Issue type ("Bug", "Epic", "Story", "Task")
- `max_results`: Maximum number of issues to process (optional, default: 25)

**Examples**:
```bash
# Process up to 25 bugs for version 1.0.0
curl -X PUT "http://localhost:7071/api/release-notes/IP/1.0.0/Bug"

# Process up to 5 epics for version 2.1.0
curl -X PUT "http://localhost:7071/api/release-notes/PLATFORM/2.1.0/Epic/5"
```

### Single Issue Processing
**Endpoint**: `PUT /api/release-notes/{proj}/{issue_key}`

**Parameters**:
- `proj`: Project key (e.g., "IP")
- `issue_key`: Specific issue key (e.g., "IP-51180")

**Example**:
```bash
# Process a specific issue
curl -X PUT "http://localhost:7071/api/release-notes/IP/IP-51180"
```

---

## Custom Configuration Endpoints

### Batch Processing with Custom Config
**Endpoint**: `POST /api/release-notes/custom`

**Request Body**:
```json
{
  "jql": "project = IP AND fixversion = '1.0.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 25,
  "atlassian_config": {
    "username": "your-email@company.com",
    "api_key": "your-api-key",
    "instance_url": "https://your-company.atlassian.net",
    "confluence_space": "YourSpace",
    "confluence_parent": "123456789"
  }
}
```

**Local Development** (simplified, no atlassian_config needed):
```json
{
  "jql": "project = IP AND fixversion = '1.0.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 25
}
```

### Single Issue with Custom Config
**Endpoint**: `POST /api/release-notes/single`

**Request Body**:
```json
{
  "issue_key": "IP-51180",
  "atlassian_config": {
    "username": "your-email@company.com",
    "api_key": "your-api-key",
    "instance_url": "https://your-company.atlassian.net",
    "confluence_space": "YourSpace",
    "confluence_parent": "123456789"
  }
}
```

**Local Development** (simplified):
```json
{
  "issue_key": "IP-51180"
}
```

---

## Utility Endpoints

### Health Check
**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "services": {
    "azure_openai": "connected",
    "jira": "connected",
    "confluence": "connected"
  },
  "model_config": {
    "deployment": "gpt-4o",
    "parameters": ["temperature", "top_p", "presence_penalty", "frequency_penalty"]
  }
}
```

### Basic Test
**Endpoint**: `GET /api/test`

**Response**:
```json
{
  "message": "Function app is running successfully",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Sample Extension
**Endpoint**: `GET /api/extensions/sample`

### Diagnostics
**Endpoint**: `PUT /api/diagnostics/release-notes/{proj}/{fixver}/{issuetype}`

Returns detailed processing information without creating Confluence pages.

---

## Response Format

### Success Response
```json
{
  "status": "success",
  "processing_time": 15.3,
  "details": [
    "Successfully fetched 5 issues from Jira",
    "Generated AI analysis for all issues",
    "Created 3 Confluence pages"
  ],
  "warnings": [],
  "confluence_pages": {
    "created": [
      {
        "title": "Release 1.0 - Bug Fixes",
        "id": "987654321",
        "url": "https://company.atlassian.net/wiki/pages/viewpage.action?pageId=987654321"
      }
    ],
    "updated": [],
    "errors": []
  }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Unauthorized access to Jira API. Please check your credentials.",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## Local Development Features

### Automatic Fallback
When running locally, custom configuration endpoints automatically fall back to `local.settings.json` if:
- `atlassian_config` is missing from request body
- Individual fields are missing from `atlassian_config`

### Environment Detection
- **Local**: Detected by absence of `WEBSITE_SITE_NAME` environment variable
- **Production**: Detected by presence of `WEBSITE_SITE_NAME` environment variable

### Simplified Testing
For local development, you can use minimal request bodies:

```bash
# Batch processing
curl -X POST "http://localhost:7071/api/release-notes/custom" \
  -H "Content-Type: application/json" \
  -d '{"jql": "project = IP AND issuetype = Bug", "max_results": 5}'

# Single issue
curl -X POST "http://localhost:7071/api/release-notes/single" \
  -H "Content-Type: application/json" \
  -d '{"issue_key": "IP-51180"}'
```

---

## Configuration Priority

### Custom Configuration Endpoints
1. **Request Body** - Values in `atlassian_config` object (highest priority)
2. **Environment Variables** - Values from `local.settings.json` (local development only)
3. **Error** - If required values are missing from both sources

### Required Configuration Fields

#### Production/Cloud Environment
All fields required in `atlassian_config`:
- `username` - Your Atlassian email
- `api_key` - Your Atlassian API token
- `instance_url` - Your Atlassian instance URL
- `confluence_space` - Target Confluence space key
- `confluence_parent` - Parent page ID

#### Local Development Environment
All fields optional in request body - will fall back to environment variables:
- `ATLASSIAN_USERNAME`
- `ATLASSIAN_API_KEY`
- `ATLASSIAN_URL` or `ATLASSIAN_INSTANCE_URL`
- `CONFLUENCE_SPACE`
- `CONFLUENCE_PARENT`

---

## Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid credentials) |
| 500 | Internal Server Error |
| 502 | Bad Gateway (Jira/Confluence API error) |
| 504 | Gateway Timeout (processing timeout) |

---

## Usage Examples

See `EXAMPLE_RESPONSES.md` for detailed request/response examples with real data.

## Performance Configuration

See `ASYNC_PERFORMANCE_GUIDE.md` for optimizing concurrent processing settings.
