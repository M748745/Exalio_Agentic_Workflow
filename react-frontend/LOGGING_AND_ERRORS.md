# Logging and Error Handling Documentation

## Overview

This document describes the centralized logging and error handling infrastructure implemented for the Agentic Workflow Builder.

## Features

### Logging Service

The logging service provides:

- **Multiple Output Formats**
  - JSON logs for machine parsing (`workflow_engine.log`)
  - Human-readable logs (`workflow_engine.readable.log`)
  - Error-only logs (`workflow_engine.error.log`)
  - Colored console output for development

- **Automatic Log Rotation**
  - Configurable max file size (default: 10MB)
  - Configurable backup count (default: 5 files)

- **Structured Logging**
  - JSON format with consistent fields
  - Contextual metadata (workflow_id, execution_id, node_id, etc.)
  - Request tracking with request IDs
  - Execution timing

### Error Handling

Custom error classes with:

- **Machine-readable error codes**
- **HTTP status codes**
- **Contextual information**
- **Hierarchical error types**

## Usage

### Basic Logging

```python
from services.logging_service import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Processing workflow")
logger.warning("Workflow taking longer than expected")
logger.error("Workflow execution failed", exc_info=True)
```

### Context Logger

Use context loggers to automatically include workflow/execution/node IDs:

```python
from services.logging_service import get_context_logger

# Create context logger
context_logger = get_context_logger(
    __name__,
    workflow_id="workflow_123",
    execution_id="exec_456",
    node_id="node_789"
)

# All logs will include the context
context_logger.info("Starting node execution")  # Includes workflow_id, execution_id, node_id
context_logger.error("Node failed", exc_info=True)  # Includes full context + exception
```

### Custom Error Classes

```python
from backend.errors import (
    WorkflowNotFoundError,
    NodeExecutionError,
    DataValidationError,
    APIError
)

# Raise custom errors
raise WorkflowNotFoundError(workflow_id="workflow_123")

# Node execution error with context
raise NodeExecutionError(
    node_id="node_1",
    node_type="api_call",
    message="API request timed out",
    original_error=timeout_exception
)

# Data validation error
raise DataValidationError(
    message="Invalid input format",
    validation_errors=[
        {"field": "email", "error": "Invalid email format"},
        {"field": "age", "error": "Must be positive"}
    ]
)
```

### In API Endpoints

```python
from backend.errors import WorkflowNotFoundError, error_to_response

@app.route('/api/workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    try:
        workflow = workflow_storage.load_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)

        logger.info(f"Retrieved workflow {workflow_id}")
        return jsonify(workflow)

    except WorkflowError as e:
        # Automatically handled by Flask error handler
        raise

    except Exception as e:
        logger.error(f"Unexpected error retrieving workflow", exc_info=True)
        raise
```

## Error Types

### Workflow Errors

- `WorkflowNotFoundError` - Workflow doesn't exist (404)
- `WorkflowValidationError` - Invalid workflow definition (400)
- `WorkflowExecutionError` - Workflow execution failed (500)
- `WorkflowVersionError` - Version conflict (400)
- `WorkflowImportError` - Import failed (400)

### Node Errors

- `NodeNotFoundError` - Node doesn't exist (404)
- `NodeConfigurationError` - Invalid node config (400)
- `NodeExecutionError` - Node execution failed (500)
- `NodeTimeoutError` - Node timed out (408)

### Data Errors

- `DataValidationError` - Invalid data format (400)
- `DataTransformationError` - Transformation failed (500)
- `DataConnectionError` - Database/API connection failed (503)

### Integration Errors

- `APIError` - External API call failed (502)
- `AuthenticationError` - Auth failed (401)
- `RateLimitError` - Rate limit exceeded (429)

### Memory Errors

- `VectorStoreError` - Vector store operation failed (500)
- `CacheError` - Cache operation failed (500)

### Template Errors

- `TemplateNotFoundError` - Template doesn't exist (404)

## Log Locations

All logs are stored in `backend/logs/`:

- `workflow_engine.log` - All logs in JSON format
- `workflow_engine.error.log` - Error logs only in JSON format
- `workflow_engine.readable.log` - Human-readable format

## JSON Log Format

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "flask_app",
  "message": "Request completed",
  "module": "flask_app",
  "function": "after_request",
  "line": 85,
  "request_id": "req_1705318245123",
  "method": "GET",
  "path": "/api/workflows/123",
  "status_code": 200,
  "duration_ms": 45,
  "workflow_id": "workflow_123",
  "execution_id": "exec_456"
}
```

## Configuration

### Logging Configuration

Modify `backend/services/logging_service.py`:

```python
logging_service = LoggingService(
    log_dir="backend/logs",
    app_name="workflow_engine",
    console_level="INFO",      # Console verbosity
    file_level="DEBUG",        # File verbosity
    max_bytes=10 * 1024 * 1024,  # 10MB per file
    backup_count=5             # Keep 5 backup files
)
```

### Error Response Format

All errors return consistent JSON:

```json
{
  "error": true,
  "error_code": "WORKFLOW_NOT_FOUND",
  "message": "Workflow not found: workflow_123",
  "status_code": 404,
  "context": {
    "workflow_id": "workflow_123"
  }
}
```

## Request Tracking

Every API request gets:

1. **Unique request ID** - `req_<timestamp>`
2. **Automatic logging** - Start and completion
3. **Timing information** - Duration in milliseconds
4. **Context propagation** - Request ID in all logs

Example logs for a request:

```
[INFO] Incoming request: GET /api/workflows/123 [request_id=req_1705318245123]
[INFO] Retrieved workflow 123 [request_id=req_1705318245123, workflow_id=workflow_123]
[INFO] Request completed: GET /api/workflows/123 - 200 [request_id=req_1705318245123, duration_ms=45]
```

## Best Practices

### 1. Use Appropriate Log Levels

- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Something unexpected but not an error
- `ERROR` - Error occurred but application can continue
- `CRITICAL` - Severe error, application may be unable to continue

### 2. Include Context

```python
# Good
logger.info(
    f"Processing workflow {workflow_id}",
    extra={'workflow_id': workflow_id, 'node_count': len(nodes)}
)

# Better - use context logger
context_logger = get_context_logger(__name__, workflow_id=workflow_id)
context_logger.info(f"Processing {len(nodes)} nodes")
```

### 3. Log Exceptions Properly

```python
try:
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)  # Includes full traceback
    raise
```

### 4. Use Custom Errors

```python
# Good
if not workflow:
    raise WorkflowNotFoundError(workflow_id)

# Avoid
if not workflow:
    raise Exception(f"Workflow {workflow_id} not found")
```

### 5. Structured Data

```python
# Good - structured
logger.info("Workflow completed", extra={
    'workflow_id': workflow_id,
    'duration_ms': duration,
    'node_count': node_count,
    'success_rate': success_rate
})

# Avoid - unstructured
logger.info(f"Workflow {workflow_id} completed in {duration}ms with {node_count} nodes")
```

## Monitoring and Debugging

### Search Logs by Request ID

```bash
# Find all logs for a specific request
grep "req_1705318245123" backend/logs/workflow_engine.log
```

### Search by Workflow/Execution

```bash
# All logs for a workflow
grep "workflow_123" backend/logs/workflow_engine.log

# Parse JSON logs
cat backend/logs/workflow_engine.log | jq 'select(.workflow_id == "workflow_123")'
```

### View Errors Only

```bash
# Error log file
tail -f backend/logs/workflow_engine.error.log

# Or filter main log
cat backend/logs/workflow_engine.log | jq 'select(.level == "ERROR")'
```

### Real-time Monitoring

```bash
# Watch all logs
tail -f backend/logs/workflow_engine.readable.log

# Watch errors only
tail -f backend/logs/workflow_engine.error.log
```

## Integration with Analytics

The logging system integrates with the analytics service:

- Node execution errors are tracked in analytics
- Retry attempts are logged with full context
- Execution timing is captured automatically
- Error patterns can be analyzed via analytics API

## Future Enhancements

Potential improvements:

1. **Remote logging** - Send logs to external services (Elasticsearch, Datadog)
2. **Log aggregation** - Centralized logging for distributed deployments
3. **Alert integration** - Automatic alerts on error patterns
4. **Performance metrics** - APM integration for detailed performance tracking
5. **Log sampling** - Reduce log volume in high-traffic scenarios
