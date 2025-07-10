# API Usage with Custom Atlassian Configuration

This document describes how to use the Azure Function API with custom Atlassian configuration provided in the request body instead of reading from environment variables.

## Overview

The API now supports two modes:
1. **Environment Configuration Mode** (existing endpoints) - Reads Atlassian configuration from environment variables
2. **Custom Configuration Mode** (new endpoints) - Accepts Atlassian configuration in the request body with fallback to environment variables for local development

## Local Development Fallback

For local development convenience, the custom configuration endpoints will automatically fall back to environment variables from `local.settings.json` if the `atlassian_config` fields are not provided in the request body.

**Detection Logic:**
- **Local Development**: When `AZURE_FUNCTIONS_ENVIRONMENT` is not set
- **Production/Cloud**: When `AZURE_FUNCTIONS_ENVIRONMENT` is set

**Fallback Behavior:**
- If `atlassian_config` is missing or incomplete in the request body
- AND you're running in local development mode
- THEN the system will use values from `local.settings.json`

This means for local development, you can use simplified requests like:
```json
{
  "jql": "project = IP AND issuetype = Bug"
  // No atlassian_config needed - will use local.settings.json
}
```

## New API Endpoints

### 1. Custom Configuration Batch Processing

**Endpoint:** `POST /api/release-notes/custom`

**Description:** Process multiple issues with custom Atlassian configuration provided in the request body.

**Request Body:**
```json
{
  "jql": "project = IP AND fixversion = 'Release 1.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 25,
  "atlassian_config": {
    "username": "your-email@company.com",
    "api_key": "ATATT3xFfGF0SDCM325pp1J5kWiu_qOzGK41oIFx0P47ePIvKlMCoOrx9LZaE1stUAXCFZO5cLYUm0kzS3KREym9yZN6Hm7-cBlMGoYZMvs4uVfqWJaac3YhabYzcbF-bJA3uqjbL54p7yVp8FgO49WhtDo3R3ttOr6jaIXwGh7EOVTIRgmm_xg=153A7477",
    "instance_url": "https://your-company.atlassian.net",
    "confluence_space": "YourProjectSpace",
    "confluence_parent": "623280329"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "jql": "project = IP AND fixversion = 'Release 1.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 25,
  "confluence_space": "YourProjectSpace",
  "confluence_parent": "623280329",
  "details": "Successfully processed JQL query with custom Atlassian configuration",
  "confluence_pages": {
    "created": [
      {
        "title": "Release Notes - Bug Fixes",
        "id": "987654321",
        "url": "https://your-company.atlassian.net/wiki/pages/viewpage.action?pageId=987654321"
      }
    ],
    "updated": [],
    "errors": []
  }
}
```

### 2. Custom Configuration Single Issue Processing

**Endpoint:** `POST /api/release-notes/single`

**Description:** Process a single issue with custom Atlassian configuration provided in the request body.

**Request Body:**
```json
{
  "issue_key": "IP-51180",
  "atlassian_config": {
    "username": "your-email@company.com",
    "api_key": "ATATT3xFfGF0SDCM325pp1J5kWiu_qOzGK41oIFx0P47ePIvKlMCoOrx9LZaE1stUAXCFZO5cLYUm0kzS3KREym9yZN6Hm7-cBlMGoYZMvs4uVfqWJaac3YhabYzcbF-bJA3uqjbL54p7yVp8FgO49WhtDo3R3ttOr6jaIXwGh7EOVTIRgmm_xg=153A7477",
    "instance_url": "https://your-company.atlassian.net",
    "confluence_space": "YourProjectSpace",
    "confluence_parent": "623280329"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "issue_key": "IP-51180",
  "confluence_space": "YourProjectSpace",
  "confluence_parent": "623280329",
  "processing_time": 15.3,
  "details": ["Successfully analyzed issue IP-51180", "Created Confluence page"],
  "warnings": [],
  "confluence_pages": {
    "created": [
      {
        "title": "IP-51180 - Fix authentication bug",
        "id": "987654321",
        "url": "https://your-company.atlassian.net/wiki/pages/viewpage.action?pageId=987654321"
      }
    ],
    "updated": [],
    "errors": []
  }
}
```

### Local Development Examples

When running locally with `local.settings.json` configured, you can omit the `atlassian_config`:

**Simplified Batch Request (Local Development):**
```json
{
  "jql": "project = IP AND fixversion = 'Release 1.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 25
}
```

**Simplified Single Issue Request (Local Development):**
```json
{
  "issue_key": "IP-51180"
}
```

**Local Development Response:**
```json
{
  "status": "success",
  "jql": "project = IP AND fixversion = 'Release 1.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 25,
  "confluence_space": "YourProjectSpace",
  "confluence_parent": "123456789",
  "details": "Successfully processed JQL query with custom Atlassian configuration",
  "local_development": true,
  "config_source": "environment_fallback"
}
```

### Production/Cloud Examples

In production or cloud environments, you must provide the full `atlassian_config`:

## Required Configuration Fields

When using the custom configuration endpoints:

### Production/Cloud Environment
You **must** provide all of the following fields in the `atlassian_config` object:

| Field | Description | Example |
|-------|-------------|---------|
| `username` | Your Atlassian username (email) | `"your-email@company.com"` |
| `api_key` | Your Atlassian API token | `"ATATT3xFfGF0..."` |
| `instance_url` | Your Atlassian instance URL | `"https://your-company.atlassian.net"` |
| `confluence_space` | Target Confluence space key | `"PROJECTSPACE"` |
| `confluence_parent` | Parent page ID for created pages | `"623280329"` |

### Local Development Environment
Configuration fields are **optional** in the request body. Missing fields will fall back to environment variables from `local.settings.json`:

| Request Field | Environment Variable | Fallback Order |
|---------------|---------------------|----------------|
| `username` | `ATLASSIAN_USERNAME` | Request → Environment |
| `api_key` | `ATLASSIAN_API_KEY` | Request → Environment |
| `instance_url` | `ATLASSIAN_INSTANCE_URL` or `ATLASSIAN_URL` | Request → Environment |
| `confluence_space` | `CONFLUENCE_SPACE` | Request → Environment |
| `confluence_parent` | `CONFLUENCE_PARENT` | Request → Environment |

## Security Benefits

### 1. No Configuration Storage
- Atlassian credentials are not stored in environment variables
- Credentials are provided per-request basis
- No persistent storage of sensitive information

### 2. User-Specific Credentials
- Each API call uses the user's own Atlassian credentials
- Better access control and audit trails
- Follows principle of least privilege

### 3. Flexible Access
- Different users can target different Confluence spaces
- Different parent pages per user/project
- No shared credentials across users

## Azure OpenAI Configuration

Note that Azure OpenAI configuration is still read from environment variables:
- `AZURE_OPENAI_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_CHAT_COMPLETIONS_API_VERSION`
- `AZURE_OPENAI_GPT_DEPLOYMENT`

This allows the Azure Function to use a centralized AI service while allowing user-specific Atlassian access.

## Error Handling

### Authentication Errors (401)
```json
{
  "status": "error",
  "message": "Unauthorized access to Jira/Confluence API. Please check your credentials."
}
```

### Missing Configuration (400) - Production
```json
{
  "status": "error",
  "message": "Missing required Atlassian configuration fields: username, api_key. Please provide all required fields in the atlassian_config object",
  "required_fields": ["username", "api_key", "instance_url", "confluence_space", "confluence_parent"],
  "local_development": false
}
```

### Missing Configuration (400) - Local Development
```json
{
  "status": "error",
  "message": "Missing required Atlassian configuration fields: username, api_key. For local development, provide values in request body or set environment variables in local.settings.json",
  "required_fields": ["username", "api_key", "instance_url", "confluence_space", "confluence_parent"],
  "local_development": true
}
```

### Invalid Issue Key (400)
```json
{
  "status": "error",
  "message": "Invalid issue key format: INVALID-KEY. Expected format: PROJECT-NUMBER (e.g., IP-51180)"
}
```

## Example Usage with cURL

### Batch Processing
```bash
curl -X POST "https://your-function-app.azurewebsites.net/api/release-notes/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = IP AND fixversion = \"Release 1.0\" AND issuetype = Bug",
    "issue_type": "Bug",
    "max_results": 10,
    "atlassian_config": {
      "username": "your-email@company.com",
      "api_key": "your-atlassian-api-key",
      "instance_url": "https://your-company.atlassian.net",
      "confluence_space": "PROJECTSPACE",
      "confluence_parent": "623280329"
    }
  }'
```

### Single Issue Processing
```bash
curl -X POST "https://your-function-app.azurewebsites.net/api/release-notes/single" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_key": "IP-51180",
    "atlassian_config": {
      "username": "your-email@company.com",
      "api_key": "your-atlassian-api-key",
      "instance_url": "https://your-company.atlassian.net",
      "confluence_space": "PROJECTSPACE",
      "confluence_parent": "623280329"
    }
  }'
```

## Migration from Environment Configuration

If you're currently using the environment-based configuration endpoints, you can migrate by:

1. **Identify your current configuration** from `local.settings.json` or Azure Function App Settings:
   - `ATLASSIAN_USERNAME`
   - `ATLASSIAN_API_KEY`
   - `ATLASSIAN_INSTANCE_URL`
   - `CONFLUENCE_SPACE`
   - `CONFLUENCE_PARENT`

2. **Update your API calls** to use the new endpoints with the configuration in the request body

3. **Test thoroughly** with the new endpoints before removing environment variables

4. **Remove sensitive environment variables** once migration is complete

## Best Practices

1. **Secure API Key Storage**: Store Atlassian API keys securely in your application (e.g., Azure Key Vault)
2. **Request Validation**: Always validate the response status before processing results
3. **Error Handling**: Implement proper error handling for authentication and API failures
4. **Rate Limiting**: Be mindful of Atlassian API rate limits when making multiple requests
5. **Logging**: Monitor API usage and errors for troubleshooting

## Limitations

1. **Azure OpenAI**: Still requires environment configuration for the AI service
2. **Function App Settings**: Other application settings (timeouts, batch sizes) are still environment-based
3. **Backwards Compatibility**: Existing environment-based endpoints remain available
