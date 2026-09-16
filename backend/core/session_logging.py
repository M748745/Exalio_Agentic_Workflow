"""
Comprehensive Logging & Session Management (AI Planet Feature)
Features:
- Build Logs (component initialization, data loading)
- Chain Logs (execution flow, model inference, inputs/outputs)
- Session Management (workflow executions with unique IDs)
- Performance tracking
- Audit trail
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogType(str, Enum):
    """Types of logs"""
    BUILD = "build"  # Component initialization, data loading
    CHAIN = "chain"  # Execution flow, model inference
    AUDIT = "audit"  # Security, compliance events
    PERFORMANCE = "performance"  # Timing, resource usage


@dataclass
class LogEntry:
    """Single log entry"""
    timestamp: datetime
    session_id: str
    log_type: LogType
    level: LogLevel
    component: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[float] = None


@dataclass
class Session:
    """Workflow execution session"""
    session_id: str
    workflow_id: str
    workflow_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, paused
    user_id: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    total_execution_time_ms: Optional[float] = None
    nodes_executed: int = 0
    errors: List[str] = field(default_factory=list)


class SessionLogger:
    """
    Comprehensive logging and session management system
    AI Planet Feature: Detailed tracking for debugging and compliance
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self._sessions: Dict[str, Session] = {}
        self._logs: Dict[str, List[LogEntry]] = {}  # session_id -> logs

        self._current_session_id: Optional[str] = None

    def create_session(
        self,
        workflow_id: str,
        workflow_name: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Create a new session for workflow execution"""

        session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            started_at=datetime.utcnow(),
            user_id=user_id,
            input_data=input_data
        )

        self._sessions[session_id] = session
        self._logs[session_id] = []
        self._current_session_id = session_id

        logger.info(f"Created session: {session_id} for workflow: {workflow_name}")

        return session_id

    def log_build(
        self,
        component: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        session_id: Optional[str] = None,
        **metadata
    ):
        """Log build/initialization events"""

        self._add_log(
            log_type=LogType.BUILD,
            level=level,
            component=component,
            message=message,
            session_id=session_id,
            metadata=metadata
        )

    def log_chain(
        self,
        component: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        session_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        **metadata
    ):
        """Log chain execution events (node execution, model inference)"""

        self._add_log(
            log_type=LogType.CHAIN,
            level=level,
            component=component,
            message=message,
            session_id=session_id,
            execution_time_ms=execution_time_ms,
            metadata=metadata
        )

    def log_audit(
        self,
        component: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        session_id: Optional[str] = None,
        **metadata
    ):
        """Log audit/security events"""

        self._add_log(
            log_type=LogType.AUDIT,
            level=level,
            component=component,
            message=message,
            session_id=session_id,
            metadata=metadata
        )

    def log_performance(
        self,
        component: str,
        message: str,
        execution_time_ms: float,
        session_id: Optional[str] = None,
        **metadata
    ):
        """Log performance metrics"""

        self._add_log(
            log_type=LogType.PERFORMANCE,
            level=LogLevel.INFO,
            component=component,
            message=message,
            session_id=session_id,
            execution_time_ms=execution_time_ms,
            metadata=metadata
        )

    def _add_log(
        self,
        log_type: LogType,
        level: LogLevel,
        component: str,
        message: str,
        session_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        metadata: Dict[str, Any] = None
    ):
        """Add a log entry"""

        session_id = session_id or self._current_session_id

        if not session_id:
            logger.warning("No session ID available for logging")
            return

        log_entry = LogEntry(
            timestamp=datetime.utcnow(),
            session_id=session_id,
            log_type=log_type,
            level=level,
            component=component,
            message=message,
            metadata=metadata or {},
            execution_time_ms=execution_time_ms
        )

        if session_id not in self._logs:
            self._logs[session_id] = []

        self._logs[session_id].append(log_entry)

        # Also log to standard logger
        log_func = getattr(logger, level.value)
        log_func(f"[{log_type.value.upper()}] {component}: {message}")

    def complete_session(
        self,
        session_id: str,
        output_data: Dict[str, Any],
        status: str = "completed"
    ):
        """Mark session as completed"""

        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return

        session = self._sessions[session_id]
        session.completed_at = datetime.utcnow()
        session.status = status
        session.output_data = output_data

        # Calculate total execution time
        if session.started_at:
            elapsed = (session.completed_at - session.started_at).total_seconds() * 1000
            session.total_execution_time_ms = elapsed

        logger.info(f"Session completed: {session_id} ({status}) in {session.total_execution_time_ms:.2f}ms")

        # Save session to file
        self._save_session(session_id)

    def fail_session(self, session_id: str, error: str):
        """Mark session as failed"""

        if session_id not in self._sessions:
            return

        session = self._sessions[session_id]
        session.status = "failed"
        session.errors.append(error)
        session.completed_at = datetime.utcnow()

        if session.started_at:
            elapsed = (session.completed_at - session.started_at).total_seconds() * 1000
            session.total_execution_time_ms = elapsed

        logger.error(f"Session failed: {session_id} - {error}")

        self._save_session(session_id)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self._sessions.get(session_id)

    def get_session_logs(
        self,
        session_id: str,
        log_type: Optional[LogType] = None,
        level: Optional[LogLevel] = None
    ) -> List[LogEntry]:
        """Get logs for a session"""

        logs = self._logs.get(session_id, [])

        # Filter by type
        if log_type:
            logs = [l for l in logs if l.log_type == log_type]

        # Filter by level
        if level:
            logs = [l for l in logs if l.level == level]

        return logs

    def get_build_logs(self, session_id: str) -> List[LogEntry]:
        """Get build logs for session"""
        return self.get_session_logs(session_id, log_type=LogType.BUILD)

    def get_chain_logs(self, session_id: str) -> List[LogEntry]:
        """Get chain execution logs for session"""
        return self.get_session_logs(session_id, log_type=LogType.CHAIN)

    def get_audit_logs(self, session_id: str) -> List[LogEntry]:
        """Get audit logs for session"""
        return self.get_session_logs(session_id, log_type=LogType.AUDIT)

    def _save_session(self, session_id: str):
        """Save session to file"""

        session = self._sessions.get(session_id)
        if not session:
            return

        logs = self._logs.get(session_id, [])

        session_data = {
            "session": {
                "session_id": session.session_id,
                "workflow_id": session.workflow_id,
                "workflow_name": session.workflow_name,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "status": session.status,
                "user_id": session.user_id,
                "total_execution_time_ms": session.total_execution_time_ms,
                "nodes_executed": session.nodes_executed,
                "errors": session.errors
            },
            "logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "log_type": log.log_type.value,
                    "level": log.level.value,
                    "component": log.component,
                    "message": log.message,
                    "metadata": log.metadata,
                    "execution_time_ms": log.execution_time_ms
                }
                for log in logs
            ]
        }

        # Save to file
        session_file = self.log_dir / f"session_{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        logger.debug(f"Session saved to: {session_file}")

    def export_logs(self, session_id: str, format: str = "json") -> str:
        """Export logs in various formats"""

        logs = self._logs.get(session_id, [])

        if format == "json":
            return json.dumps([
                {
                    "timestamp": log.timestamp.isoformat(),
                    "type": log.log_type.value,
                    "level": log.level.value,
                    "component": log.component,
                    "message": log.message,
                    "execution_time_ms": log.execution_time_ms
                }
                for log in logs
            ], indent=2)

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(["timestamp", "type", "level", "component", "message", "execution_time_ms"])

            for log in logs:
                writer.writerow([
                    log.timestamp.isoformat(),
                    log.log_type.value,
                    log.level.value,
                    log.component,
                    log.message,
                    log.execution_time_ms or ""
                ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}")


# Global session logger
session_logger = SessionLogger()
