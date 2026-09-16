"""
Retry Service
Handles retry logic for failed node executions with configurable strategies
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry backoff strategies"""
    IMMEDIATE = "immediate"  # No delay between retries
    LINEAR = "linear"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponentially increasing delay
    FIBONACCI = "fibonacci"  # Fibonacci sequence delays


class RetryService:
    """
    Service for implementing retry logic with various strategies
    """

    def __init__(self):
        """Initialize retry service"""
        self.retry_history = {}  # Track retry attempts

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retry_on_exceptions: Optional[Tuple[type, ...]] = None,
        backoff_multiplier: float = 2.0,
        node_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a function with retry logic

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            strategy: Retry strategy to use
            retry_on_exceptions: Tuple of exception types to retry on (None = retry all)
            backoff_multiplier: Multiplier for exponential backoff
            node_id: Optional node ID for tracking
            **kwargs: Keyword arguments for func

        Returns:
            Dictionary with result and retry metadata
        """
        attempt = 0
        last_error = None
        retry_log = []

        while attempt <= max_retries:
            try:
                # Execute the function
                start_time = time.time()

                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                execution_time = time.time() - start_time

                # Success - return result with metadata
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1,
                    "total_retries": attempt,
                    "execution_time": execution_time,
                    "retry_log": retry_log
                }

            except Exception as e:
                last_error = e
                attempt += 1

                # Check if we should retry this exception
                if retry_on_exceptions and not isinstance(e, retry_on_exceptions):
                    logger.warning(f"Exception {type(e).__name__} not in retry list, failing immediately")
                    break

                # Check if we have retries left
                if attempt > max_retries:
                    break

                # Calculate delay for this retry
                delay = self._calculate_delay(
                    attempt=attempt,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    strategy=strategy,
                    backoff_multiplier=backoff_multiplier
                )

                # Log retry attempt
                retry_info = {
                    "attempt": attempt,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "delay": delay,
                    "timestamp": time.time()
                }
                retry_log.append(retry_info)

                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed with {type(e).__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )

                # Store retry history
                if node_id:
                    if node_id not in self.retry_history:
                        self.retry_history[node_id] = []
                    self.retry_history[node_id].append(retry_info)

                # Wait before retry
                await asyncio.sleep(delay)

        # All retries exhausted - return failure
        return {
            "success": False,
            "error": str(last_error),
            "error_type": type(last_error).__name__ if last_error else "Unknown",
            "attempts": attempt,
            "total_retries": attempt - 1,
            "retry_log": retry_log,
            "max_retries_exceeded": True
        }

    def _calculate_delay(
        self,
        attempt: int,
        initial_delay: float,
        max_delay: float,
        strategy: RetryStrategy,
        backoff_multiplier: float
    ) -> float:
        """
        Calculate delay for the current retry attempt

        Args:
            attempt: Current attempt number (1-indexed)
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            strategy: Retry strategy
            backoff_multiplier: Multiplier for exponential backoff

        Returns:
            Delay in seconds
        """
        if strategy == RetryStrategy.IMMEDIATE:
            return 0.0

        elif strategy == RetryStrategy.LINEAR:
            delay = initial_delay

        elif strategy == RetryStrategy.EXPONENTIAL:
            # Exponential: delay = initial_delay * (multiplier ^ (attempt - 1))
            delay = initial_delay * (backoff_multiplier ** (attempt - 1))

        elif strategy == RetryStrategy.FIBONACCI:
            # Fibonacci sequence for delays
            delay = initial_delay * self._fibonacci(attempt)

        else:
            # Default to exponential
            delay = initial_delay * (backoff_multiplier ** (attempt - 1))

        # Cap at max_delay
        return min(delay, max_delay)

    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number (1-indexed)"""
        if n <= 1:
            return 1
        elif n == 2:
            return 1

        a, b = 1, 1
        for _ in range(n - 2):
            a, b = b, a + b
        return b

    def get_retry_stats(self, node_id: str) -> Dict[str, Any]:
        """
        Get retry statistics for a specific node

        Args:
            node_id: Node ID

        Returns:
            Dictionary with retry statistics
        """
        if node_id not in self.retry_history:
            return {
                "node_id": node_id,
                "total_retries": 0,
                "retry_history": []
            }

        retry_history = self.retry_history[node_id]

        return {
            "node_id": node_id,
            "total_retries": len(retry_history),
            "retry_history": retry_history,
            "most_common_error": self._get_most_common_error(retry_history)
        }

    def _get_most_common_error(self, retry_history: list) -> Optional[str]:
        """Get the most common error type from retry history"""
        if not retry_history:
            return None

        error_counts = {}
        for retry in retry_history:
            error_type = retry.get("error_type", "Unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return max(error_counts, key=error_counts.get)

    def clear_history(self, node_id: Optional[str] = None):
        """
        Clear retry history

        Args:
            node_id: Optional node ID to clear specific history, None clears all
        """
        if node_id:
            self.retry_history.pop(node_id, None)
        else:
            self.retry_history.clear()


# Decorator for easy retry functionality
def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retry_on_exceptions: Optional[Tuple[type, ...]] = None,
    backoff_multiplier: float = 2.0
):
    """
    Decorator to add retry logic to async functions

    Usage:
        @with_retry(max_retries=5, strategy=RetryStrategy.EXPONENTIAL)
        async def my_function():
            # Your code here
            pass
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            retry_service = RetryService()
            result = await retry_service.execute_with_retry(
                func,
                *args,
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                strategy=strategy,
                retry_on_exceptions=retry_on_exceptions,
                backoff_multiplier=backoff_multiplier,
                **kwargs
            )

            if not result["success"]:
                raise Exception(f"Failed after {result['attempts']} attempts: {result['error']}")

            return result["result"]

        return wrapper
    return decorator


# Global instance
retry_service = RetryService()
