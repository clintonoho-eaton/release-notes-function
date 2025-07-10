# Async Performance Configuration Guide

This document describes the asynchronous improvements implemented to optimize Azure OpenAI API calls for processing large numbers of Jira issues.

## Key Improvements

### 1. Concurrent Processing
- **Batch Processing**: Issues are processed in configurable batches to manage memory and API rate limits
- **Semaphore Control**: Uses asyncio semaphores to limit concurrent Azure OpenAI API calls
- **Async/Await**: Full async implementation throughout the processing pipeline

### 2. Performance Configuration

The following environment variables can be configured to optimize performance:

#### Core Async Settings
- `MAX_CONCURRENT_AI_CALLS` (default: 5) - Maximum number of concurrent Azure OpenAI API calls
- `AI_BATCH_SIZE` (default: 10) - Number of issues to process in each batch
- `AZURE_OPENAI_REQUEST_TIMEOUT` (default: 60) - Timeout in seconds for individual API calls

#### HTTP Client Settings
- `AZURE_OPENAI_MAX_CONNECTIONS` (default: 20) - Maximum total HTTP connections
- `AZURE_OPENAI_MAX_CONNECTIONS_PER_HOST` (default: 10) - Maximum connections per host

### 3. Timeout Configuration
- **Function Timeout**: Increased to 20 minutes in `host.json` to handle large batches
- **Request Timeout**: Configurable per-request timeout with proper error handling
- **Processing Timeout**: Intelligent timeout scaling based on the number of issues

## Recommended Settings by Use Case

### Small Batches (1-10 issues)
```env
MAX_CONCURRENT_AI_CALLS=3
AI_BATCH_SIZE=5
AZURE_OPENAI_REQUEST_TIMEOUT=60
```

### Medium Batches (10-25 issues)
```env
MAX_CONCURRENT_AI_CALLS=5
AI_BATCH_SIZE=10
AZURE_OPENAI_REQUEST_TIMEOUT=60
```

### Large Batches (25-50 issues)
```env
MAX_CONCURRENT_AI_CALLS=7
AI_BATCH_SIZE=15
AZURE_OPENAI_REQUEST_TIMEOUT=90
```

### Very Large Batches (50+ issues)
```env
MAX_CONCURRENT_AI_CALLS=10
AI_BATCH_SIZE=20
AZURE_OPENAI_REQUEST_TIMEOUT=120
```

## Performance Benefits

### Before (Sequential Processing)
- 50 bugs × 3-5 seconds per call = 150-250 seconds
- Single API call at a time
- No parallelization

### After (Concurrent Processing)
- 50 bugs ÷ 5 concurrent calls = ~10 batches
- Each batch processed in parallel
- Estimated time: 30-60 seconds for 50 bugs

## Rate Limiting and Error Handling

### Built-in Protections
1. **Semaphore Control**: Prevents overwhelming the Azure OpenAI service
2. **Batch Delays**: Small delays between batches to respect rate limits
3. **Retry Logic**: Exponential backoff for transient failures
4. **Timeout Handling**: Graceful handling of API timeouts

### Error Recovery
- Individual issue failures don't stop the entire batch
- Detailed logging for troubleshooting
- Comprehensive error reporting in function responses

## Monitoring and Logging

### Performance Metrics
- Batch processing progress
- Concurrent operation counts
- Processing time per issue and overall
- Success/failure rates

### Log Levels
- `INFO`: Batch progress and completion status
- `DEBUG`: Individual issue processing details
- `ERROR`: Failures and timeouts with stack traces

## Azure Functions Configuration

### host.json Changes
- Increased `functionTimeout` to `00:20:00` (20 minutes)
- Enhanced logging configuration for better monitoring

### Deployment Considerations
- Consider using Premium or Dedicated plans for consistent performance
- Monitor Application Insights for performance metrics
- Set appropriate scaling rules based on expected load

## Best Practices

1. **Start Conservative**: Begin with lower concurrency settings and gradually increase
2. **Monitor Rate Limits**: Watch for 429 (Too Many Requests) responses from Azure OpenAI
3. **Adjust Batch Size**: Larger batches use more memory but reduce overhead
4. **Use Appropriate Timeouts**: Balance between responsiveness and allowing enough time for processing
5. **Test Thoroughly**: Performance can vary based on issue complexity and Azure OpenAI model load

## Troubleshooting

### Common Issues
1. **TimeoutError**: Reduce batch size or increase timeout
2. **Rate Limiting**: Reduce concurrent calls or add delays
3. **Memory Issues**: Reduce batch size for large issues with lots of content
4. **API Quota**: Monitor Azure OpenAI usage and quota limits

### Debug Mode
Set logging level to `DEBUG` to see detailed processing information:
```env
FUNCTIONS_WORKER_LOG_LEVEL=DEBUG
```

## Migration Notes

The async implementation is backward compatible. Existing configurations will continue to work with default async settings applied automatically.
