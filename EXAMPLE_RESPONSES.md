# Example API Responses - Custom Configuration

This document shows example responses from the new custom configuration API endpoints.

## Successful Batch Processing Response

**Request:**
```bash
POST /api/release-notes/custom
Content-Type: application/json

{
  "jql": "project = IP AND fixversion = 'Release 1.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 3,
  "atlassian_config": {
    "username": "developer@company.com",
    "api_key": "ATATT3xFfGF0...",
    "instance_url": "https://company.atlassian.net",
    "confluence_space": "IoTPlatform",
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
  "max_results": 3,
  "confluence_space": "IoTPlatform",
  "confluence_parent": "623280329",
  "details": "Successfully processed JQL query with custom Atlassian configuration",
  "confluence_pages": {
    "created": [
      {
        "title": "Release 1.0 - Bug Fixes",
        "id": "987654321",
        "url": "https://company.atlassian.net/wiki/pages/viewpage.action?pageId=987654321",
        "space": "IoTPlatform",
        "parent_id": "623280329"
      }
    ],
    "updated": [],
    "errors": []
  }
}
```

## Successful Single Issue Response

**Request:**
```bash
POST /api/release-notes/single
Content-Type: application/json

{
  "issue_key": "IP-51180",
  "atlassian_config": {
    "username": "developer@company.com",
    "api_key": "ATATT3xFfGF0...",
    "instance_url": "https://company.atlassian.net",
    "confluence_space": "IoTPlatform",
    "confluence_parent": "623280329"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "issue_key": "IP-51180",
  "confluence_space": "IoTPlatform",
  "confluence_parent": "623280329",
  "processing_time": 12.7,
  "details": [
    "Successfully analyzed issue IP-51180",
    "Generated AI-powered release notes",
    "Created Confluence page successfully"
  ],
  "warnings": [],
  "confluence_pages": {
    "created": [
      {
        "title": "IP-51180 - Authentication timeout in mobile app",
        "id": "111222333",
        "url": "https://company.atlassian.net/wiki/pages/viewpage.action?pageId=111222333",
        "space": "IoTPlatform",
        "parent_id": "623280329"
      }
    ],
    "updated": [],
    "errors": []
  }
}
```

## Validation Error Examples

### Missing Required Fields

**Request:**
```json
{
  "jql": "project = IP AND issuetype = Bug"
  // Missing atlassian_config
}
```

**Response:**
```json
{
  "status": "error",
  "message": "Missing required fields: atlassian_config"
}
```

### Incomplete Atlassian Configuration

**Request:**
```json
{
  "jql": "project = IP AND issuetype = Bug",
  "atlassian_config": {
    "username": "developer@company.com",
    "api_key": "ATATT3xFfGF0..."
    // Missing instance_url, confluence_space, confluence_parent
  }
}
```

**Response:**
```json
{
  "status": "error",
  "message": "Missing required Atlassian configuration fields: instance_url, confluence_space, confluence_parent",
  "required_fields": [
    "username",
    "api_key", 
    "instance_url",
    "confluence_space",
    "confluence_parent"
  ]
}
```

### Invalid Issue Key Format

**Request:**
```json
{
  "issue_key": "INVALID-KEY-FORMAT",
  "atlassian_config": { ... }
}
```

**Response:**
```json
{
  "status": "error",
  "message": "Invalid issue key format: INVALID-KEY-FORMAT. Expected format: PROJECT-NUMBER (e.g., IP-51180)"
}
```

## Authentication Error Examples

### Invalid Credentials

**Response:**
```json
{
  "status": "error",
  "message": "Unauthorized access to Jira/Confluence API. Please check your credentials."
}
```

### Insufficient Permissions

**Response:**
```json
{
  "status": "error",
  "message": "Jira API error: You do not have permission to access project IP"
}
```

## Processing Error Examples

### Issue Not Found

**Response:**
```json
{
  "status": "error",
  "issue_key": "IP-99999",
  "message": "Issue IP-99999 not found or you don't have permission to view it",
  "warnings": []
}
```

### Confluence Space Access Error

**Response:**
```json
{
  "status": "success",
  "issue_key": "IP-51180",
  "confluence_space": "RESTRICTED",
  "confluence_parent": "623280329",
  "processing_time": 8.2,
  "details": [
    "Successfully analyzed issue IP-51180"
  ],
  "warnings": [
    "Failed to create Confluence page: Access denied to space RESTRICTED"
  ],
  "confluence_pages": {
    "created": [],
    "updated": [],
    "errors": [
      {
        "error": "Access denied",
        "space": "RESTRICTED",
        "message": "User does not have write permission to the specified Confluence space"
      }
    ]
  }
}
```

## Timeout Error

**Response:**
```json
{
  "status": "error",
  "message": "Processing timed out after 900 seconds. This may be due to high API load or too many concurrent requests. Please try with fewer issues or reduce concurrency settings."
}
```

## Rate Limiting Error

**Response:**
```json
{
  "status": "error",
  "message": "Jira API error: Too Many Requests - Rate limit exceeded. Please wait before making additional requests."
}
```

## Key Differences from Environment Configuration

1. **Request Method**: POST instead of PUT
2. **Configuration Source**: Request body instead of environment variables  
3. **Flexibility**: Each request can use different Atlassian instances/spaces
4. **Security**: No persistent storage of credentials
5. **User-specific**: Each user provides their own credentials

## Response Field Descriptions

| Field | Description |
|-------|-------------|
| `status` | Either "success" or "error" |
| `jql` | The JQL query that was processed |
| `issue_key` | The specific issue key (single issue endpoint) |
| `confluence_space` | The Confluence space used |
| `confluence_parent` | The parent page ID used |
| `processing_time` | Time taken to process in seconds |
| `details` | Array of success messages |
| `warnings` | Array of warning messages |
| `confluence_pages.created` | Array of successfully created pages |
| `confluence_pages.updated` | Array of updated pages |
| `confluence_pages.errors` | Array of page creation errors |

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid credentials) |
| 500 | Internal Server Error |
| 502 | Bad Gateway (Jira/Confluence API error) |
| 504 | Gateway Timeout (processing timeout) |

## Local Development Examples - ✅ WORKING

### Simplified Request (No atlassian_config)

When running locally, you can omit the `atlassian_config` and the system will use values from `local.settings.json`:

**Request:**
```bash
POST /api/release-notes/custom
Content-Type: application/json

{
  "jql": "project = IP AND fixversion = 'Release 1.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 3
}
```

**Response:**
```json
{
  "status": "success",
  "jql": "project = IP AND fixversion = 'Release 1.0' AND issuetype = Bug",
  "issue_type": "Bug",
  "max_results": 3,
  "confluence_space": "IoTPlatform",
  "confluence_parent": "623280329",
  "details": "Successfully processed JQL query with custom Atlassian configuration",
  "confluence_pages": {
    "created": [],
    "updated": [],
    "errors": []
  }
}
```

### Partial Configuration with Fallback - ✅ WORKING

You can also provide partial configuration and missing fields will fall back to environment variables:

**Request:**
```bash
POST /api/release-notes/custom
Content-Type: application/json

{
  "jql": "project = IP AND issuetype = Bug",
  "max_results": 5,
  "atlassian_config": {
    "confluence_space": "CUSTOM_SPACE"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "jql": "project = IP AND issuetype = Bug",
  "max_results": 5,
  "confluence_space": "CUSTOM_SPACE",
  "confluence_parent": "623280329",
  "details": "Successfully processed JQL query with custom Atlassian configuration",
  "confluence_pages": {
    "created": [],
    "updated": [],
    "errors": []
  }
}
```
