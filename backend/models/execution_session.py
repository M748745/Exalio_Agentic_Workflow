"""
Execution Session Model

Represents a single workflow execution session for step-by-step execution.
Tracks execution state, node results, and manages execution order.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


class ExecutionSession:
    """Represents a single workflow execution session"""

    def __init__(self, workflow: Dict[str, Any], inputs: Dict[str, Any]):
        """
        Initialize execution session

        Args:
            workflow: Workflow definition with nodes and edges
            inputs: Initial input values for the workflow
        """
        self.session_id = str(uuid.uuid4())
        self.workflow = workflow
        self.inputs = inputs
        self.current_index = 0
        self.results = {}  # node_id -> execution result
        self.status = "ready"  # ready, running, paused, completed, error
        self.executed_nodes = []  # List of executed node IDs
        self.pending_nodes = []  # List of nodes to execute
        self.error = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Initialize execution order
        self._initialize_execution_order()

    def _initialize_execution_order(self):
        """Determine node execution order using topological sort"""
        nodes = self.workflow.get('nodes', [])
        edges = self.workflow.get('edges', [])

        # Build adjacency list (dependencies)
        in_degree = {node['id']: 0 for node in nodes}
        adjacency = {node['id']: [] for node in nodes}

        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target:
                adjacency[source].append(target)
                in_degree[target] = in_degree.get(target, 0) + 1

        # Topological sort using Kahn's algorithm
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []

        while queue:
            # Sort queue for consistent ordering
            queue.sort()
            node_id = queue.pop(0)
            sorted_nodes.append(node_id)

            # Reduce in-degree for neighbors
            for neighbor in adjacency.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(sorted_nodes) != len(nodes):
            raise ValueError("Workflow contains cycles - cannot determine execution order")

        self.pending_nodes = sorted_nodes

    def get_next_node(self) -> Optional[Dict[str, Any]]:
        """Get next node to execute"""
        if self.current_index < len(self.pending_nodes):
            node_id = self.pending_nodes[self.current_index]
            # Find node definition
            for node in self.workflow.get('nodes', []):
                if node['id'] == node_id:
                    return node
        return None

    def execute_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single node

        Args:
            node: Node definition to execute

        Returns:
            Node execution result
        """
        self.status = "running"
        self.updated_at = datetime.utcnow()

        try:
            node_id = node['id']
            node_type = node.get('type', '')
            node_data = node.get('data', {})

            # Build context from previous results
            context = {
                'inputs': self.inputs,
                'results': self.results,
                'node': node
            }

            # Execute node using workflow executor
            result = self._execute_single_node(node, context)

            # Store result
            self.results[node_id] = result
            self.executed_nodes.append(node_id)
            self.current_index += 1

            return result

        except Exception as e:
            self.status = "error"
            self.error = str(e)
            self.updated_at = datetime.utcnow()
            raise e

    def _execute_single_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute a single node with context

        Args:
            node: Node definition
            context: Execution context with inputs and previous results

        Returns:
            Node execution result
        """
        node_type = node.get('type', '')
        node_data = node.get('data', {})
        node_id = node['id']

        # Handle different node types
        if node_type == 'input':
            # Input nodes return their configured value or from context
            label = node_data.get('label', '')
            return context['inputs'].get(label, node_data.get('value', ''))

        elif node_type == 'output':
            # Output nodes return the input they receive
            # Find incoming edge
            incoming_edges = [e for e in self.workflow.get('edges', [])
                            if e.get('target') == node_id]
            if incoming_edges:
                source_id = incoming_edges[0].get('source')
                return context['results'].get(source_id, '')
            return None

        elif node_type == 'llm':
            # LLM nodes - use workflow executor's LLM execution
            return self._execute_llm_node(node, context)

        elif node_type in ['memory_cache_get', 'memory_cache_set', 'memory_vector_store',
                          'memory_vector_search', 'memory_context_get', 'memory_context_append']:
            # Memory nodes - use workflow executor's memory execution
            return self._execute_memory_node(node, context)

        elif node_type == 'transform':
            # Transform nodes - apply transformation
            return self._execute_transform_node(node, context)

        elif node_type == 'if_else':
            # Conditional nodes
            return self._execute_conditional_node(node, context)

        else:
            # Default: return node data
            return {'type': node_type, 'data': node_data}

    def _get_node_inputs(self, node_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get inputs for a node from connected edges"""
        inputs = {}
        edges = self.workflow.get('edges', [])

        for edge in edges:
            if edge.get('target') == node_id:
                source_id = edge.get('source')
                source_handle = edge.get('sourceHandle', 'output')
                target_handle = edge.get('targetHandle', 'input')

                # Get result from source node
                if source_id in context['results']:
                    inputs[target_handle] = context['results'][source_id]

        return inputs

    def _execute_llm_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM node"""
        node_data = node.get('data', {})
        config = node_data.get('config', {})

        # Get inputs from connected nodes
        inputs = self._get_node_inputs(node['id'], context)

        # Get prompt (from config or input)
        prompt = inputs.get('prompt', config.get('prompt', ''))

        # Placeholder for LLM execution
        # In production, this would call the actual LLM API
        return {
            'response': f"LLM response to: {prompt[:50]}...",
            'model': config.get('model', 'unknown'),
            'tokens': 100
        }

    def _execute_memory_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute memory node"""
        node_type = node.get('type', '')
        node_data = node.get('data', {})
        config = node_data.get('config', {})

        # Get inputs from connected nodes
        inputs = self._get_node_inputs(node['id'], context)

        # Placeholder for memory operations
        if 'get' in node_type:
            return {'value': 'cached_value', 'found': True}
        elif 'set' in node_type or 'store' in node_type or 'append' in node_type:
            return {'success': True, 'stored': True}
        elif 'search' in node_type:
            return {'results': [], 'count': 0}

        return {'success': True}

    def _execute_transform_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute transform node"""
        node_data = node.get('data', {})
        config = node_data.get('config', {})

        # Get inputs
        inputs = self._get_node_inputs(node['id'], context)
        input_value = inputs.get('input', '')

        # Apply transformation
        transform_type = config.get('type', 'text')
        if transform_type == 'uppercase':
            return str(input_value).upper()
        elif transform_type == 'lowercase':
            return str(input_value).lower()
        else:
            return input_value

    def _execute_conditional_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional (if/else) node"""
        node_data = node.get('data', {})
        config = node_data.get('config', {})

        # Get inputs
        inputs = self._get_node_inputs(node['id'], context)
        condition_value = inputs.get('condition', False)

        # Evaluate condition
        operator = config.get('operator', 'equals')
        compare_value = config.get('value', '')

        result = False
        if operator == 'equals':
            result = str(condition_value) == str(compare_value)
        elif operator == 'contains':
            result = str(compare_value) in str(condition_value)
        elif operator == 'greater_than':
            try:
                result = float(condition_value) > float(compare_value)
            except:
                result = False

        return {'condition': result, 'true_path': result, 'false_path': not result}

    def pause(self):
        """Pause execution"""
        if self.status == "running":
            self.status = "paused"
            self.updated_at = datetime.utcnow()

    def resume(self):
        """Resume execution"""
        if self.status == "paused":
            self.status = "running"
            self.updated_at = datetime.utcnow()

    def is_complete(self) -> bool:
        """Check if execution is complete"""
        return self.current_index >= len(self.pending_nodes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'status': self.status,
            'executed_nodes': self.executed_nodes,
            'pending_nodes': self.pending_nodes[self.current_index:],
            'current_index': self.current_index,
            'total_nodes': len(self.pending_nodes),
            'results': self.results,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed': self.is_complete()
        }
