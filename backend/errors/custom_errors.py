"""
Custom Error Classes
Defines application-specific exceptions with error codes and context
"""

from typing import Any, Dict, Optional


class WorkflowError(Exception):
    """Base exception for all workflow-related errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize workflow error

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            'error': True,
            'error_code': self.error_code,
            'message': self.message,
            'status_code': self.status_code,
            'context': self.context
        }


# ========== WORKFLOW ERRORS ==========

class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow is not found"""

    def __init__(self, workflow_id: str):
        super().__init__(
            message=f"Workflow not found: {workflow_id}",
            error_code="WORKFLOW_NOT_FOUND",
            status_code=404,
            context={'workflow_id': workflow_id}
        )


class WorkflowValidationError(WorkflowError):
    """Raised when workflow validation fails"""

    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(
            message=message,
            error_code="WORKFLOW_VALIDATION_ERROR",
            status_code=400,
            context={'validation_errors': validation_errors or []}
        )


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails"""

    def __init__(self, workflow_id: str, message: str, execution_id: Optional[str] = None):
        super().__init__(
            message=f"Workflow execution failed: {message}",
            error_code="WORKFLOW_EXECUTION_ERROR",
            status_code=500,
            context={
                'workflow_id': workflow_id,
                'execution_id': execution_id
            }
        )


class WorkflowVersionError(WorkflowError):
    """Raised when there are issues with workflow versioning"""

    def __init__(self, workflow_id: str, message: str):
        super().__init__(
            message=message,
            error_code="WORKFLOW_VERSION_ERROR",
            status_code=400,
            context={'workflow_id': workflow_id}
        )


class WorkflowImportError(WorkflowError):
    """Raised when workflow import fails"""

    def __init__(self, message: str, import_errors: Optional[list] = None):
        super().__init__(
            message=f"Workflow import failed: {message}",
            error_code="WORKFLOW_IMPORT_ERROR",
            status_code=400,
            context={'import_errors': import_errors or []}
        )


# ========== NODE ERRORS ==========

class NodeError(WorkflowError):
    """Base exception for node-related errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        node_id: str,
        node_type: Optional[str] = None,
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context.update({
            'node_id': node_id,
            'node_type': node_type
        })
        super().__init__(message, error_code, status_code, context)


class NodeNotFoundError(NodeError):
    """Raised when a node is not found"""

    def __init__(self, node_id: str):
        super().__init__(
            message=f"Node not found: {node_id}",
            error_code="NODE_NOT_FOUND",
            node_id=node_id,
            status_code=404
        )


class NodeConfigurationError(NodeError):
    """Raised when node configuration is invalid"""

    def __init__(self, node_id: str, node_type: str, message: str):
        super().__init__(
            message=f"Node configuration error: {message}",
            error_code="NODE_CONFIGURATION_ERROR",
            node_id=node_id,
            node_type=node_type,
            status_code=400
        )


class NodeExecutionError(NodeError):
    """Raised when node execution fails"""

    def __init__(
        self,
        node_id: str,
        node_type: str,
        message: str,
        original_error: Optional[Exception] = None
    ):
        context = {}
        if original_error:
            context['original_error'] = {
                'type': type(original_error).__name__,
                'message': str(original_error)
            }

        super().__init__(
            message=f"Node execution failed: {message}",
            error_code="NODE_EXECUTION_ERROR",
            node_id=node_id,
            node_type=node_type,
            status_code=500,
            context=context
        )


class NodeTimeoutError(NodeError):
    """Raised when node execution times out"""

    def __init__(self, node_id: str, node_type: str, timeout_seconds: int):
        super().__init__(
            message=f"Node execution timed out after {timeout_seconds} seconds",
            error_code="NODE_TIMEOUT_ERROR",
            node_id=node_id,
            node_type=node_type,
            status_code=408,
            context={'timeout_seconds': timeout_seconds}
        )


# ========== DATA ERRORS ==========

class DataError(WorkflowError):
    """Base exception for data-related errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, context)


class DataValidationError(DataError):
    """Raised when data validation fails"""

    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(
            message=f"Data validation failed: {message}",
            error_code="DATA_VALIDATION_ERROR",
            status_code=400,
            context={'validation_errors': validation_errors or []}
        )


class DataTransformationError(DataError):
    """Raised when data transformation fails"""

    def __init__(self, message: str, transformation_type: Optional[str] = None):
        super().__init__(
            message=f"Data transformation failed: {message}",
            error_code="DATA_TRANSFORMATION_ERROR",
            status_code=500,
            context={'transformation_type': transformation_type}
        )


class DataConnectionError(DataError):
    """Raised when database or API connection fails"""

    def __init__(self, message: str, connection_type: Optional[str] = None):
        super().__init__(
            message=f"Connection failed: {message}",
            error_code="DATA_CONNECTION_ERROR",
            status_code=503,
            context={'connection_type': connection_type}
        )


# ========== INTEGRATION ERRORS ==========

class IntegrationError(WorkflowError):
    """Base exception for integration-related errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        service_name: str,
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context['service_name'] = service_name
        super().__init__(message, error_code, status_code, context)


class APIError(IntegrationError):
    """Raised when external API call fails"""

    def __init__(
        self,
        service_name: str,
        message: str,
        api_status_code: Optional[int] = None,
        api_response: Optional[str] = None
    ):
        context = {}
        if api_status_code:
            context['api_status_code'] = api_status_code
        if api_response:
            context['api_response'] = api_response

        super().__init__(
            message=f"API call failed: {message}",
            error_code="API_ERROR",
            service_name=service_name,
            status_code=502,
            context=context
        )


class AuthenticationError(IntegrationError):
    """Raised when authentication fails"""

    def __init__(self, service_name: str, message: str):
        super().__init__(
            message=f"Authentication failed: {message}",
            error_code="AUTHENTICATION_ERROR",
            service_name=service_name,
            status_code=401
        )


class RateLimitError(IntegrationError):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        service_name: str,
        retry_after: Optional[int] = None
    ):
        context = {}
        if retry_after:
            context['retry_after'] = retry_after

        super().__init__(
            message=f"Rate limit exceeded for {service_name}",
            error_code="RATE_LIMIT_ERROR",
            service_name=service_name,
            status_code=429,
            context=context
        )


# ========== MEMORY ERRORS ==========

class MemoryError(WorkflowError):
    """Base exception for memory/storage errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        memory_type: str,
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context['memory_type'] = memory_type
        super().__init__(message, error_code, status_code, context)


class VectorStoreError(MemoryError):
    """Raised when vector store operation fails"""

    def __init__(self, message: str, collection: Optional[str] = None):
        super().__init__(
            message=f"Vector store error: {message}",
            error_code="VECTOR_STORE_ERROR",
            memory_type="vector_store",
            status_code=500,
            context={'collection': collection}
        )


class CacheError(MemoryError):
    """Raised when cache operation fails"""

    def __init__(self, message: str, key: Optional[str] = None):
        super().__init__(
            message=f"Cache error: {message}",
            error_code="CACHE_ERROR",
            memory_type="cache",
            status_code=500,
            context={'key': key}
        )


# ========== TEMPLATE ERRORS ==========

class TemplateError(WorkflowError):
    """Base exception for template-related errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        template_id: Optional[str] = None,
        status_code: int = 400,
        context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        if template_id:
            context['template_id'] = template_id
        super().__init__(message, error_code, status_code, context)


class TemplateNotFoundError(TemplateError):
    """Raised when a template is not found"""

    def __init__(self, template_id: str):
        super().__init__(
            message=f"Template not found: {template_id}",
            error_code="TEMPLATE_NOT_FOUND",
            template_id=template_id,
            status_code=404
        )


# ========== UTILITY FUNCTIONS ==========

def error_to_response(error: Exception) -> tuple:
    """
    Convert an exception to a Flask response tuple

    Args:
        error: Exception to convert

    Returns:
        Tuple of (response_dict, status_code)
    """
    if isinstance(error, WorkflowError):
        return error.to_dict(), error.status_code
    else:
        # Generic error
        return {
            'error': True,
            'error_code': 'INTERNAL_ERROR',
            'message': str(error),
            'status_code': 500
        }, 500
