"""
Step Executor Service

Manages step-by-step workflow execution sessions.
Provides API for creating sessions, executing steps, and managing session state.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models.execution_session import ExecutionSession


class StepExecutor:
    """Manages step-by-step workflow execution"""

    def __init__(self):
        """Initialize step executor with session storage"""
        self.sessions: Dict[str, ExecutionSession] = {}
        self.session_timeout = timedelta(hours=2)  # Sessions expire after 2 hours

    def create_session(self, workflow: Dict[str, Any], inputs: Dict[str, Any]) -> str:
        """
        Create new execution session

        Args:
            workflow: Workflow definition with nodes and edges
            inputs: Initial input values

        Returns:
            session_id: Unique session identifier
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()

        # Create new session
        session = ExecutionSession(workflow, inputs)
        session_id = session.session_id

        # Store session
        self.sessions[session_id] = session

        return session_id

    def execute_next_step(self, session_id: str) -> Dict[str, Any]:
        """
        Execute next node in workflow

        Args:
            session_id: Session identifier

        Returns:
            Execution result with node info and status

        Raises:
            ValueError: If session not found
        """
        session = self._get_session(session_id)

        # Check if already completed
        if session.is_complete():
            return {
                'session_id': session_id,
                'status': 'completed',
                'completed': True,
                'message': 'Workflow execution already complete'
            }

        # Get next node
        next_node = session.get_next_node()
        if not next_node:
            session.status = 'completed'
            return {
                'session_id': session_id,
                'status': 'completed',
                'completed': True,
                'message': 'No more nodes to execute'
            }

        # Execute node
        try:
            result = session.execute_node(next_node)

            return {
                'session_id': session_id,
                'node_id': next_node['id'],
                'node_label': next_node.get('data', {}).get('label', next_node['id']),
                'node_type': next_node.get('type', ''),
                'result': result,
                'status': session.status,
                'progress': {
                    'current': session.current_index,
                    'total': len(session.pending_nodes),
                    'percentage': int((session.current_index / len(session.pending_nodes)) * 100)
                },
                'completed': session.is_complete()
            }

        except Exception as e:
            return {
                'session_id': session_id,
                'node_id': next_node['id'],
                'status': 'error',
                'error': str(e),
                'completed': False
            }

    def execute_all_steps(self, session_id: str) -> Dict[str, Any]:
        """
        Execute all remaining steps in workflow

        Args:
            session_id: Session identifier

        Returns:
            Final execution result

        Raises:
            ValueError: If session not found
        """
        session = self._get_session(session_id)

        step_results = []
        while not session.is_complete():
            step_result = self.execute_next_step(session_id)
            step_results.append(step_result)

            # Stop on error
            if step_result.get('status') == 'error':
                break

        return {
            'session_id': session_id,
            'status': session.status,
            'steps': step_results,
            'total_steps': len(step_results),
            'completed': session.is_complete(),
            'results': session.results
        }

    def pause_session(self, session_id: str) -> Dict[str, Any]:
        """
        Pause execution

        Args:
            session_id: Session identifier

        Returns:
            Session status

        Raises:
            ValueError: If session not found
        """
        session = self._get_session(session_id)
        session.pause()

        return {
            'session_id': session_id,
            'status': session.status,
            'message': 'Session paused'
        }

    def resume_session(self, session_id: str) -> Dict[str, Any]:
        """
        Resume execution

        Args:
            session_id: Session identifier

        Returns:
            Session status

        Raises:
            ValueError: If session not found
        """
        session = self._get_session(session_id)
        session.resume()

        return {
            'session_id': session_id,
            'status': session.status,
            'message': 'Session resumed'
        }

    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session state

        Args:
            session_id: Session identifier

        Returns:
            Complete session state

        Raises:
            ValueError: If session not found
        """
        session = self._get_session(session_id)
        return session.to_dict()

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete session

        Args:
            session_id: Session identifier

        Returns:
            Deletion confirmation

        Raises:
            ValueError: If session not found
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        del self.sessions[session_id]

        return {
            'session_id': session_id,
            'status': 'deleted',
            'message': 'Session deleted successfully'
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active sessions

        Returns:
            List of session summaries
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()

        sessions_list = []
        for session_id, session in self.sessions.items():
            sessions_list.append({
                'session_id': session_id,
                'status': session.status,
                'progress': {
                    'current': session.current_index,
                    'total': len(session.pending_nodes)
                },
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'completed': session.is_complete()
            })

        return sessions_list

    def _get_session(self, session_id: str) -> ExecutionSession:
        """
        Get session by ID

        Args:
            session_id: Session identifier

        Returns:
            ExecutionSession instance

        Raises:
            ValueError: If session not found
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        return self.sessions[session_id]

    def _cleanup_expired_sessions(self):
        """Remove sessions older than timeout"""
        now = datetime.utcnow()
        expired_ids = []

        for session_id, session in self.sessions.items():
            if session.updated_at:
                age = now - session.updated_at
                if age > self.session_timeout:
                    expired_ids.append(session_id)

        # Delete expired sessions
        for session_id in expired_ids:
            del self.sessions[session_id]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get executor statistics

        Returns:
            Statistics about active sessions
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()

        total_sessions = len(self.sessions)
        running_sessions = sum(1 for s in self.sessions.values() if s.status == 'running')
        paused_sessions = sum(1 for s in self.sessions.values() if s.status == 'paused')
        completed_sessions = sum(1 for s in self.sessions.values() if s.is_complete())
        error_sessions = sum(1 for s in self.sessions.values() if s.status == 'error')

        return {
            'total_sessions': total_sessions,
            'running_sessions': running_sessions,
            'paused_sessions': paused_sessions,
            'completed_sessions': completed_sessions,
            'error_sessions': error_sessions,
            'timeout_minutes': int(self.session_timeout.total_seconds() / 60)
        }


# Global singleton instance
step_executor = StepExecutor()
