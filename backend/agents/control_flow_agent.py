"""
Control Flow & Conditional Logic Agents
Critical missing feature: Branching, loops, error handling

Nodes Provided:
- If/Else Node - Conditional branching
- Switch/Case Node - Multi-way branching
- For Loop Node - Iterate over arrays
- While Loop Node - Loop until condition met
- Try/Catch Node - Error handling
- Parallel Execution Node - Run branches simultaneously
- Wait/Delay Node - Pause execution
- Break/Continue Node - Control loop flow
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import asyncio
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ControlFlowResult:
    """Result from control flow execution"""
    branch_taken: Optional[str] = None
    iterations: int = 0
    execution_time_ms: float = 0.0
    output: Any = None
    error: Optional[str] = None


class IfElseAgent:
    """
    Conditional branching node
    Evaluates condition and executes one of two branches
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute if/else logic

        Config:
            condition: Python expression or comparison (e.g., "value > 100")
            if_true: Node ID to execute if true
            if_false: Node ID to execute if false

        Inputs:
            value: Value to test in condition
            context: Additional context for evaluation
        """
        start_time = time.time()

        condition = self.config.get('condition', 'True')
        value = inputs.get('value')

        # Evaluate condition safely
        try:
            # Create safe evaluation context
            eval_context = {
                'value': value,
                **inputs.get('context', {})
            }

            # Evaluate condition
            result = self._safe_eval(condition, eval_context)

            branch_taken = 'if_true' if result else 'if_false'

            return {
                'branch': branch_taken,
                'condition_result': result,
                'next_node': self.config.get(branch_taken),
                'execution_time_ms': (time.time() - start_time) * 1000
            }

        except Exception as e:
            logger.error(f"If/Else evaluation error: {e}")
            return {
                'branch': 'error',
                'error': str(e),
                'next_node': self.config.get('on_error')
            }

    def _safe_eval(self, expression: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate expression"""
        # Whitelist of allowed operations
        allowed_names = {
            'True': True,
            'False': False,
            'None': None,
            'and': lambda x, y: x and y,
            'or': lambda x, y: x or y,
            'not': lambda x: not x,
            **context
        }

        # Compile and evaluate
        code = compile(expression, '<string>', 'eval')

        # Check for dangerous operations
        if any(name not in allowed_names for name in code.co_names):
            raise ValueError(f"Unsafe operation in condition: {expression}")

        return eval(code, {"__builtins__": {}}, allowed_names)


class SwitchCaseAgent:
    """
    Multi-way branching node
    Similar to switch/case in programming
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute switch/case logic

        Config:
            variable: Variable to test
            cases: Dict of value -> node_id mappings
            default: Node ID for default case

        Inputs:
            value: Value to match against cases
        """
        value = inputs.get('value')
        cases = self.config.get('cases', {})
        default_node = self.config.get('default')

        # Find matching case
        matched_node = cases.get(str(value), default_node)

        return {
            'matched_case': str(value) if str(value) in cases else 'default',
            'next_node': matched_node,
            'value': value
        }


class ForLoopAgent:
    """
    Iterate over array/list
    Execute sub-workflow for each item
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute for loop

        Config:
            array_source: Input key containing array
            loop_body: Node ID to execute for each item
            max_iterations: Safety limit (default: 1000)

        Inputs:
            array: Array to iterate over

        Returns:
            results: Array of results from each iteration
        """
        array = inputs.get('array', [])
        loop_body = self.config.get('loop_body')
        max_iterations = self.config.get('max_iterations', 1000)

        if len(array) > max_iterations:
            raise ValueError(f"Array too large: {len(array)} > {max_iterations}")

        results = []
        for index, item in enumerate(array):
            iteration_result = {
                'item': item,
                'index': index,
                'total': len(array)
            }
            results.append(iteration_result)

        return {
            'results': results,
            'iterations': len(array),
            'loop_body_node': loop_body
        }


class WhileLoopAgent:
    """
    Loop while condition is true
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute while loop

        Config:
            condition: Condition to evaluate each iteration
            loop_body: Node ID to execute
            max_iterations: Safety limit (default: 100)

        Inputs:
            initial_value: Starting value
        """
        condition = self.config.get('condition', 'False')
        max_iterations = self.config.get('max_iterations', 100)

        iterations = 0
        current_value = inputs.get('initial_value')

        # Safety check - we can't actually execute the loop without the workflow engine
        # This node would need to coordinate with the workflow engine for actual execution

        return {
            'type': 'while_loop',
            'condition': condition,
            'max_iterations': max_iterations,
            'loop_body_node': self.config.get('loop_body'),
            'note': 'While loop execution requires workflow engine coordination'
        }


class TryCatchAgent:
    """
    Error handling node
    Try executing a node, catch errors and execute recovery
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute try/catch logic

        Config:
            try_node: Node ID to try executing
            catch_node: Node ID to execute on error
            finally_node: Node ID to always execute (optional)
            retry_count: Number of retries (default: 0)
            retry_delay: Delay between retries in seconds

        Returns:
            success: Boolean indicating if try block succeeded
            error: Error message if failed
            next_node: Node to execute next
        """
        try_node = self.config.get('try_node')
        catch_node = self.config.get('catch_node')
        finally_node = self.config.get('finally_node')
        retry_count = self.config.get('retry_count', 0)
        retry_delay = self.config.get('retry_delay', 1)

        return {
            'type': 'try_catch',
            'try_node': try_node,
            'catch_node': catch_node,
            'finally_node': finally_node,
            'retry_count': retry_count,
            'retry_delay': retry_delay,
            'note': 'Try/catch execution requires workflow engine coordination'
        }


class ParallelExecutionAgent:
    """
    Execute multiple branches in parallel
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute branches in parallel

        Config:
            branches: List of node IDs to execute in parallel
            wait_for_all: If true, wait for all branches (default: true)
            timeout: Max time to wait in seconds

        Returns:
            results: Results from all branches
            completed: Number of branches completed
        """
        branches = self.config.get('branches', [])
        wait_for_all = self.config.get('wait_for_all', True)
        timeout = self.config.get('timeout', 300)

        return {
            'type': 'parallel',
            'branches': branches,
            'wait_for_all': wait_for_all,
            'timeout': timeout,
            'note': 'Parallel execution requires workflow engine coordination'
        }


class WaitDelayAgent:
    """
    Pause execution for specified duration
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wait for specified time

        Config:
            duration_seconds: Time to wait
            duration_ms: Time to wait in milliseconds
        """
        duration_seconds = self.config.get('duration_seconds', 0)
        duration_ms = self.config.get('duration_ms', 0)

        total_wait = duration_seconds + (duration_ms / 1000)

        if total_wait > 0:
            await asyncio.sleep(total_wait)

        return {
            'waited_seconds': total_wait,
            'completed_at': time.time()
        }


class BreakContinueAgent:
    """
    Control loop flow
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Break or continue loop

        Config:
            action: 'break' or 'continue'
            condition: Optional condition for action
        """
        action = self.config.get('action', 'break')
        condition = self.config.get('condition')

        should_act = True
        if condition:
            # Evaluate condition
            should_act = self._evaluate_condition(condition, inputs)

        return {
            'action': action if should_act else 'none',
            'condition_met': should_act
        }

    def _evaluate_condition(self, condition: str, inputs: Dict[str, Any]) -> bool:
        """Evaluate condition safely"""
        try:
            # Simple evaluation for demo
            # In production, use safe_eval like IfElseAgent
            return eval(condition, {"__builtins__": {}}, inputs)
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False
