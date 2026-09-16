"""
Human-in-the-Loop (HITL) Agents (MEDIUM PRIORITY)
7 nodes for human oversight and intervention in workflows

Features:
- Approval workflows (multi-level approval chains)
- Manual input collection (forms, data entry)
- Review processes (document review, quality checks)
- Escalation (routing to supervisors/specialists)
- Task assignment (assign work to specific users)
- Notifications (alert humans about workflow events)
- Feedback collection (gather human feedback)

This enables enterprise workflows with human oversight and decision-making.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Task assignment status"""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# 1. APPROVAL NODE
# ============================================================================

class ApprovalAgent:
    """
    Request approval from humans
    Supports single or multi-level approval chains
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pending_approvals: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request approval

        Config:
            approvers: List of approver user IDs/emails
            approval_type: 'any' (any approver), 'all' (all approvers), 'majority'
            timeout_minutes: Auto-reject after timeout
            notification_channels: ['email', 'slack', 'sms']
            allow_comments: Whether approvers can add comments
            auto_escalate: Auto-escalate on timeout
            escalation_chain: List of escalation approvers

        Inputs:
            request_title: Approval request title
            request_description: Detailed description
            request_data: Data payload for context
            requester_id: User requesting approval
            priority: 'low', 'medium', 'high', 'urgent'

        Returns:
            approval_id, status, approved_by, rejected_by, comments, timeout_at
        """
        try:
            approvers = self.config.get('approvers', [])
            approval_type = self.config.get('approval_type', 'any')
            timeout_minutes = self.config.get('timeout_minutes', 1440)  # 24 hours default
            allow_comments = self.config.get('allow_comments', True)
            auto_escalate = self.config.get('auto_escalate', False)
            escalation_chain = self.config.get('escalation_chain', [])

            request_title = inputs.get('request_title', 'Approval Required')
            request_description = inputs.get('request_description', '')
            request_data = inputs.get('request_data', {})
            requester_id = inputs.get('requester_id')
            priority = inputs.get('priority', 'medium')

            # Generate approval ID
            approval_id = str(uuid.uuid4())

            # Calculate timeout
            timeout_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

            # Create approval record
            approval_record = {
                'approval_id': approval_id,
                'status': ApprovalStatus.PENDING.value,
                'request_title': request_title,
                'request_description': request_description,
                'request_data': request_data,
                'requester_id': requester_id,
                'priority': priority,
                'approvers': approvers,
                'approval_type': approval_type,
                'approved_by': [],
                'rejected_by': [],
                'comments': [],
                'created_at': datetime.utcnow().isoformat(),
                'timeout_at': timeout_at.isoformat(),
                'auto_escalate': auto_escalate,
                'escalation_chain': escalation_chain
            }

            # Store pending approval
            self.pending_approvals[approval_id] = approval_record

            # Send notifications (placeholder - would integrate with notification system)
            notifications_sent = self._send_approval_notifications(
                approval_record,
                self.config.get('notification_channels', ['email'])
            )

            return {
                'success': True,
                'approval_id': approval_id,
                'status': ApprovalStatus.PENDING.value,
                'approvers': approvers,
                'approval_type': approval_type,
                'timeout_at': timeout_at.isoformat(),
                'notifications_sent': notifications_sent,
                'request_title': request_title
            }

        except Exception as e:
            logger.error(f"Approval request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def process_approval_response(
        self,
        approval_id: str,
        approver_id: str,
        decision: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process approval response from human

        Args:
            approval_id: Approval request ID
            approver_id: Approver user ID
            decision: 'approve' or 'reject'
            comment: Optional comment

        Returns:
            Final approval status and details
        """
        try:
            if approval_id not in self.pending_approvals:
                return {
                    'success': False,
                    'error': 'Approval request not found'
                }

            approval = self.pending_approvals[approval_id]

            # Check if approver is authorized
            if approver_id not in approval['approvers']:
                return {
                    'success': False,
                    'error': 'Unauthorized approver'
                }

            # Check if already responded
            if approver_id in approval['approved_by'] or approver_id in approval['rejected_by']:
                return {
                    'success': False,
                    'error': 'Approver already responded'
                }

            # Record decision
            if decision.lower() == 'approve':
                approval['approved_by'].append(approver_id)
            elif decision.lower() == 'reject':
                approval['rejected_by'].append(approver_id)

            # Add comment
            if comment:
                approval['comments'].append({
                    'approver_id': approver_id,
                    'comment': comment,
                    'decision': decision,
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Check if final decision reached
            approval_type = approval['approval_type']
            total_approvers = len(approval['approvers'])
            approved_count = len(approval['approved_by'])
            rejected_count = len(approval['rejected_by'])

            final_status = None

            if approval_type == 'any':
                # Any approver can approve, any can reject
                if approved_count > 0:
                    final_status = ApprovalStatus.APPROVED
                elif rejected_count > 0:
                    final_status = ApprovalStatus.REJECTED

            elif approval_type == 'all':
                # All must approve, any can reject
                if rejected_count > 0:
                    final_status = ApprovalStatus.REJECTED
                elif approved_count == total_approvers:
                    final_status = ApprovalStatus.APPROVED

            elif approval_type == 'majority':
                # Majority wins
                if approved_count > total_approvers / 2:
                    final_status = ApprovalStatus.APPROVED
                elif rejected_count > total_approvers / 2:
                    final_status = ApprovalStatus.REJECTED

            # Update status if final decision reached
            if final_status:
                approval['status'] = final_status.value
                approval['completed_at'] = datetime.utcnow().isoformat()

            return {
                'success': True,
                'approval_id': approval_id,
                'status': approval['status'],
                'approved_by': approval['approved_by'],
                'rejected_by': approval['rejected_by'],
                'comments': approval['comments'],
                'is_final': final_status is not None
            }

        except Exception as e:
            logger.error(f"Process approval response failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _send_approval_notifications(self, approval: Dict, channels: List[str]) -> List[str]:
        """Send approval request notifications"""
        # Placeholder - would integrate with NotificationAgent
        logger.info(f"Sending approval notifications to {approval['approvers']} via {channels}")
        return channels


# ============================================================================
# 2. MANUAL INPUT NODE
# ============================================================================

class ManualInputAgent:
    """
    Collect manual input from humans
    Supports forms, data entry, file uploads
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pending_inputs: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request manual input

        Config:
            input_fields: List of field definitions
            assigned_to: User ID to collect input from
            timeout_minutes: Auto-timeout if not provided
            validation_rules: Field validation rules

        Input Field Definition:
            {
                "name": "customer_email",
                "label": "Customer Email",
                "type": "email",  # text, email, number, date, file, select, checkbox
                "required": True,
                "validation": {"pattern": "^[a-z]+@[a-z]+\\.[a-z]+$"},
                "options": ["Option 1", "Option 2"],  # For select fields
                "help_text": "Enter the customer's email address"
            }

        Returns:
            input_request_id, status, assigned_to, timeout_at
        """
        try:
            input_fields = self.config.get('input_fields', [])
            assigned_to = self.config.get('assigned_to') or inputs.get('assigned_to')
            timeout_minutes = self.config.get('timeout_minutes', 1440)
            validation_rules = self.config.get('validation_rules', {})

            request_title = inputs.get('request_title', 'Manual Input Required')
            request_description = inputs.get('request_description', '')
            context_data = inputs.get('context_data', {})

            # Generate input request ID
            input_request_id = str(uuid.uuid4())

            # Calculate timeout
            timeout_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

            # Create input request
            input_request = {
                'input_request_id': input_request_id,
                'status': 'pending',
                'request_title': request_title,
                'request_description': request_description,
                'input_fields': input_fields,
                'assigned_to': assigned_to,
                'context_data': context_data,
                'validation_rules': validation_rules,
                'collected_data': {},
                'created_at': datetime.utcnow().isoformat(),
                'timeout_at': timeout_at.isoformat()
            }

            # Store pending input request
            self.pending_inputs[input_request_id] = input_request

            return {
                'success': True,
                'input_request_id': input_request_id,
                'status': 'pending',
                'assigned_to': assigned_to,
                'input_fields': input_fields,
                'timeout_at': timeout_at.isoformat(),
                'request_title': request_title
            }

        except Exception as e:
            logger.error(f"Manual input request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def submit_input(
        self,
        input_request_id: str,
        user_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit manual input

        Args:
            input_request_id: Input request ID
            user_id: User submitting input
            input_data: Dict of field_name -> value

        Returns:
            success, validation_errors, collected_data
        """
        try:
            if input_request_id not in self.pending_inputs:
                return {
                    'success': False,
                    'error': 'Input request not found'
                }

            request = self.pending_inputs[input_request_id]

            # Check if user is authorized
            if request['assigned_to'] and user_id != request['assigned_to']:
                return {
                    'success': False,
                    'error': 'Unauthorized user'
                }

            # Validate input
            validation_errors = self._validate_input(
                input_data,
                request['input_fields'],
                request['validation_rules']
            )

            if validation_errors:
                return {
                    'success': False,
                    'validation_errors': validation_errors
                }

            # Store collected data
            request['collected_data'] = input_data
            request['status'] = 'completed'
            request['submitted_by'] = user_id
            request['submitted_at'] = datetime.utcnow().isoformat()

            return {
                'success': True,
                'input_request_id': input_request_id,
                'status': 'completed',
                'collected_data': input_data,
                'submitted_by': user_id
            }

        except Exception as e:
            logger.error(f"Submit input failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_input(
        self,
        input_data: Dict,
        input_fields: List[Dict],
        validation_rules: Dict
    ) -> List[Dict]:
        """Validate submitted input"""
        errors = []

        for field in input_fields:
            field_name = field['name']
            field_value = input_data.get(field_name)

            # Check required
            if field.get('required', False) and not field_value:
                errors.append({
                    'field': field_name,
                    'error': f'{field.get("label", field_name)} is required'
                })
                continue

            # Type validation
            field_type = field.get('type', 'text')
            if field_value:
                if field_type == 'email':
                    import re
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(field_value)):
                        errors.append({
                            'field': field_name,
                            'error': 'Invalid email format'
                        })
                elif field_type == 'number':
                    try:
                        float(field_value)
                    except ValueError:
                        errors.append({
                            'field': field_name,
                            'error': 'Must be a number'
                        })

            # Custom validation
            if field_name in validation_rules:
                rule = validation_rules[field_name]
                if 'pattern' in rule:
                    import re
                    if not re.match(rule['pattern'], str(field_value)):
                        errors.append({
                            'field': field_name,
                            'error': rule.get('error_message', 'Invalid format')
                        })

        return errors


# ============================================================================
# 3. REVIEW NODE
# ============================================================================

class ReviewAgent:
    """
    Human review process for documents, data, or workflow outputs
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pending_reviews: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request human review

        Config:
            reviewers: List of reviewer user IDs
            review_type: 'document', 'data', 'output', 'code'
            review_criteria: List of criteria to check
            allow_feedback: Whether reviewers can provide feedback
            require_all_reviewers: All must review or just one

        Inputs:
            review_title: Review request title
            content_to_review: Content (text, data, file path)
            content_type: 'text', 'json', 'file', 'url'
            priority: Review priority

        Returns:
            review_id, status, reviewers, criteria
        """
        try:
            reviewers = self.config.get('reviewers', [])
            review_type = self.config.get('review_type', 'document')
            review_criteria = self.config.get('review_criteria', [])
            allow_feedback = self.config.get('allow_feedback', True)
            require_all_reviewers = self.config.get('require_all_reviewers', False)

            review_title = inputs.get('review_title', 'Review Required')
            content_to_review = inputs.get('content_to_review')
            content_type = inputs.get('content_type', 'text')
            priority = inputs.get('priority', 'medium')

            # Generate review ID
            review_id = str(uuid.uuid4())

            # Create review record
            review_record = {
                'review_id': review_id,
                'status': 'pending',
                'review_title': review_title,
                'review_type': review_type,
                'content_to_review': content_to_review,
                'content_type': content_type,
                'review_criteria': review_criteria,
                'reviewers': reviewers,
                'require_all_reviewers': require_all_reviewers,
                'priority': priority,
                'reviews_submitted': [],
                'feedbacks': [],
                'created_at': datetime.utcnow().isoformat()
            }

            # Store pending review
            self.pending_reviews[review_id] = review_record

            return {
                'success': True,
                'review_id': review_id,
                'status': 'pending',
                'reviewers': reviewers,
                'review_criteria': review_criteria,
                'review_title': review_title
            }

        except Exception as e:
            logger.error(f"Review request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def submit_review(
        self,
        review_id: str,
        reviewer_id: str,
        decision: str,
        criteria_scores: Dict[str, int],
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit review

        Args:
            review_id: Review request ID
            reviewer_id: Reviewer user ID
            decision: 'approve', 'reject', 'needs_revision'
            criteria_scores: Dict of criterion -> score (1-5)
            feedback: Optional feedback text

        Returns:
            success, status, overall_score
        """
        try:
            if review_id not in self.pending_reviews:
                return {
                    'success': False,
                    'error': 'Review request not found'
                }

            review = self.pending_reviews[review_id]

            # Check if reviewer is authorized
            if reviewer_id not in review['reviewers']:
                return {
                    'success': False,
                    'error': 'Unauthorized reviewer'
                }

            # Check if already reviewed
            if reviewer_id in [r['reviewer_id'] for r in review['reviews_submitted']]:
                return {
                    'success': False,
                    'error': 'Already submitted review'
                }

            # Calculate overall score
            overall_score = sum(criteria_scores.values()) / len(criteria_scores) if criteria_scores else 0

            # Record review
            review_submission = {
                'reviewer_id': reviewer_id,
                'decision': decision,
                'criteria_scores': criteria_scores,
                'overall_score': overall_score,
                'feedback': feedback,
                'submitted_at': datetime.utcnow().isoformat()
            }

            review['reviews_submitted'].append(review_submission)

            if feedback:
                review['feedbacks'].append({
                    'reviewer_id': reviewer_id,
                    'feedback': feedback,
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Check if review complete
            require_all = review['require_all_reviewers']
            total_reviewers = len(review['reviewers'])
            reviews_count = len(review['reviews_submitted'])

            if require_all and reviews_count == total_reviewers:
                # All reviewed - determine final status
                decisions = [r['decision'] for r in review['reviews_submitted']]
                if all(d == 'approve' for d in decisions):
                    review['status'] = 'approved'
                elif any(d == 'reject' for d in decisions):
                    review['status'] = 'rejected'
                else:
                    review['status'] = 'needs_revision'
                review['completed_at'] = datetime.utcnow().isoformat()

            elif not require_all and reviews_count > 0:
                # Just one review needed
                review['status'] = decision
                review['completed_at'] = datetime.utcnow().isoformat()

            return {
                'success': True,
                'review_id': review_id,
                'status': review['status'],
                'overall_score': overall_score,
                'reviews_submitted': reviews_count,
                'total_reviewers': total_reviewers
            }

        except Exception as e:
            logger.error(f"Submit review failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 4. ESCALATION NODE
# ============================================================================

class EscalationAgent:
    """
    Escalate issues to supervisors or specialists
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Escalate issue

        Config:
            escalation_rules: List of escalation rules
            escalation_chain: List of escalation levels
            auto_escalate_after_minutes: Auto-escalate if not resolved

        Escalation Rule:
            {
                "condition": "priority == 'urgent'",
                "escalate_to": "supervisor_team",
                "level": 1
            }

        Inputs:
            issue_title: Issue title
            issue_description: Detailed description
            issue_data: Issue context data
            priority: Issue priority
            current_assignee: Current handler
            reason: Escalation reason

        Returns:
            escalation_id, escalated_to, level, notification_sent
        """
        try:
            escalation_rules = self.config.get('escalation_rules', [])
            escalation_chain = self.config.get('escalation_chain', [])

            issue_title = inputs.get('issue_title', 'Issue Escalation')
            issue_description = inputs.get('issue_description', '')
            issue_data = inputs.get('issue_data', {})
            priority = inputs.get('priority', 'medium')
            current_assignee = inputs.get('current_assignee')
            reason = inputs.get('reason', 'Manual escalation')

            # Determine escalation level
            escalation_level = 1
            escalated_to = None

            # Check rules
            for rule in escalation_rules:
                condition = rule.get('condition', 'False')
                try:
                    context = {'priority': priority, **issue_data}
                    if eval(condition, {"__builtins__": {}}, context):
                        escalated_to = rule.get('escalate_to')
                        escalation_level = rule.get('level', 1)
                        break
                except:
                    pass

            # Use escalation chain if no rule matched
            if not escalated_to and escalation_chain:
                escalated_to = escalation_chain[min(escalation_level - 1, len(escalation_chain) - 1)]

            # Generate escalation ID
            escalation_id = str(uuid.uuid4())

            # Create escalation record
            escalation_record = {
                'escalation_id': escalation_id,
                'issue_title': issue_title,
                'issue_description': issue_description,
                'issue_data': issue_data,
                'priority': priority,
                'current_assignee': current_assignee,
                'escalated_to': escalated_to,
                'escalation_level': escalation_level,
                'reason': reason,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'escalated'
            }

            # Send escalation notification (placeholder)
            logger.info(f"Escalating to {escalated_to}: {issue_title}")

            return {
                'success': True,
                'escalation_id': escalation_id,
                'escalated_to': escalated_to,
                'escalation_level': escalation_level,
                'issue_title': issue_title,
                'priority': priority,
                'notification_sent': True
            }

        except Exception as e:
            logger.error(f"Escalation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 5. ASSIGNMENT NODE
# ============================================================================

class AssignmentAgent:
    """
    Assign tasks to specific users or teams
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.assignments: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign task

        Config:
            assignment_strategy: 'specific', 'round_robin', 'load_balanced', 'skill_based'
            available_assignees: List of user IDs
            team_id: Team to assign from

        Inputs:
            task_title: Task title
            task_description: Task description
            task_data: Task context
            assigned_to: Specific user (for 'specific' strategy)
            priority: Task priority
            due_date: Task due date
            estimated_time_minutes: Estimated completion time

        Returns:
            assignment_id, assigned_to, status, due_date
        """
        try:
            assignment_strategy = self.config.get('assignment_strategy', 'specific')
            available_assignees = self.config.get('available_assignees', [])

            task_title = inputs.get('task_title', 'Task Assignment')
            task_description = inputs.get('task_description', '')
            task_data = inputs.get('task_data', {})
            assigned_to = inputs.get('assigned_to')
            priority = inputs.get('priority', 'medium')
            due_date = inputs.get('due_date')
            estimated_time_minutes = inputs.get('estimated_time_minutes', 60)

            # Determine assignee based on strategy
            if assignment_strategy == 'specific':
                # Use specified assignee
                if not assigned_to:
                    return {
                        'success': False,
                        'error': 'assigned_to required for specific strategy'
                    }
            elif assignment_strategy == 'round_robin':
                # Simple round robin
                if available_assignees:
                    assigned_to = available_assignees[len(self.assignments) % len(available_assignees)]
            elif assignment_strategy == 'load_balanced':
                # Assign to person with least tasks (simplified)
                if available_assignees:
                    # Count assignments per user
                    user_counts = {user: 0 for user in available_assignees}
                    for assignment in self.assignments.values():
                        if assignment['assigned_to'] in user_counts:
                            user_counts[assignment['assigned_to']] += 1
                    assigned_to = min(user_counts, key=user_counts.get)

            # Generate assignment ID
            assignment_id = str(uuid.uuid4())

            # Create assignment
            assignment_record = {
                'assignment_id': assignment_id,
                'task_title': task_title,
                'task_description': task_description,
                'task_data': task_data,
                'assigned_to': assigned_to,
                'priority': priority,
                'due_date': due_date,
                'estimated_time_minutes': estimated_time_minutes,
                'status': TaskStatus.ASSIGNED.value,
                'created_at': datetime.utcnow().isoformat(),
                'assigned_at': datetime.utcnow().isoformat()
            }

            # Store assignment
            self.assignments[assignment_id] = assignment_record

            return {
                'success': True,
                'assignment_id': assignment_id,
                'assigned_to': assigned_to,
                'status': TaskStatus.ASSIGNED.value,
                'task_title': task_title,
                'priority': priority,
                'due_date': due_date
            }

        except Exception as e:
            logger.error(f"Assignment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 6. NOTIFICATION NODE
# ============================================================================

class NotificationAgent:
    """
    Send notifications to users about workflow events
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification

        Config:
            notification_channels: ['email', 'slack', 'sms', 'in_app']
            template: Notification template

        Inputs:
            recipients: List of user IDs to notify
            title: Notification title
            message: Notification message
            priority: 'low', 'medium', 'high', 'urgent'
            action_url: Optional URL for action button
            data: Additional data payload

        Returns:
            notification_id, sent_to, channels_used, success_count
        """
        try:
            notification_channels = self.config.get('notification_channels', ['in_app'])

            recipients = inputs.get('recipients', [])
            if isinstance(recipients, str):
                recipients = [recipients]

            title = inputs.get('title', 'Notification')
            message = inputs.get('message', '')
            priority = inputs.get('priority', 'medium')
            action_url = inputs.get('action_url')
            data = inputs.get('data', {})

            # Generate notification ID
            notification_id = str(uuid.uuid4())

            # Create notification
            notification = {
                'notification_id': notification_id,
                'recipients': recipients,
                'title': title,
                'message': message,
                'priority': priority,
                'action_url': action_url,
                'data': data,
                'channels': notification_channels,
                'created_at': datetime.utcnow().isoformat(),
                'sent': False
            }

            # Send notifications via channels (placeholder)
            success_count = 0
            for channel in notification_channels:
                try:
                    logger.info(f"Sending {channel} notification to {recipients}: {title}")
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {e}")

            notification['sent'] = success_count > 0
            notification['success_count'] = success_count

            return {
                'success': True,
                'notification_id': notification_id,
                'sent_to': recipients,
                'channels_used': notification_channels,
                'success_count': success_count,
                'title': title,
                'priority': priority
            }

        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 7. FEEDBACK COLLECTION NODE
# ============================================================================

class FeedbackCollectionAgent:
    """
    Collect feedback from users
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.feedback_requests: Dict[str, Dict] = {}

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request feedback

        Config:
            feedback_type: 'rating', 'survey', 'freeform', 'nps'
            questions: List of questions
            rating_scale: Scale for ratings (e.g., 1-5, 1-10)
            allow_anonymous: Allow anonymous feedback

        Question Format:
            {
                "question": "How satisfied are you?",
                "type": "rating",  # rating, multiple_choice, text, yes_no
                "scale": 5,
                "options": ["Option 1", "Option 2"],  # For multiple_choice
                "required": True
            }

        Inputs:
            feedback_title: Feedback request title
            feedback_description: Description
            target_users: Users to request feedback from
            context_data: Context about what feedback is for

        Returns:
            feedback_request_id, status, target_users, questions
        """
        try:
            feedback_type = self.config.get('feedback_type', 'rating')
            questions = self.config.get('questions', [])
            rating_scale = self.config.get('rating_scale', 5)
            allow_anonymous = self.config.get('allow_anonymous', False)

            feedback_title = inputs.get('feedback_title', 'Feedback Request')
            feedback_description = inputs.get('feedback_description', '')
            target_users = inputs.get('target_users', [])
            context_data = inputs.get('context_data', {})

            # Generate feedback request ID
            feedback_request_id = str(uuid.uuid4())

            # Create feedback request
            feedback_request = {
                'feedback_request_id': feedback_request_id,
                'feedback_title': feedback_title,
                'feedback_description': feedback_description,
                'feedback_type': feedback_type,
                'questions': questions,
                'rating_scale': rating_scale,
                'allow_anonymous': allow_anonymous,
                'target_users': target_users,
                'context_data': context_data,
                'responses': [],
                'created_at': datetime.utcnow().isoformat(),
                'status': 'open'
            }

            # Store feedback request
            self.feedback_requests[feedback_request_id] = feedback_request

            return {
                'success': True,
                'feedback_request_id': feedback_request_id,
                'status': 'open',
                'target_users': target_users,
                'questions': questions,
                'feedback_title': feedback_title
            }

        except Exception as e:
            logger.error(f"Feedback request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def submit_feedback(
        self,
        feedback_request_id: str,
        user_id: Optional[str],
        answers: Dict[str, Any],
        additional_comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit feedback

        Args:
            feedback_request_id: Feedback request ID
            user_id: User submitting (None if anonymous)
            answers: Dict of question_id -> answer
            additional_comments: Optional additional comments

        Returns:
            success, feedback_submission_id
        """
        try:
            if feedback_request_id not in self.feedback_requests:
                return {
                    'success': False,
                    'error': 'Feedback request not found'
                }

            request = self.feedback_requests[feedback_request_id]

            # Check if anonymous allowed
            if not user_id and not request['allow_anonymous']:
                return {
                    'success': False,
                    'error': 'Anonymous feedback not allowed'
                }

            # Generate submission ID
            submission_id = str(uuid.uuid4())

            # Create feedback submission
            submission = {
                'submission_id': submission_id,
                'user_id': user_id,
                'answers': answers,
                'additional_comments': additional_comments,
                'submitted_at': datetime.utcnow().isoformat()
            }

            # Store response
            request['responses'].append(submission)

            # Calculate aggregate stats
            response_count = len(request['responses'])

            return {
                'success': True,
                'feedback_submission_id': submission_id,
                'feedback_request_id': feedback_request_id,
                'response_count': response_count
            }

        except Exception as e:
            logger.error(f"Submit feedback failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ApprovalAgent',
    'ManualInputAgent',
    'ReviewAgent',
    'EscalationAgent',
    'AssignmentAgent',
    'NotificationAgent',
    'FeedbackCollectionAgent',
    'ApprovalStatus',
    'TaskStatus',
    'NotificationPriority'
]
