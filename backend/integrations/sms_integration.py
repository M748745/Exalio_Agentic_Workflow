"""
SMS Integration - Twilio SMS sending
Send SMS messages via Twilio API
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SMSIntegration:
    """
    SMS integration using Twilio
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SMS integration

        Args:
            config: Configuration dict with:
                - account_sid: Twilio Account SID
                - auth_token: Twilio Auth Token
                - from_number: Twilio phone number to send from
        """
        self.config = config
        self.account_sid = config.get('account_sid')
        self.auth_token = config.get('auth_token')
        self.from_number = config.get('from_number')

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("Twilio credentials not fully configured")

    def send_sms(
        self,
        to_number: str,
        body: str,
        from_number: Optional[str] = None,
        media_url: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS message

        Args:
            to_number: Recipient phone number (E.164 format: +1234567890)
            body: Message body (max 1600 chars)
            from_number: Override sender number
            media_url: List of media URLs to send (MMS)

        Returns:
            Dict with status and message_sid
        """
        try:
            from twilio.rest import Client
        except ImportError:
            return {
                'status': 'error',
                'error': 'Twilio package not installed. Run: pip install twilio'
            }

        if not all([self.account_sid, self.auth_token]):
            return {
                'status': 'error',
                'error': 'Twilio account_sid and auth_token required'
            }

        try:
            from_number = from_number or self.from_number

            if not from_number:
                return {
                    'status': 'error',
                    'error': 'from_number is required'
                }

            # Initialize Twilio client
            client = Client(self.account_sid, self.auth_token)

            # Send message
            message_params = {
                'body': body,
                'from_': from_number,
                'to': to_number
            }

            if media_url:
                message_params['media_url'] = media_url

            message = client.messages.create(**message_params)

            logger.info(f"SMS sent to {to_number}, SID: {message.sid}")

            return {
                'status': 'success',
                'message_sid': message.sid,
                'to': to_number,
                'from': from_number,
                'body': body[:50] + '...' if len(body) > 50 else body
            }

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def send_bulk_sms(
        self,
        recipients: List[str],
        body: str,
        from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS to multiple recipients

        Args:
            recipients: List of phone numbers
            body: Message body
            from_number: Override sender number

        Returns:
            Dict with results for each recipient
        """
        results = []

        for to_number in recipients:
            result = self.send_sms(to_number, body, from_number)
            results.append({
                'to': to_number,
                'result': result
            })

        successful = sum(1 for r in results if r['result']['status'] == 'success')
        failed = len(results) - successful

        return {
            'status': 'success' if failed == 0 else 'partial',
            'total': len(results),
            'successful': successful,
            'failed': failed,
            'results': results
        }

    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get status of a sent message

        Args:
            message_sid: Twilio message SID

        Returns:
            Dict with message status
        """
        try:
            from twilio.rest import Client
        except ImportError:
            return {
                'status': 'error',
                'error': 'Twilio package not installed'
            }

        try:
            client = Client(self.account_sid, self.auth_token)
            message = client.messages(message_sid).fetch()

            return {
                'status': 'success',
                'message_sid': message.sid,
                'message_status': message.status,
                'to': message.to,
                'from': message.from_,
                'date_sent': str(message.date_sent) if message.date_sent else None,
                'error_code': message.error_code,
                'error_message': message.error_message
            }

        except Exception as e:
            logger.error(f"Failed to get message status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


class SMSAgent:
    """
    Agent wrapper for SMS integration
    Compatible with workflow engine
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize SMS agent"""
        self.integration = SMSIntegration(config)
        self.name = "sms_agent"
        self.description = "Send SMS messages via Twilio"

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SMS sending

        Context should contain:
            - to_number: Recipient phone number
            - body: Message text
            - from_number: Sender number (optional)
            - media_url: Media URLs for MMS (optional)
        """
        try:
            to_number = context.get('to_number')
            body = context.get('body', '')

            if not to_number:
                return {
                    'status': 'error',
                    'error': 'to_number is required'
                }

            if not body:
                return {
                    'status': 'error',
                    'error': 'body is required'
                }

            result = self.integration.send_sms(
                to_number=to_number,
                body=body,
                from_number=context.get('from_number'),
                media_url=context.get('media_url')
            )

            return result

        except Exception as e:
            logger.error(f"SMS agent error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['SMSIntegration', 'SMSAgent']
