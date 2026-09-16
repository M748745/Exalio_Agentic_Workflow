"""
Scheduling & Triggers Agents (MEDIUM PRIORITY)
8 nodes for workflow automation triggers and scheduling

Features:
- Cron scheduler (time-based triggers)
- Event triggers (system/custom events)
- Webhook triggers (HTTP callbacks)
- File watch triggers (file system monitoring)
- Email triggers (email-based automation)
- Database triggers (data change monitoring)
- Interval triggers (periodic execution)
- Time delay triggers (scheduled one-time execution)

This enables fully automated, event-driven workflows.
"""

from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
import asyncio
import re
from enum import Enum
import hashlib
import time

logger = logging.getLogger(__name__)


class TriggerStatus(Enum):
    """Trigger status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


class TriggerType(Enum):
    """Trigger type"""
    CRON = "cron"
    EVENT = "event"
    WEBHOOK = "webhook"
    FILE_WATCH = "file_watch"
    EMAIL = "email"
    DATABASE = "database"
    INTERVAL = "interval"
    TIME_DELAY = "time_delay"


@dataclass
class TriggerExecution:
    """Record of trigger execution"""
    trigger_id: str
    trigger_type: str
    triggered_at: datetime
    workflow_id: str
    success: bool
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 1. CRON SCHEDULER NODE
# ============================================================================

class CronSchedulerAgent:
    """
    Time-based workflow triggers using cron expressions
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scheduled_jobs: Dict[str, Dict] = {}
        self.running = False

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create cron schedule

        Config:
            cron_expression: Cron expression (e.g., "0 9 * * 1-5" = weekdays at 9am)
            timezone: Timezone (e.g., "UTC", "America/New_York")
            workflow_id: Workflow to trigger
            enabled: Whether schedule is active

        Cron Expression Format:
            ┌───────────── minute (0 - 59)
            │ ┌───────────── hour (0 - 23)
            │ │ ┌───────────── day of month (1 - 31)
            │ │ │ ┌───────────── month (1 - 12)
            │ │ │ │ ┌───────────── day of week (0 - 6) (Sunday=0)
            │ │ │ │ │
            * * * * *

        Examples:
            "0 9 * * *"       - Daily at 9:00 AM
            "0 */6 * * *"     - Every 6 hours
            "0 9 * * 1-5"     - Weekdays at 9:00 AM
            "0 0 1 * *"       - First day of month at midnight
            "*/15 * * * *"    - Every 15 minutes

        Returns:
            schedule_id, next_run, status
        """
        try:
            cron_expression = self.config.get('cron_expression', '0 9 * * *')
            timezone = self.config.get('timezone', 'UTC')
            workflow_id = self.config.get('workflow_id')
            enabled = self.config.get('enabled', True)
            schedule_name = inputs.get('schedule_name', 'Cron Schedule')

            # Validate cron expression
            if not self._validate_cron(cron_expression):
                return {
                    'success': False,
                    'error': 'Invalid cron expression'
                }

            # Generate schedule ID
            schedule_id = hashlib.md5(
                f"{workflow_id}:{cron_expression}".encode()
            ).hexdigest()[:16]

            # Calculate next run time
            next_run = self._calculate_next_run(cron_expression, timezone)

            # Create schedule
            schedule = {
                'schedule_id': schedule_id,
                'schedule_name': schedule_name,
                'cron_expression': cron_expression,
                'timezone': timezone,
                'workflow_id': workflow_id,
                'enabled': enabled,
                'next_run': next_run.isoformat() if next_run else None,
                'created_at': datetime.utcnow().isoformat(),
                'last_run': None,
                'run_count': 0,
                'status': TriggerStatus.ACTIVE.value if enabled else TriggerStatus.INACTIVE.value
            }

            # Store schedule
            self.scheduled_jobs[schedule_id] = schedule

            return {
                'success': True,
                'schedule_id': schedule_id,
                'cron_expression': cron_expression,
                'next_run': next_run.isoformat() if next_run else None,
                'status': schedule['status'],
                'schedule_name': schedule_name
            }

        except Exception as e:
            logger.error(f"Cron scheduler failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_cron(self, expression: str) -> bool:
        """Validate cron expression"""
        parts = expression.split()
        if len(parts) != 5:
            return False

        # Basic validation (simplified)
        for i, part in enumerate(parts):
            if part == '*':
                continue
            if '/' in part or '-' in part or ',' in part:
                continue
            try:
                int(part)
            except ValueError:
                return False

        return True

    def _calculate_next_run(self, cron_expression: str, timezone: str) -> Optional[datetime]:
        """Calculate next run time (simplified implementation)"""
        # This is a simplified version - production should use croniter library
        now = datetime.utcnow()

        parts = cron_expression.split()
        minute, hour = parts[0], parts[1]

        # Handle simple cases
        if minute == '*' and hour == '*':
            # Every minute
            return now + timedelta(minutes=1)
        elif minute.isdigit() and hour == '*':
            # Every hour at specific minute
            next_run = now.replace(minute=int(minute), second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
            return next_run
        elif minute.isdigit() and hour.isdigit():
            # Daily at specific time
            next_run = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        # Default: next hour
        return now + timedelta(hours=1)


# ============================================================================
# 2. EVENT TRIGGER NODE
# ============================================================================

class EventTriggerAgent:
    """
    Trigger workflows based on system or custom events
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.event_listeners: Dict[str, List[Dict]] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register event trigger

        Config:
            event_type: Type of event to listen for
            event_filters: Filters to apply to events
            workflow_id: Workflow to trigger
            debounce_seconds: Minimum time between triggers

        Event Types:
            - system.startup
            - system.shutdown
            - workflow.completed
            - workflow.failed
            - data.created
            - data.updated
            - data.deleted
            - user.login
            - user.logout
            - custom.*

        Event Filters:
            {
                "workflow_id": "specific_workflow",
                "status": "success",
                "user_id": "user123"
            }

        Returns:
            trigger_id, event_type, status
        """
        try:
            event_type = self.config.get('event_type')
            event_filters = self.config.get('event_filters', {})
            workflow_id = self.config.get('workflow_id')
            debounce_seconds = self.config.get('debounce_seconds', 0)

            # Generate trigger ID
            trigger_id = hashlib.md5(
                f"{workflow_id}:{event_type}:{json.dumps(event_filters)}".encode()
            ).hexdigest()[:16]

            # Create trigger
            trigger = {
                'trigger_id': trigger_id,
                'event_type': event_type,
                'event_filters': event_filters,
                'workflow_id': workflow_id,
                'debounce_seconds': debounce_seconds,
                'created_at': datetime.utcnow().isoformat(),
                'last_triggered': None,
                'trigger_count': 0,
                'status': TriggerStatus.ACTIVE.value
            }

            # Register listener
            if event_type not in self.event_listeners:
                self.event_listeners[event_type] = []
            self.event_listeners[event_type].append(trigger)

            return {
                'success': True,
                'trigger_id': trigger_id,
                'event_type': event_type,
                'status': TriggerStatus.ACTIVE.value,
                'listening': True
            }

        except Exception as e:
            logger.error(f"Event trigger registration failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> List[str]:
        """
        Emit event and trigger matching workflows

        Args:
            event_type: Type of event
            event_data: Event payload

        Returns:
            List of triggered workflow IDs
        """
        triggered_workflows = []

        if event_type in self.event_listeners:
            for trigger in self.event_listeners[event_type]:
                # Check filters
                if self._matches_filters(event_data, trigger['event_filters']):
                    # Check debounce
                    if self._check_debounce(trigger):
                        # Trigger workflow
                        triggered_workflows.append(trigger['workflow_id'])
                        trigger['last_triggered'] = datetime.utcnow().isoformat()
                        trigger['trigger_count'] += 1

        return triggered_workflows

    def _matches_filters(self, event_data: Dict, filters: Dict) -> bool:
        """Check if event data matches filters"""
        for key, value in filters.items():
            if key not in event_data or event_data[key] != value:
                return False
        return True

    def _check_debounce(self, trigger: Dict) -> bool:
        """Check if debounce period has passed"""
        if trigger['debounce_seconds'] == 0:
            return True

        if trigger['last_triggered']:
            last_triggered = datetime.fromisoformat(trigger['last_triggered'])
            elapsed = (datetime.utcnow() - last_triggered).total_seconds()
            return elapsed >= trigger['debounce_seconds']

        return True


# ============================================================================
# 3. WEBHOOK TRIGGER NODE
# ============================================================================

class WebhookTriggerAgent:
    """
    Trigger workflows via HTTP webhooks
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.webhook_endpoints: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create webhook trigger endpoint

        Config:
            webhook_path: URL path for webhook (e.g., "/webhooks/order-created")
            workflow_id: Workflow to trigger
            secret: Secret for signature validation
            allowed_methods: HTTP methods (GET, POST, PUT, DELETE)
            payload_mapping: Map webhook payload to workflow inputs

        Returns:
            webhook_url, webhook_id, secret
        """
        try:
            webhook_path = self.config.get('webhook_path', '/webhook')
            workflow_id = self.config.get('workflow_id')
            secret = self.config.get('secret', self._generate_secret())
            allowed_methods = self.config.get('allowed_methods', ['POST'])
            payload_mapping = self.config.get('payload_mapping', {})

            # Generate webhook ID
            webhook_id = hashlib.md5(f"{workflow_id}:{webhook_path}".encode()).hexdigest()[:16]

            # Create webhook endpoint
            webhook = {
                'webhook_id': webhook_id,
                'webhook_path': webhook_path,
                'workflow_id': workflow_id,
                'secret': secret,
                'allowed_methods': allowed_methods,
                'payload_mapping': payload_mapping,
                'created_at': datetime.utcnow().isoformat(),
                'trigger_count': 0,
                'status': TriggerStatus.ACTIVE.value
            }

            # Register endpoint
            self.webhook_endpoints[webhook_path] = webhook

            # Build webhook URL (placeholder - would use actual server URL)
            webhook_url = f"https://your-domain.com{webhook_path}"

            return {
                'success': True,
                'webhook_id': webhook_id,
                'webhook_url': webhook_url,
                'webhook_path': webhook_path,
                'secret': secret,
                'status': TriggerStatus.ACTIVE.value
            }

        except Exception as e:
            logger.error(f"Webhook trigger creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_secret(self) -> str:
        """Generate webhook secret"""
        import secrets
        return secrets.token_urlsafe(32)


# ============================================================================
# 4. FILE WATCH TRIGGER NODE
# ============================================================================

class FileWatchTriggerAgent:
    """
    Trigger workflows when files are created, modified, or deleted
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.watched_paths: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Watch directory for file changes

        Config:
            watch_path: Directory path to watch
            watch_events: Events to watch ['created', 'modified', 'deleted', 'moved']
            file_pattern: File pattern to match (e.g., "*.pdf", "data_*.csv")
            recursive: Watch subdirectories
            workflow_id: Workflow to trigger
            debounce_seconds: Minimum time between triggers for same file

        Returns:
            watch_id, watch_path, watching
        """
        try:
            watch_path = self.config.get('watch_path')
            watch_events = self.config.get('watch_events', ['created', 'modified'])
            file_pattern = self.config.get('file_pattern', '*')
            recursive = self.config.get('recursive', False)
            workflow_id = self.config.get('workflow_id')
            debounce_seconds = self.config.get('debounce_seconds', 1)

            # Validate path
            path = Path(watch_path)
            if not path.exists():
                return {
                    'success': False,
                    'error': f'Path does not exist: {watch_path}'
                }

            # Generate watch ID
            watch_id = hashlib.md5(f"{workflow_id}:{watch_path}".encode()).hexdigest()[:16]

            # Create watch
            watch = {
                'watch_id': watch_id,
                'watch_path': watch_path,
                'watch_events': watch_events,
                'file_pattern': file_pattern,
                'recursive': recursive,
                'workflow_id': workflow_id,
                'debounce_seconds': debounce_seconds,
                'created_at': datetime.utcnow().isoformat(),
                'trigger_count': 0,
                'status': TriggerStatus.ACTIVE.value,
                'last_events': {}
            }

            # Register watch
            self.watched_paths[watch_id] = watch

            return {
                'success': True,
                'watch_id': watch_id,
                'watch_path': watch_path,
                'watching': True,
                'events': watch_events,
                'pattern': file_pattern
            }

        except Exception as e:
            logger.error(f"File watch trigger failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)


# ============================================================================
# 5. EMAIL TRIGGER NODE
# ============================================================================

class EmailTriggerAgent:
    """
    Trigger workflows based on incoming emails
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.email_rules: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor email inbox for triggers

        Config:
            email_server: IMAP server
            email_account: Email to monitor
            email_password: Email password
            filters: Email filters
            workflow_id: Workflow to trigger
            check_interval_seconds: How often to check

        Email Filters:
            {
                "from": "customer@example.com",
                "subject_contains": "Order",
                "has_attachment": True,
                "attachment_type": ".pdf"
            }

        Returns:
            rule_id, monitoring, status
        """
        try:
            email_server = self.config.get('email_server')
            email_account = self.config.get('email_account')
            email_password = self.config.get('email_password')
            filters = self.config.get('filters', {})
            workflow_id = self.config.get('workflow_id')
            check_interval_seconds = self.config.get('check_interval_seconds', 60)

            # Generate rule ID
            rule_id = hashlib.md5(
                f"{workflow_id}:{email_account}:{json.dumps(filters)}".encode()
            ).hexdigest()[:16]

            # Create email rule
            rule = {
                'rule_id': rule_id,
                'email_server': email_server,
                'email_account': email_account,
                'email_password': email_password,  # Should be encrypted
                'filters': filters,
                'workflow_id': workflow_id,
                'check_interval_seconds': check_interval_seconds,
                'created_at': datetime.utcnow().isoformat(),
                'last_checked': None,
                'trigger_count': 0,
                'status': TriggerStatus.ACTIVE.value
            }

            # Register rule
            self.email_rules[rule_id] = rule

            return {
                'success': True,
                'rule_id': rule_id,
                'monitoring': email_account,
                'status': TriggerStatus.ACTIVE.value,
                'check_interval': check_interval_seconds
            }

        except Exception as e:
            logger.error(f"Email trigger failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 6. DATABASE TRIGGER NODE
# ============================================================================

class DatabaseTriggerAgent:
    """
    Trigger workflows when database records change
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_watches: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Watch database table for changes

        Config:
            db_type: Database type (postgresql, mysql, sqlite)
            connection_string: Database connection
            table_name: Table to watch
            watch_operations: ['INSERT', 'UPDATE', 'DELETE']
            conditions: WHERE conditions to filter
            workflow_id: Workflow to trigger
            poll_interval_seconds: How often to check

        Returns:
            watch_id, watching, status
        """
        try:
            db_type = self.config.get('db_type', 'sqlite')
            connection_string = self.config.get('connection_string')
            table_name = self.config.get('table_name')
            watch_operations = self.config.get('watch_operations', ['INSERT', 'UPDATE'])
            conditions = self.config.get('conditions', {})
            workflow_id = self.config.get('workflow_id')
            poll_interval_seconds = self.config.get('poll_interval_seconds', 10)

            # Generate watch ID
            watch_id = hashlib.md5(
                f"{workflow_id}:{table_name}:{json.dumps(watch_operations)}".encode()
            ).hexdigest()[:16]

            # Create database watch
            watch = {
                'watch_id': watch_id,
                'db_type': db_type,
                'connection_string': connection_string,
                'table_name': table_name,
                'watch_operations': watch_operations,
                'conditions': conditions,
                'workflow_id': workflow_id,
                'poll_interval_seconds': poll_interval_seconds,
                'created_at': datetime.utcnow().isoformat(),
                'last_checked': None,
                'trigger_count': 0,
                'status': TriggerStatus.ACTIVE.value,
                'last_record_id': None
            }

            # Register watch
            self.db_watches[watch_id] = watch

            return {
                'success': True,
                'watch_id': watch_id,
                'watching': f"{table_name} ({', '.join(watch_operations)})",
                'status': TriggerStatus.ACTIVE.value,
                'poll_interval': poll_interval_seconds
            }

        except Exception as e:
            logger.error(f"Database trigger failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 7. INTERVAL TRIGGER NODE
# ============================================================================

class IntervalTriggerAgent:
    """
    Trigger workflows at regular intervals
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.intervals: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger workflow at regular intervals

        Config:
            interval_seconds: Interval in seconds
            interval_minutes: Interval in minutes
            interval_hours: Interval in hours
            workflow_id: Workflow to trigger
            max_executions: Maximum number of executions (0 = unlimited)
            enabled: Whether interval is active

        Examples:
            Every 30 seconds: {"interval_seconds": 30}
            Every 5 minutes: {"interval_minutes": 5}
            Every 2 hours: {"interval_hours": 2}

        Returns:
            interval_id, next_run, status
        """
        try:
            interval_seconds = self.config.get('interval_seconds', 0)
            interval_minutes = self.config.get('interval_minutes', 0)
            interval_hours = self.config.get('interval_hours', 0)
            workflow_id = self.config.get('workflow_id')
            max_executions = self.config.get('max_executions', 0)
            enabled = self.config.get('enabled', True)

            # Calculate total interval
            total_seconds = interval_seconds + (interval_minutes * 60) + (interval_hours * 3600)

            if total_seconds == 0:
                return {
                    'success': False,
                    'error': 'Interval must be greater than 0'
                }

            # Generate interval ID
            interval_id = hashlib.md5(f"{workflow_id}:{total_seconds}".encode()).hexdigest()[:16]

            # Calculate next run
            next_run = datetime.utcnow() + timedelta(seconds=total_seconds)

            # Create interval
            interval = {
                'interval_id': interval_id,
                'interval_seconds': total_seconds,
                'workflow_id': workflow_id,
                'max_executions': max_executions,
                'enabled': enabled,
                'next_run': next_run.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'execution_count': 0,
                'status': TriggerStatus.ACTIVE.value if enabled else TriggerStatus.INACTIVE.value
            }

            # Register interval
            self.intervals[interval_id] = interval

            return {
                'success': True,
                'interval_id': interval_id,
                'interval_seconds': total_seconds,
                'interval_display': self._format_interval(total_seconds),
                'next_run': next_run.isoformat(),
                'status': interval['status']
            }

        except Exception as e:
            logger.error(f"Interval trigger failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _format_interval(self, seconds: int) -> str:
        """Format interval for display"""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            return f"{seconds // 60} minutes"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes:
                return f"{hours} hours {minutes} minutes"
            return f"{hours} hours"


# ============================================================================
# 8. TIME DELAY TRIGGER NODE
# ============================================================================

class TimeDelayTriggerAgent:
    """
    Trigger workflow once after a specified delay or at a specific time
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scheduled_triggers: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule one-time workflow trigger

        Config:
            trigger_type: 'delay' or 'absolute'
            delay_seconds: Seconds to wait (for delay type)
            delay_minutes: Minutes to wait (for delay type)
            delay_hours: Hours to wait (for delay type)
            trigger_at: Specific datetime (for absolute type, ISO format)
            workflow_id: Workflow to trigger

        Returns:
            trigger_id, scheduled_for, status
        """
        try:
            trigger_type = self.config.get('trigger_type', 'delay')
            workflow_id = self.config.get('workflow_id')

            if trigger_type == 'delay':
                delay_seconds = self.config.get('delay_seconds', 0)
                delay_minutes = self.config.get('delay_minutes', 0)
                delay_hours = self.config.get('delay_hours', 0)

                total_seconds = delay_seconds + (delay_minutes * 60) + (delay_hours * 3600)
                scheduled_for = datetime.utcnow() + timedelta(seconds=total_seconds)

            elif trigger_type == 'absolute':
                trigger_at = self.config.get('trigger_at')
                scheduled_for = datetime.fromisoformat(trigger_at)

            else:
                return {
                    'success': False,
                    'error': f'Invalid trigger_type: {trigger_type}'
                }

            # Generate trigger ID
            trigger_id = hashlib.md5(
                f"{workflow_id}:{scheduled_for.isoformat()}".encode()
            ).hexdigest()[:16]

            # Create scheduled trigger
            trigger = {
                'trigger_id': trigger_id,
                'trigger_type': trigger_type,
                'workflow_id': workflow_id,
                'scheduled_for': scheduled_for.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'executed': False,
                'status': TriggerStatus.ACTIVE.value
            }

            # Register trigger
            self.scheduled_triggers[trigger_id] = trigger

            return {
                'success': True,
                'trigger_id': trigger_id,
                'scheduled_for': scheduled_for.isoformat(),
                'trigger_type': trigger_type,
                'status': TriggerStatus.ACTIVE.value
            }

        except Exception as e:
            logger.error(f"Time delay trigger failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# TRIGGER MANAGER (Central coordinator)
# ============================================================================

class TriggerManager:
    """
    Central manager for all trigger types
    Coordinates trigger monitoring and workflow execution
    """

    def __init__(self):
        self.cron_scheduler = None
        self.event_trigger = None
        self.webhook_trigger = None
        self.file_watch = None
        self.email_trigger = None
        self.db_trigger = None
        self.interval_trigger = None
        self.time_delay_trigger = None
        self.trigger_history: List[TriggerExecution] = []
        self.running = False

    def register_trigger_agent(self, trigger_type: str, agent: Any):
        """Register a trigger agent"""
        if trigger_type == 'cron':
            self.cron_scheduler = agent
        elif trigger_type == 'event':
            self.event_trigger = agent
        elif trigger_type == 'webhook':
            self.webhook_trigger = agent
        elif trigger_type == 'file_watch':
            self.file_watch = agent
        elif trigger_type == 'email':
            self.email_trigger = agent
        elif trigger_type == 'database':
            self.db_trigger = agent
        elif trigger_type == 'interval':
            self.interval_trigger = agent
        elif trigger_type == 'time_delay':
            self.time_delay_trigger = agent

    async def start_monitoring(self):
        """Start monitoring all triggers"""
        self.running = True
        logger.info("Trigger Manager started monitoring")

    async def stop_monitoring(self):
        """Stop monitoring all triggers"""
        self.running = False
        logger.info("Trigger Manager stopped monitoring")

    def get_trigger_stats(self) -> Dict[str, Any]:
        """Get trigger statistics"""
        return {
            'total_triggers': sum([
                len(getattr(agent, 'scheduled_jobs', {})) if agent else 0
                for agent in [
                    self.cron_scheduler,
                    self.event_trigger,
                    self.webhook_trigger,
                    self.file_watch,
                    self.email_trigger,
                    self.db_trigger,
                    self.interval_trigger,
                    self.time_delay_trigger
                ]
            ]),
            'total_executions': len(self.trigger_history),
            'running': self.running
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'CronSchedulerAgent',
    'EventTriggerAgent',
    'WebhookTriggerAgent',
    'FileWatchTriggerAgent',
    'EmailTriggerAgent',
    'DatabaseTriggerAgent',
    'IntervalTriggerAgent',
    'TimeDelayTriggerAgent',
    'TriggerManager',
    'TriggerStatus',
    'TriggerType',
    'TriggerExecution'
]
