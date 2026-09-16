"""
Workflow Storage Service
Manages persistent storage of workflows using SQLite
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import os

class WorkflowStorage:
    def __init__(self, db_path="backend/database/workflows.db"):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Read and execute schema
        schema_path = "backend/database/schema.sql"
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
                cursor.executescript(schema)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def save_workflow(self, workflow_data: Dict, metadata: Optional[Dict] = None) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        metadata = metadata or {}
        workflow_id = metadata.get('id') or str(uuid.uuid4())
        name = metadata.get('name', f'Workflow {workflow_id[:8]}')
        description = metadata.get('description', '')
        author = metadata.get('author', 'Anonymous')
        tags = json.dumps(metadata.get('tags', []))
        category = metadata.get('category', 'Custom')
        is_template = metadata.get('is_template', False)
        
        cursor.execute("SELECT id, version FROM workflows WHERE id = ?", (workflow_id,))
        existing = cursor.fetchone()
        
        if existing:
            version = existing['version'] + 1
            cursor.execute("""
                UPDATE workflows 
                SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP,
                    version = ?, author = ?, tags = ?, category = ?
                WHERE id = ?
            """, (name, description, version, author, tags, category, workflow_id))
        else:
            version = 1
            cursor.execute("""
                INSERT INTO workflows (id, name, description, version, author, tags, is_template, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (workflow_id, name, description, version, author, tags, is_template, category))
        
        version_id = str(uuid.uuid4())
        workflow_json = json.dumps(workflow_data)
        change_description = metadata.get('change_description', 'Workflow updated')
        
        cursor.execute("""
            INSERT INTO workflow_versions (id, workflow_id, version, workflow_data, change_description)
            VALUES (?, ?, ?, ?, ?)
        """, (version_id, workflow_id, version, workflow_json, change_description))
        
        conn.commit()
        conn.close()

        return workflow_id

    def list_workflows(self, category: Optional[str] = None, is_template: Optional[bool] = None) -> List[Dict]:
        """List all workflows with optional filtering"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM workflows WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if is_template is not None:
            query += " AND is_template = ?"
            params.append(1 if is_template else 0)

        query += " ORDER BY updated_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_workflow(self, workflow_id: str, version: Optional[int] = None) -> Optional[Dict]:
        """Get a specific workflow by ID and optionally by version"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get workflow metadata
        cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        workflow_row = cursor.fetchone()

        if not workflow_row:
            conn.close()
            return None

        workflow = dict(workflow_row)

        # Get workflow data from versions table
        if version:
            cursor.execute("""
                SELECT workflow_data, version, created_at, change_description
                FROM workflow_versions
                WHERE workflow_id = ? AND version = ?
            """, (workflow_id, version))
        else:
            cursor.execute("""
                SELECT workflow_data, version, created_at, change_description
                FROM workflow_versions
                WHERE workflow_id = ?
                ORDER BY version DESC
                LIMIT 1
            """, (workflow_id,))

        version_row = cursor.fetchone()
        conn.close()

        if not version_row:
            return workflow

        workflow_data = json.loads(version_row['workflow_data'])
        workflow['workflow_data'] = workflow_data
        workflow['current_version'] = version_row['version']
        workflow['version_created_at'] = version_row['created_at']
        workflow['change_description'] = version_row['change_description']

        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow and all its versions"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def get_workflow_versions(self, workflow_id: str) -> List[Dict]:
        """Get all versions of a workflow"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, version, created_at, change_description
            FROM workflow_versions
            WHERE workflow_id = ?
            ORDER BY version DESC
        """, (workflow_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def search_workflows(self, query: str) -> List[Dict]:
        """Search workflows by name or description"""
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM workflows
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY updated_at DESC
        """, (search_pattern, search_pattern))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def record_execution(self, workflow_id: str, input_data: Dict,
                        output_data: Optional[Dict] = None,
                        status: str = 'running',
                        error_message: Optional[str] = None) -> str:
        """Record a workflow execution"""
        conn = self._get_connection()
        cursor = conn.cursor()

        execution_id = str(uuid.uuid4())
        input_json = json.dumps(input_data)
        output_json = json.dumps(output_data) if output_data else None

        cursor.execute("""
            INSERT INTO workflow_executions
            (id, workflow_id, status, input_data, output_data, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (execution_id, workflow_id, status, input_json, output_json, error_message))

        conn.commit()
        conn.close()

        return execution_id

    def update_execution(self, execution_id: str, output_data: Optional[Dict] = None,
                        status: str = 'completed', error_message: Optional[str] = None,
                        duration_ms: Optional[int] = None):
        """Update an execution record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        output_json = json.dumps(output_data) if output_data else None

        cursor.execute("""
            UPDATE workflow_executions
            SET completed_at = CURRENT_TIMESTAMP,
                output_data = ?,
                status = ?,
                error_message = ?,
                duration_ms = ?
            WHERE id = ?
        """, (output_json, status, error_message, duration_ms, execution_id))

        conn.commit()
        conn.close()

    def get_workflow_executions(self, workflow_id: str, limit: int = 50) -> List[Dict]:
        """Get execution history for a workflow"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM workflow_executions
            WHERE workflow_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (workflow_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

# Global instance
workflow_storage = WorkflowStorage()
