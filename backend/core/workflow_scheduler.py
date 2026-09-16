"""
Workflow Scheduler - Schedule workflow execution with cron, intervals, and events
Uses APScheduler for robust scheduling
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class WorkflowScheduler:
    """
    Schedule workflow execution using APScheduler
    Supports cron, interval, and event-based scheduling
    """

    def __init__(self, workflow_engine=None, workflow_storage=None):
        """
        Initialize workflow scheduler

        Args:
            workflow_engine: WorkflowEngine instance for executing workflows
            workflow_storage: WorkflowStorage instance for loading workflows
        """
        self.workflow_engine = workflow_engine
        self.workflow_storage = workflow_storage
        self.scheduler = None
        self.jobs = {}

        self._initialize_scheduler()

    def _initialize_scheduler(self):
        """Initialize APScheduler"""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger
            from apscheduler.triggers.date import DateTrigger

            self.scheduler = BackgroundScheduler()
            self.CronTrigger = CronTrigger
            self.IntervalTrigger = IntervalTrigger
            self.DateTrigger = DateTrigger

            logger.info("Scheduler initialized")

        except ImportError:
            logger.warning("APScheduler not installed. Run: pip install apscheduler")
            self.scheduler = None

    def start(self):
        """Start the scheduler"""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
            return {'status': 'success', 'message': 'Scheduler started'}
        elif not self.scheduler:
            return {'status': 'error', 'error': 'Scheduler not initialized'}
        else:
            return {'status': 'info', 'message': 'Scheduler already running'}

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
            return {'status': 'success', 'message': 'Scheduler stopped'}
        else:
            return {'status': 'info', 'message': 'Scheduler not running'}

    def schedule_cron(
        self,
        workflow_id: str,
        cron_expression: str,
        input_data: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule workflow with cron expression

        Args:
            workflow_id: Workflow to execute
            cron_expression: Cron expression (e.g., "0 9 * * *" for daily at 9am)
            input_data: Input data for workflow
            job_id: Optional job ID (auto-generated if not provided)

        Returns:
            Dict with job info
        """
        if not self.scheduler:
            return {'status': 'error', 'error': 'Scheduler not available'}

        try:
            job_id = job_id or f"cron_{workflow_id}_{datetime.now().timestamp()}"

            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) != 5:
                return {'status': 'error', 'error': 'Invalid cron expression'}

            minute, hour, day, month, day_of_week = parts

            # Create trigger
            trigger = self.CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )

            # Schedule job
            job = self.scheduler.add_job(
                func=self._execute_workflow,
                trigger=trigger,
                args=[workflow_id, input_data],
                id=job_id,
                name=f"Workflow: {workflow_id}",
                replace_existing=True
            )

            self.jobs[job_id] = {
                'workflow_id': workflow_id,
                'type': 'cron',
                'expression': cron_expression,
                'input_data': input_data,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Scheduled cron job: {job_id}")

            return {
                'status': 'success',
                'job_id': job_id,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

        except Exception as e:
            logger.error(f"Failed to schedule cron job: {e}")
            return {'status': 'error', 'error': str(e)}

    def schedule_interval(
        self,
        workflow_id: str,
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        input_data: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule workflow at regular intervals

        Args:
            workflow_id: Workflow to execute
            seconds: Interval in seconds
            minutes: Interval in minutes
            hours: Interval in hours
            days: Interval in days
            input_data: Input data for workflow
            job_id: Optional job ID

        Returns:
            Dict with job info
        """
        if not self.scheduler:
            return {'status': 'error', 'error': 'Scheduler not available'}

        try:
            job_id = job_id or f"interval_{workflow_id}_{datetime.now().timestamp()}"

            # Create trigger
            trigger = self.IntervalTrigger(
                seconds=seconds or 0,
                minutes=minutes or 0,
                hours=hours or 0,
                days=days or 0
            )

            # Schedule job
            job = self.scheduler.add_job(
                func=self._execute_workflow,
                trigger=trigger,
                args=[workflow_id, input_data],
                id=job_id,
                name=f"Workflow: {workflow_id}",
                replace_existing=True
            )

            interval_str = self._format_interval(seconds, minutes, hours, days)

            self.jobs[job_id] = {
                'workflow_id': workflow_id,
                'type': 'interval',
                'interval': interval_str,
                'input_data': input_data,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Scheduled interval job: {job_id}")

            return {
                'status': 'success',
                'job_id': job_id,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

        except Exception as e:
            logger.error(f"Failed to schedule interval job: {e}")
            return {'status': 'error', 'error': str(e)}

    def schedule_once(
        self,
        workflow_id: str,
        run_date: datetime,
        input_data: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule workflow to run once at specific time

        Args:
            workflow_id: Workflow to execute
            run_date: When to run the workflow
            input_data: Input data for workflow
            job_id: Optional job ID

        Returns:
            Dict with job info
        """
        if not self.scheduler:
            return {'status': 'error', 'error': 'Scheduler not available'}

        try:
            job_id = job_id or f"once_{workflow_id}_{datetime.now().timestamp()}"

            # Create trigger
            trigger = self.DateTrigger(run_date=run_date)

            # Schedule job
            job = self.scheduler.add_job(
                func=self._execute_workflow,
                trigger=trigger,
                args=[workflow_id, input_data],
                id=job_id,
                name=f"Workflow: {workflow_id}",
                replace_existing=True
            )

            self.jobs[job_id] = {
                'workflow_id': workflow_id,
                'type': 'once',
                'run_date': run_date.isoformat(),
                'input_data': input_data,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Scheduled one-time job: {job_id}")

            return {
                'status': 'success',
                'job_id': job_id,
                'run_date': run_date.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to schedule one-time job: {e}")
            return {'status': 'error', 'error': str(e)}

    def remove_job(self, job_id: str) -> Dict[str, Any]:
        """
        Remove a scheduled job

        Args:
            job_id: Job ID to remove

        Returns:
            Dict with status
        """
        if not self.scheduler:
            return {'status': 'error', 'error': 'Scheduler not available'}

        try:
            self.scheduler.remove_job(job_id)

            if job_id in self.jobs:
                del self.jobs[job_id]

            logger.info(f"Removed job: {job_id}")

            return {'status': 'success', 'message': f'Job {job_id} removed'}

        except Exception as e:
            logger.error(f"Failed to remove job: {e}")
            return {'status': 'error', 'error': str(e)}

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all scheduled jobs

        Returns:
            List of job info dicts
        """
        if not self.scheduler:
            return []

        jobs_list = []
        for job in self.scheduler.get_jobs():
            job_info = self.jobs.get(job.id, {})
            jobs_list.append({
                'job_id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'workflow_id': job_info.get('workflow_id'),
                'type': job_info.get('type'),
                'trigger': str(job.trigger)
            })

        return jobs_list

    def _execute_workflow(self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None):
        """Execute a scheduled workflow"""
        try:
            logger.info(f"Executing scheduled workflow: {workflow_id}")

            if not self.workflow_engine or not self.workflow_storage:
                logger.error("Workflow engine or storage not configured")
                return

            # Load workflow
            workflow = self.workflow_storage.load_workflow(workflow_id)
            if not workflow:
                logger.error(f"Workflow not found: {workflow_id}")
                return

            # Execute workflow
            import asyncio
            result = asyncio.run(
                self.workflow_engine.execute_workflow(workflow, input_data or {})
            )

            logger.info(f"Scheduled workflow completed: {workflow_id}, status: {result.status}")

        except Exception as e:
            logger.error(f"Scheduled workflow execution failed: {e}")

    def _format_interval(
        self,
        seconds: Optional[int],
        minutes: Optional[int],
        hours: Optional[int],
        days: Optional[int]
    ) -> str:
        """Format interval as human-readable string"""
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds:
            parts.append(f"{seconds}s")

        return " ".join(parts) if parts else "0s"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['WorkflowScheduler']
