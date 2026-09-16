"""
Backend Errors Package
"""

from .custom_errors import (
    # Base errors
    WorkflowError,

    # Workflow errors
    WorkflowNotFoundError,
    WorkflowValidationError,
    WorkflowExecutionError,
    WorkflowVersionError,
    WorkflowImportError,

    # Node errors
    NodeError,
    NodeNotFoundError,
    NodeConfigurationError,
    NodeExecutionError,
    NodeTimeoutError,

    # Data errors
    DataError,
    DataValidationError,
    DataTransformationError,
    DataConnectionError,

    # Integration errors
    IntegrationError,
    APIError,
    AuthenticationError,
    RateLimitError,

    # Memory errors
    MemoryError,
    VectorStoreError,
    CacheError,

    # Template errors
    TemplateError,
    TemplateNotFoundError,

    # Utility functions
    error_to_response
)

__all__ = [
    'WorkflowError',
    'WorkflowNotFoundError',
    'WorkflowValidationError',
    'WorkflowExecutionError',
    'WorkflowVersionError',
    'WorkflowImportError',
    'NodeError',
    'NodeNotFoundError',
    'NodeConfigurationError',
    'NodeExecutionError',
    'NodeTimeoutError',
    'DataError',
    'DataValidationError',
    'DataTransformationError',
    'DataConnectionError',
    'IntegrationError',
    'APIError',
    'AuthenticationError',
    'RateLimitError',
    'MemoryError',
    'VectorStoreError',
    'CacheError',
    'TemplateError',
    'TemplateNotFoundError',
    'error_to_response'
]
