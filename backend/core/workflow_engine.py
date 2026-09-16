"""
Core Workflow Engine for Agentic Automation Platform
Handles workflow execution, agent orchestration, and state management
Uses Ollama for all LLM operations (offline/local or Colab deployed)
"""

from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Types of nodes in a workflow"""
    START = "start"
    END = "end"
    AGENT = "agent"
    CONDITION = "condition"
    HUMAN_IN_LOOP = "human_in_loop"
    DATA_TRANSFORM = "data_transform"
    PARALLEL = "parallel"
    MERGE = "merge"


class ExecutionStatus(str, Enum):
    """Workflow execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    WAITING_HUMAN = "waiting_human"


class WorkflowNode(BaseModel):
    """Represents a single node in the workflow"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: NodeType
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    next_nodes: List[str] = Field(default_factory=list)
    condition: Optional[str] = None

    class Config:
        use_enum_values = True


class WorkflowEdge(BaseModel):
    """Represents a connection between nodes"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    target: str
    condition: Optional[str] = None
    label: Optional[str] = None


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowState(BaseModel):
    """State container for workflow execution"""
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    current_node: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    data: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class AgentRegistry:
    """Registry for agent handlers"""

    def __init__(self):
        self._agents: Dict[str, Callable] = {}

    def register(self, agent_type: str, handler: Callable):
        """Register an agent handler"""
        self._agents[agent_type] = handler
        logger.info(f"Registered agent: {agent_type}")

    def get(self, agent_type: str) -> Optional[Callable]:
        """Get an agent handler"""
        return self._agents.get(agent_type)

    def list_agents(self) -> List[str]:
        """List all registered agents"""
        return list(self._agents.keys())


class WorkflowEngine:
    """
    Core workflow engine that executes agentic workflows
    Supports multi-agent orchestration, conditional routing, and human-in-the-loop
    Uses Ollama for all LLM operations
    """

    def __init__(self, agent_registry: Optional[AgentRegistry] = None):
        self.agent_registry = agent_registry or AgentRegistry()
        self._executions: Dict[str, WorkflowState] = {}
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition"""
        self._workflows[workflow.id] = workflow
        logger.info(f"Registered workflow: {workflow.name} ({workflow.id})")

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition"""
        return self._workflows.get(workflow_id)

    async def execute(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        Execute a workflow

        Args:
            workflow_id: ID of the workflow to execute
            input_data: Initial input data for the workflow
            context: Additional context (user info, permissions, etc.)

        Returns:
            WorkflowState with execution results
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Initialize state
        state = WorkflowState(
            workflow_id=workflow_id,
            data={"input": input_data, "context": context or {}},
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )

        self._executions[state.execution_id] = state

        try:
            # Find start node
            start_node = next(
                (node for node in workflow.nodes if node.type == NodeType.START),
                None
            )

            if not start_node:
                raise ValueError("No start node found in workflow")

            # Execute workflow
            await self._execute_node(workflow, state, start_node)

            state.status = ExecutionStatus.COMPLETED
            state.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            state.status = ExecutionStatus.FAILED
            state.error = str(e)
            state.completed_at = datetime.utcnow()

        return state

    async def _execute_node(
        self,
        workflow: WorkflowDefinition,
        state: WorkflowState,
        node: WorkflowNode
    ):
        """Execute a single node"""
        logger.info(f"Executing node: {node.name} ({node.type})")

        state.current_node = node.id
        state.history.append({
            "node_id": node.id,
            "node_name": node.name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started"
        })

        try:
            # Execute based on node type
            if node.type == NodeType.START:
                await self._execute_start_node(state, node)
            elif node.type == NodeType.END:
                await self._execute_end_node(state, node)
            elif node.type == NodeType.AGENT:
                await self._execute_agent_node(state, node)
            elif node.type == NodeType.CONDITION:
                await self._execute_condition_node(workflow, state, node)
                return
            elif node.type == NodeType.HUMAN_IN_LOOP:
                await self._execute_human_in_loop_node(state, node)
                return
            elif node.type == NodeType.PARALLEL:
                await self._execute_parallel_node(workflow, state, node)
            elif node.type == NodeType.DATA_TRANSFORM:
                await self._execute_transform_node(state, node)

            state.history[-1]["status"] = "completed"

            # Continue to next nodes
            next_nodes = self._get_next_nodes(workflow, node)
            for next_node in next_nodes:
                await self._execute_node(workflow, state, next_node)

        except Exception as e:
            state.history[-1]["status"] = "failed"
            state.history[-1]["error"] = str(e)
            raise

    async def _execute_start_node(self, state: WorkflowState, node: WorkflowNode):
        """Execute start node"""
        state.data["start_time"] = datetime.utcnow().isoformat()

    async def _execute_end_node(self, state: WorkflowState, node: WorkflowNode):
        """Execute end node"""
        state.data["end_time"] = datetime.utcnow().isoformat()

    async def _execute_agent_node(self, state: WorkflowState, node: WorkflowNode):
        """Execute an agent node"""
        agent_type = node.config.get("agent_type")
        if not agent_type:
            raise ValueError(f"No agent_type specified for node: {node.name}")

        agent_handler = self.agent_registry.get(agent_type)
        if not agent_handler:
            raise ValueError(f"Agent not found: {agent_type}")

        # Execute agent
        result = await agent_handler(state.data, node.config)

        # Store result in state
        output_key = node.config.get("output_key", f"{node.id}_output")
        state.data[output_key] = result

    async def _execute_condition_node(
        self,
        workflow: WorkflowDefinition,
        state: WorkflowState,
        node: WorkflowNode
    ):
        """Execute a condition node"""
        condition = node.config.get("condition")
        if not condition:
            raise ValueError(f"No condition specified for node: {node.name}")

        result = self._evaluate_condition(condition, state.data)

        edges = [e for e in workflow.edges if e.source == node.id]

        for edge in edges:
            edge_condition = edge.condition or "default"
            if (result and edge_condition == "true") or \
               (not result and edge_condition == "false") or \
               edge_condition == "default":
                target_node = next(
                    n for n in workflow.nodes if n.id == edge.target
                )
                await self._execute_node(workflow, state, target_node)
                break

    async def _execute_human_in_loop_node(
        self,
        state: WorkflowState,
        node: WorkflowNode
    ):
        """Execute human-in-the-loop node"""
        state.status = ExecutionStatus.WAITING_HUMAN
        state.data["human_review"] = {
            "node_id": node.id,
            "prompt": node.config.get("prompt"),
            "options": node.config.get("options"),
            "required_fields": node.config.get("required_fields", [])
        }

    async def _execute_parallel_node(
        self,
        workflow: WorkflowDefinition,
        state: WorkflowState,
        node: WorkflowNode
    ):
        """Execute parallel node"""
        next_nodes = self._get_next_nodes(workflow, node)
        tasks = [
            self._execute_node(workflow, state, next_node)
            for next_node in next_nodes
        ]
        await asyncio.gather(*tasks)

    async def _execute_transform_node(self, state: WorkflowState, node: WorkflowNode):
        """Execute data transformation node"""
        transform_type = node.config.get("transform_type")
        input_key = node.config.get("input_key")
        output_key = node.config.get("output_key")

        input_data = state.data.get(input_key)

        if transform_type == "extract":
            fields = node.config.get("fields", [])
            result = {field: input_data.get(field) for field in fields}
        elif transform_type == "merge":
            keys = node.config.get("keys", [])
            result = {}
            for key in keys:
                result.update(state.data.get(key, {}))
        else:
            result = input_data

        state.data[output_key] = result

    def _get_next_nodes(
        self,
        workflow: WorkflowDefinition,
        node: WorkflowNode
    ) -> List[WorkflowNode]:
        """Get the next nodes to execute"""
        edges = [e for e in workflow.edges if e.source == node.id]
        next_node_ids = [e.target for e in edges]
        return [n for n in workflow.nodes if n.id in next_node_ids]

    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate a condition expression"""
        try:
            if "==" in condition:
                key, value = condition.split("==")
                return str(data.get(key.strip())) == value.strip()
            elif ">" in condition:
                key, value = condition.split(">")
                return float(data.get(key.strip(), 0)) > float(value.strip())
            elif "<" in condition:
                key, value = condition.split("<")
                return float(data.get(key.strip(), 0)) < float(value.strip())
            else:
                return bool(data.get(condition.strip()))
        except Exception:
            return False

    async def resume_execution(
        self,
        execution_id: str,
        human_input: Dict[str, Any]
    ) -> WorkflowState:
        """Resume a paused workflow execution with human input"""
        state = self._executions.get(execution_id)
        if not state:
            raise ValueError(f"Execution not found: {execution_id}")

        if state.status != ExecutionStatus.WAITING_HUMAN:
            raise ValueError(f"Execution is not waiting for human input: {execution_id}")

        state.data["human_input"] = human_input
        state.status = ExecutionStatus.RUNNING

        workflow = self.get_workflow(state.workflow_id)
        current_node = next(
            n for n in workflow.nodes if n.id == state.current_node
        )

        next_nodes = self._get_next_nodes(workflow, current_node)
        for next_node in next_nodes:
            await self._execute_node(workflow, state, next_node)

        state.status = ExecutionStatus.COMPLETED
        state.completed_at = datetime.utcnow()

        return state

    def get_execution(self, execution_id: str) -> Optional[WorkflowState]:
        """Get execution state"""
        return self._executions.get(execution_id)
