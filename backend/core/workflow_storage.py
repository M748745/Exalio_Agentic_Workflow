"""
Workflow Storage - Database persistence for workflows
Handles CRUD operations, versioning, and execution history
"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import asyncio
from contextlib import contextmanager

from core.workflow_engine import WorkflowDefinition, WorkflowState, WorkflowNode, WorkflowEdge

logger = logging.getLogger(__name__)


class WorkflowStorage:
    """
    Handles workflow persistence to SQLite database
    Provides CRUD operations, versioning, and execution history
    """

    def __init__(self, db_path: str = "workflows.db"):
        """
        Initialize workflow storage

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database schema"""
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"

        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                logger.info("Database initialized successfully")
        else:
            logger.warning(f"Schema file not found: {schema_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ========================================================================
    # WORKFLOW CRUD OPERATIONS
    # ========================================================================

    def save_workflow(self, workflow: WorkflowDefinition, user_id: Optional[int] = None) -> str:
        """
        Save workflow to database

        Args:
            workflow: WorkflowDefinition to save
            user_id: Optional user ID who owns the workflow

        Returns:
            Workflow ID
        """
        try:
            # Convert workflow to JSON
            definition_json = self._workflow_to_json(workflow)

            with self._get_connection() as conn:
                # Check if workflow exists
                existing = conn.execute(
                    "SELECT id FROM workflows WHERE id = ?",
                    (workflow.id,)
                ).fetchone()

                if existing:
                    # Update existing workflow
                    conn.execute("""
                        UPDATE workflows
                        SET name = ?, description = ?, version = ?,
                            definition = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        workflow.name,
                        workflow.description,
                        workflow.version,
                        definition_json,
                        workflow.id
                    ))

                    # Create new version
                    self._create_version(conn, workflow.id, definition_json, user_id)

                else:
                    # Insert new workflow
                    conn.execute("""
                        INSERT INTO workflows (id, name, description, version, user_id, definition)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        workflow.id,
                        workflow.name,
                        workflow.description,
                        workflow.version,
                        user_id,
                        definition_json
                    ))

                    # Create initial version
                    self._create_version(conn, workflow.id, definition_json, user_id, version=1)

            logger.info(f"Saved workflow: {workflow.name} ({workflow.id})")
            return workflow.id

        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            raise

    def load_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Load workflow from database

        Args:
            workflow_id: Workflow ID to load

        Returns:
            WorkflowDefinition or None if not found
        """
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT definition FROM workflows WHERE id = ?",
                    (workflow_id,)
                ).fetchone()

                if row:
                    return self._json_to_workflow(row['definition'])
                else:
                    logger.warning(f"Workflow not found: {workflow_id}")
                    return None

        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            raise

    def list_workflows(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all workflows

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of workflow summaries
        """
        try:
            with self._get_connection() as conn:
                if user_id:
                    rows = conn.execute("""
                        SELECT id, name, description, version, created_at, updated_at
                        FROM workflows
                        WHERE user_id = ?
                        ORDER BY updated_at DESC
                    """, (user_id,)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT id, name, description, version, created_at, updated_at
                        FROM workflows
                        ORDER BY updated_at DESC
                    """).fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete workflow from database

        Args:
            workflow_id: Workflow ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with self._get_connection() as conn:
                # Delete workflow and all related data (cascade)
                conn.execute("DELETE FROM workflow_versions WHERE workflow_id = ?", (workflow_id,))
                conn.execute("DELETE FROM workflow_executions WHERE workflow_id = ?", (workflow_id,))
                conn.execute("DELETE FROM scheduled_workflows WHERE workflow_id = ?", (workflow_id,))
                result = conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))

                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Deleted workflow: {workflow_id}")
                return deleted

        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            raise

    # ========================================================================
    # WORKFLOW VERSIONING
    # ========================================================================

    def _create_version(
        self,
        conn,
        workflow_id: str,
        definition_json: str,
        user_id: Optional[int] = None,
        version: Optional[int] = None,
        description: Optional[str] = None
    ):
        """Create a new version of the workflow"""
        if version is None:
            # Get latest version number
            row = conn.execute(
                "SELECT MAX(version) as max_version FROM workflow_versions WHERE workflow_id = ?",
                (workflow_id,)
            ).fetchone()
            version = (row['max_version'] or 0) + 1

        conn.execute("""
            INSERT INTO workflow_versions (workflow_id, version, definition, created_by, change_description)
            VALUES (?, ?, ?, ?, ?)
        """, (workflow_id, version, definition_json, user_id, description))

    def get_workflow_versions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a workflow"""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT version, created_at, created_by, change_description
                    FROM workflow_versions
                    WHERE workflow_id = ?
                    ORDER BY version DESC
                """, (workflow_id,)).fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get workflow versions: {e}")
            raise

    def load_workflow_version(self, workflow_id: str, version: int) -> Optional[WorkflowDefinition]:
        """Load a specific version of a workflow"""
        try:
            with self._get_connection() as conn:
                row = conn.execute("""
                    SELECT definition
                    FROM workflow_versions
                    WHERE workflow_id = ? AND version = ?
                """, (workflow_id, version)).fetchone()

                if row:
                    return self._json_to_workflow(row['definition'])
                return None

        except Exception as e:
            logger.error(f"Failed to load workflow version: {e}")
            raise

    # ========================================================================
    # EXECUTION HISTORY
    # ========================================================================

    def save_execution(self, state: WorkflowState) -> str:
        """Save workflow execution to database"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO workflow_executions
                    (id, workflow_id, status, input_data, output_data, error, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    state.execution_id,
                    state.workflow_id,
                    state.status,
                    json.dumps(state.data.get('input', {})),
                    json.dumps(state.data),
                    state.error,
                    state.started_at.isoformat() if state.started_at else None,
                    state.completed_at.isoformat() if state.completed_at else None
                ))

                # Save execution logs
                for log_entry in state.history:
                    conn.execute("""
                        INSERT INTO execution_logs
                        (execution_id, node_id, node_name, status, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        state.execution_id,
                        log_entry.get('node_id'),
                        log_entry.get('node_name'),
                        log_entry.get('status'),
                        log_entry.get('timestamp')
                    ))

            logger.info(f"Saved execution: {state.execution_id}")
            return state.execution_id

        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
            raise

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution by ID"""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM workflow_executions WHERE id = ?",
                    (execution_id,)
                ).fetchone()

                if row:
                    return dict(row)
                return None

        except Exception as e:
            logger.error(f"Failed to get execution: {e}")
            raise

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List workflow executions"""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM workflow_executions WHERE 1=1"
                params = []

                if workflow_id:
                    query += " AND workflow_id = ?"
                    params.append(workflow_id)

                if status:
                    query += " AND status = ?"
                    params.append(status)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            raise

    # ========================================================================
    # IMPORT/EXPORT
    # ========================================================================

    def export_workflow_to_json(self, workflow_id: str, file_path: str):
        """Export workflow to JSON file"""
        try:
            workflow = self.load_workflow(workflow_id)
            if workflow:
                definition_json = self._workflow_to_json(workflow)

                with open(file_path, 'w') as f:
                    json.dump(json.loads(definition_json), f, indent=2)

                logger.info(f"Exported workflow to: {file_path}")
            else:
                raise ValueError(f"Workflow not found: {workflow_id}")

        except Exception as e:
            logger.error(f"Failed to export workflow: {e}")
            raise

    def import_workflow_from_json(self, file_path: str, user_id: Optional[int] = None) -> str:
        """Import workflow from JSON file"""
        try:
            with open(file_path, 'r') as f:
                definition_dict = json.load(f)

            workflow = self._json_to_workflow(json.dumps(definition_dict))

            # Generate new ID if not present
            if not workflow.id:
                workflow.id = str(uuid4())

            workflow_id = self.save_workflow(workflow, user_id)
            logger.info(f"Imported workflow from: {file_path}")
            return workflow_id

        except Exception as e:
            logger.error(f"Failed to import workflow: {e}")
            raise

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _workflow_to_json(self, workflow: WorkflowDefinition) -> str:
        """Convert WorkflowDefinition to JSON string"""
        return json.dumps({
            'id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'version': workflow.version,
            'nodes': [
                {
                    'id': node.id,
                    'type': node.type,
                    'name': node.name,
                    'config': node.config,
                    'next_nodes': node.next_nodes,
                    'condition': node.condition
                }
                for node in workflow.nodes
            ],
            'edges': [
                {
                    'id': edge.id,
                    'source': edge.source,
                    'target': edge.target,
                    'condition': edge.condition,
                    'label': edge.label
                }
                for edge in workflow.edges
            ],
            'metadata': workflow.metadata
        })

    def _json_to_workflow(self, definition_json: str) -> WorkflowDefinition:
        """Convert JSON string to WorkflowDefinition"""
        data = json.loads(definition_json)

        return WorkflowDefinition(
            id=data.get('id', str(uuid4())),
            name=data['name'],
            description=data.get('description'),
            version=data.get('version', '1.0.0'),
            nodes=[
                WorkflowNode(
                    id=node['id'],
                    type=node['type'],
                    name=node['name'],
                    config=node.get('config', {}),
                    next_nodes=node.get('next_nodes', []),
                    condition=node.get('condition')
                )
                for node in data.get('nodes', [])
            ],
            edges=[
                WorkflowEdge(
                    id=edge['id'],
                    source=edge['source'],
                    target=edge['target'],
                    condition=edge.get('condition'),
                    label=edge.get('label')
                )
                for edge in data.get('edges', [])
            ],
            metadata=data.get('metadata', {})
        )


# ============================================================================
# HITL TASK MANAGEMENT
# ============================================================================

class HITLTaskManager:
    """Manages human-in-the-loop tasks"""

    def __init__(self, db_path: str = "workflows.db"):
        self.db_path = db_path

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_task(
        self,
        execution_id: str,
        node_id: str,
        task_type: str,
        prompt: str,
        data: Dict[str, Any],
        assigned_to: Optional[int] = None
    ) -> str:
        """Create a new HITL task"""
        task_id = str(uuid4())

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO hitl_tasks
                    (id, execution_id, node_id, task_type, prompt, data, assigned_to)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (task_id, execution_id, node_id, task_type, prompt, json.dumps(data), assigned_to))

            logger.info(f"Created HITL task: {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"Failed to create HITL task: {e}")
            raise

    def get_pending_tasks(self, assigned_to: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get pending HITL tasks"""
        try:
            with self._get_connection() as conn:
                if assigned_to:
                    rows = conn.execute("""
                        SELECT * FROM hitl_tasks
                        WHERE status = 'pending' AND (assigned_to = ? OR assigned_to IS NULL)
                        ORDER BY created_at ASC
                    """, (assigned_to,)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT * FROM hitl_tasks
                        WHERE status = 'pending'
                        ORDER BY created_at ASC
                    """).fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get pending tasks: {e}")
            raise

    def respond_to_task(
        self,
        task_id: str,
        status: str,
        response: Dict[str, Any],
        responded_by: Optional[int] = None
    ):
        """Respond to a HITL task"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE hitl_tasks
                    SET status = ?, response = ?, responded_by = ?, responded_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, json.dumps(response), responded_by, task_id))

            logger.info(f"Responded to HITL task: {task_id}")

        except Exception as e:
            logger.error(f"Failed to respond to task: {e}")
            raise


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['WorkflowStorage', 'HITLTaskManager']
