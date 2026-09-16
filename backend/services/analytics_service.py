"""
Analytics Service
Tracks workflow execution metrics and provides analytics data
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid


class AnalyticsService:
    """Service for tracking and retrieving workflow execution analytics"""

    def __init__(self, db_path: str = "backend/database/workflows.db"):
        """Initialize analytics service with database path"""
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Ensure database and analytics tables exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Read and execute schema
        schema_path = Path("backend/database/schema.sql")
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
                cursor.executescript(schema_sql)

        conn.commit()
        conn.close()

    def start_execution(
        self,
        workflow_id: str,
        input_data: Optional[Dict] = None
    ) -> str:
        """
        Start tracking a new workflow execution

        Args:
            workflow_id: ID of the workflow being executed
            input_data: Input data for the execution

        Returns:
            execution_id: Unique ID for this execution
        """
        execution_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO workflow_executions (
                id, workflow_id, status, input_data, started_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            execution_id,
            workflow_id,
            'running',
            json.dumps(input_data) if input_data else None,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return execution_id

    def end_execution(
        self,
        execution_id: str,
        status: str,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """
        Complete a workflow execution

        Args:
            execution_id: ID of the execution
            status: Final status (completed, failed, cancelled)
            output_data: Output data from execution
            error_message: Error message if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get start time to calculate duration
        cursor.execute(
            'SELECT started_at, workflow_id FROM workflow_executions WHERE id = ?',
            (execution_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        started_at_str, workflow_id = row
        started_at = datetime.fromisoformat(started_at_str)
        completed_at = datetime.now()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        # Count node successes and failures
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as succeeded,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM node_executions
            WHERE execution_id = ?
        ''', (execution_id,))

        node_stats = cursor.fetchone()
        node_count = node_stats[0] if node_stats else 0
        nodes_succeeded = node_stats[1] if node_stats else 0
        nodes_failed = node_stats[2] if node_stats else 0

        # Update execution record
        cursor.execute('''
            UPDATE workflow_executions
            SET completed_at = ?,
                status = ?,
                output_data = ?,
                error_message = ?,
                duration_ms = ?,
                node_count = ?,
                nodes_succeeded = ?,
                nodes_failed = ?
            WHERE id = ?
        ''', (
            completed_at.isoformat(),
            status,
            json.dumps(output_data) if output_data else None,
            error_message,
            duration_ms,
            node_count,
            nodes_succeeded,
            nodes_failed,
            execution_id
        ))

        conn.commit()
        conn.close()

        # Update analytics aggregation
        self._update_workflow_analytics(workflow_id)

    def track_node_execution(
        self,
        execution_id: str,
        workflow_id: str,
        node_id: str,
        node_type: str,
        node_label: str,
        status: str,
        duration_ms: int,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """
        Track individual node execution

        Args:
            execution_id: Parent execution ID
            workflow_id: Workflow ID
            node_id: Node ID
            node_type: Type of node
            node_label: Label/name of node
            status: Node execution status
            duration_ms: Execution duration in milliseconds
            input_data: Node input data
            output_data: Node output data
            error_message: Error if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        node_execution_id = str(uuid.uuid4())
        completed_at = datetime.now()
        started_at = completed_at - timedelta(milliseconds=duration_ms)

        cursor.execute('''
            INSERT INTO node_executions (
                id, execution_id, workflow_id, node_id, node_type, node_label,
                started_at, completed_at, status, duration_ms, error_message,
                input_data, output_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node_execution_id,
            execution_id,
            workflow_id,
            node_id,
            node_type,
            node_label,
            started_at.isoformat(),
            completed_at.isoformat(),
            status,
            duration_ms,
            error_message,
            json.dumps(input_data) if input_data else None,
            json.dumps(output_data) if output_data else None
        ))

        conn.commit()
        conn.close()

    def _update_workflow_analytics(self, workflow_id: str):
        """Update aggregated analytics for a workflow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate analytics
        cursor.execute('''
            SELECT
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(duration_ms) as avg_duration,
                MIN(duration_ms) as min_duration,
                MAX(duration_ms) as max_duration,
                MAX(completed_at) as last_execution
            FROM workflow_executions
            WHERE workflow_id = ? AND status != 'running'
        ''', (workflow_id,))

        stats = cursor.fetchone()
        if not stats or not stats[0]:
            conn.close()
            return

        total = stats[0]
        successful = stats[1] or 0
        failed = stats[2] or 0
        avg_duration = stats[3] or 0
        min_duration = stats[4] or 0
        max_duration = stats[5] or 0
        last_execution = stats[6]

        success_rate = (successful / total * 100) if total > 0 else 0

        # Upsert analytics
        cursor.execute('''
            INSERT OR REPLACE INTO workflow_analytics (
                workflow_id, total_executions, successful_executions, failed_executions,
                average_duration_ms, min_duration_ms, max_duration_ms,
                last_execution_at, success_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow_id,
            total,
            successful,
            failed,
            avg_duration,
            min_duration,
            max_duration,
            last_execution,
            success_rate
        ))

        conn.commit()
        conn.close()

    def get_workflow_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get aggregated analytics for a workflow

        Args:
            workflow_id: Workflow ID

        Returns:
            Dictionary with analytics data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get aggregated analytics
        cursor.execute(
            'SELECT * FROM workflow_analytics WHERE workflow_id = ?',
            (workflow_id,)
        )
        analytics_row = cursor.fetchone()

        if not analytics_row:
            # No analytics yet, compute them
            self._update_workflow_analytics(workflow_id)
            cursor.execute(
                'SELECT * FROM workflow_analytics WHERE workflow_id = ?',
                (workflow_id,)
            )
            analytics_row = cursor.fetchone()

        analytics = dict(analytics_row) if analytics_row else {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_duration_ms': 0,
            'min_duration_ms': 0,
            'max_duration_ms': 0,
            'success_rate': 0
        }

        # Get recent executions (last 10)
        cursor.execute('''
            SELECT id, started_at, completed_at, status, duration_ms, error_message,
                   node_count, nodes_succeeded, nodes_failed
            FROM workflow_executions
            WHERE workflow_id = ?
            ORDER BY started_at DESC
            LIMIT 10
        ''', (workflow_id,))

        recent_executions = [dict(row) for row in cursor.fetchall()]

        # Get node-level statistics
        cursor.execute('''
            SELECT
                node_id,
                node_type,
                node_label,
                COUNT(*) as execution_count,
                AVG(duration_ms) as avg_duration,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failure_count
            FROM node_executions
            WHERE workflow_id = ?
            GROUP BY node_id, node_type, node_label
            ORDER BY execution_count DESC
        ''', (workflow_id,))

        node_stats = [dict(row) for row in cursor.fetchall()]

        # Calculate node success rates
        for node in node_stats:
            total = node['execution_count']
            node['success_rate'] = (node['success_count'] / total * 100) if total > 0 else 0

        # Get execution timeline (last 30 days)
        cursor.execute('''
            SELECT
                DATE(started_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM workflow_executions
            WHERE workflow_id = ? AND started_at >= datetime('now', '-30 days')
            GROUP BY DATE(started_at)
            ORDER BY date DESC
        ''', (workflow_id,))

        timeline = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'workflow_id': workflow_id,
            'summary': analytics,
            'recent_executions': recent_executions,
            'node_statistics': node_stats,
            'execution_timeline': timeline
        }

    def get_execution_details(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific execution

        Args:
            execution_id: Execution ID

        Returns:
            Dictionary with execution details including node-level data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get execution info
        cursor.execute(
            'SELECT * FROM workflow_executions WHERE id = ?',
            (execution_id,)
        )
        execution_row = cursor.fetchone()

        if not execution_row:
            conn.close()
            return None

        execution = dict(execution_row)

        # Parse JSON fields
        if execution.get('input_data'):
            try:
                execution['input_data'] = json.loads(execution['input_data'])
            except:
                pass

        if execution.get('output_data'):
            try:
                execution['output_data'] = json.loads(execution['output_data'])
            except:
                pass

        # Get node executions
        cursor.execute('''
            SELECT *
            FROM node_executions
            WHERE execution_id = ?
            ORDER BY started_at ASC
        ''', (execution_id,))

        node_executions = []
        for row in cursor.fetchall():
            node_exec = dict(row)

            # Parse JSON fields
            if node_exec.get('input_data'):
                try:
                    node_exec['input_data'] = json.loads(node_exec['input_data'])
                except:
                    pass

            if node_exec.get('output_data'):
                try:
                    node_exec['output_data'] = json.loads(node_exec['output_data'])
                except:
                    pass

            node_executions.append(node_exec)

        conn.close()

        execution['node_executions'] = node_executions

        return execution

    def get_global_analytics(self) -> Dict[str, Any]:
        """
        Get system-wide analytics across all workflows

        Returns:
            Dictionary with global analytics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Overall statistics
        cursor.execute('''
            SELECT
                COUNT(DISTINCT workflow_id) as total_workflows,
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(duration_ms) as avg_duration,
                SUM(node_count) as total_nodes_executed
            FROM workflow_executions
        ''')

        overall = dict(cursor.fetchone())

        # Most executed workflows
        cursor.execute('''
            SELECT w.id, w.name, COUNT(we.id) as execution_count
            FROM workflows w
            LEFT JOIN workflow_executions we ON w.id = we.workflow_id
            GROUP BY w.id, w.name
            ORDER BY execution_count DESC
            LIMIT 10
        ''')

        top_workflows = [dict(row) for row in cursor.fetchall()]

        # Recent activity
        cursor.execute('''
            SELECT
                DATE(started_at) as date,
                COUNT(*) as executions
            FROM workflow_executions
            WHERE started_at >= datetime('now', '-7 days')
            GROUP BY DATE(started_at)
            ORDER BY date DESC
        ''')

        recent_activity = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'overall_statistics': overall,
            'top_workflows': top_workflows,
            'recent_activity': recent_activity
        }


# Global instance
analytics_service = AnalyticsService()
