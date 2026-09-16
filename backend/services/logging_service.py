"""
Logging Service
Provides centralized logging configuration with multiple handlers and formatters
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'workflow_id'):
            log_data['workflow_id'] = record.workflow_id
        if hasattr(record, 'execution_id'):
            log_data['execution_id'] = record.execution_id
        if hasattr(record, 'node_id'):
            log_data['node_id'] = record.node_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Formatter that adds colors to console output
    """

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Build log message
        log_msg = f"{color}[{record.levelname}]{reset} {timestamp} - {record.name} - {record.getMessage()}"

        # Add context if available
        context_parts = []
        if hasattr(record, 'workflow_id'):
            context_parts.append(f"workflow={record.workflow_id}")
        if hasattr(record, 'execution_id'):
            context_parts.append(f"execution={record.execution_id}")
        if hasattr(record, 'node_id'):
            context_parts.append(f"node={record.node_id}")

        if context_parts:
            log_msg += f" [{', '.join(context_parts)}]"

        # Add exception if present
        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"

        return log_msg


class LoggingService:
    """
    Centralized logging service
    """

    def __init__(
        self,
        log_dir: str = "backend/logs",
        app_name: str = "workflow_engine",
        console_level: str = "INFO",
        file_level: str = "DEBUG",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Initialize logging service

        Args:
            log_dir: Directory for log files
            app_name: Application name for log files
            console_level: Log level for console output
            file_level: Log level for file output
            max_bytes: Max size of each log file before rotation
            backup_count: Number of backup files to keep
        """
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.console_level = getattr(logging, console_level.upper())
        self.file_level = getattr(logging, file_level.upper())
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging handlers and formatters"""

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture all levels

        # Remove existing handlers
        root_logger.handlers.clear()

        # Console Handler (with colors)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        console_handler.setFormatter(ColoredConsoleFormatter())
        root_logger.addHandler(console_handler)

        # File Handler - All logs (JSON format)
        all_logs_path = self.log_dir / f"{self.app_name}.log"
        all_handler = logging.handlers.RotatingFileHandler(
            all_logs_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        all_handler.setLevel(self.file_level)
        all_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(all_handler)

        # File Handler - Error logs only (JSON format)
        error_logs_path = self.log_dir / f"{self.app_name}.error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_logs_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)

        # File Handler - Human-readable logs
        readable_logs_path = self.log_dir / f"{self.app_name}.readable.log"
        readable_handler = logging.handlers.RotatingFileHandler(
            readable_logs_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        readable_handler.setLevel(self.file_level)
        readable_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        readable_handler.setFormatter(readable_formatter)
        root_logger.addHandler(readable_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance

        Args:
            name: Logger name (typically __name__)

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    def log_with_context(
        self,
        logger: logging.Logger,
        level: str,
        message: str,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        node_id: Optional[str] = None,
        user_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        **extra_context
    ):
        """
        Log a message with additional context

        Args:
            logger: Logger instance
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            workflow_id: Optional workflow ID
            execution_id: Optional execution ID
            node_id: Optional node ID
            user_id: Optional user ID
            duration_ms: Optional duration in milliseconds
            **extra_context: Additional context fields
        """
        extra = {}
        if workflow_id:
            extra['workflow_id'] = workflow_id
        if execution_id:
            extra['execution_id'] = execution_id
        if node_id:
            extra['node_id'] = node_id
        if user_id:
            extra['user_id'] = user_id
        if duration_ms is not None:
            extra['duration_ms'] = duration_ms

        extra.update(extra_context)

        log_level = getattr(logging, level.upper())
        logger.log(log_level, message, extra=extra)


class ContextLogger:
    """
    Logger wrapper that automatically includes context in all log messages
    """

    def __init__(
        self,
        logger: logging.Logger,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        node_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize context logger

        Args:
            logger: Base logger instance
            workflow_id: Workflow ID to include in all logs
            execution_id: Execution ID to include in all logs
            node_id: Node ID to include in all logs
            user_id: User ID to include in all logs
        """
        self.logger = logger
        self.context = {}

        if workflow_id:
            self.context['workflow_id'] = workflow_id
        if execution_id:
            self.context['execution_id'] = execution_id
        if node_id:
            self.context['node_id'] = node_id
        if user_id:
            self.context['user_id'] = user_id

    def _log(self, level: int, message: str, *args, **kwargs):
        """Internal log method that adds context"""
        extra = kwargs.pop('extra', {})
        extra.update(self.context)
        self.logger.log(level, message, *args, extra=extra, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message with context"""
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message with context"""
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message with context"""
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message with context"""
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message with context"""
        self._log(logging.CRITICAL, message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log exception with context"""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, *args, **kwargs)


# Global instance
logging_service = LoggingService()

# Convenience function
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging_service.get_logger(name)

def get_context_logger(
    name: str,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    node_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> ContextLogger:
    """Get a context logger instance"""
    logger = logging_service.get_logger(name)
    return ContextLogger(logger, workflow_id, execution_id, node_id, user_id)
