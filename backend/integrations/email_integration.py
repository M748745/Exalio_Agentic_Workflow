"""
Email Integration - SMTP and SendGrid support
Sends emails via SMTP or SendGrid API
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailIntegration:
    """
    Email integration supporting SMTP and SendGrid
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize email integration

        Args:
            config: Configuration dict with:
                - provider: 'smtp' or 'sendgrid'
                - smtp_host: SMTP server host (for SMTP)
                - smtp_port: SMTP server port (for SMTP)
                - smtp_username: SMTP username
                - smtp_password: SMTP password
                - use_tls: Use TLS (default: True)
                - sendgrid_api_key: SendGrid API key (for SendGrid)
                - from_email: Default sender email
                - from_name: Default sender name
        """
        self.config = config
        self.provider = config.get('provider', 'smtp').lower()

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach
            from_email: Override sender email
            from_name: Override sender name

        Returns:
            Dict with status and message_id
        """
        try:
            if self.provider == 'smtp':
                return self._send_smtp(
                    to_email, subject, body, html_body,
                    cc, bcc, attachments, from_email, from_name
                )
            elif self.provider == 'sendgrid':
                return self._send_sendgrid(
                    to_email, subject, body, html_body,
                    cc, bcc, attachments, from_email, from_name
                )
            else:
                raise ValueError(f"Unsupported email provider: {self.provider}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _send_smtp(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP"""

        # Get configuration
        smtp_host = self.config.get('smtp_host', 'smtp.gmail.com')
        smtp_port = self.config.get('smtp_port', 587)
        smtp_username = self.config.get('smtp_username')
        smtp_password = self.config.get('smtp_password')
        use_tls = self.config.get('use_tls', True)

        from_email = from_email or self.config.get('from_email')
        from_name = from_name or self.config.get('from_name', '')

        if not from_email:
            raise ValueError("from_email is required")

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
        msg['To'] = to_email

        if cc:
            msg['Cc'] = ', '.join(cc)

        # Add body
        msg.attach(MIMEText(body, 'plain'))

        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Add attachments
        if attachments:
            for filepath in attachments:
                if Path(filepath).exists():
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(filepath).name}'
                        )
                        msg.attach(part)

        # Send email
        recipients = [to_email]
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()

            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)

            server.send_message(msg)

        logger.info(f"Email sent via SMTP to {to_email}")

        return {
            'status': 'success',
            'provider': 'smtp',
            'to': to_email,
            'subject': subject
        }

    def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid API"""

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
            import base64
        except ImportError:
            raise ImportError("sendgrid package not installed. Run: pip install sendgrid")

        api_key = self.config.get('sendgrid_api_key')
        if not api_key:
            raise ValueError("SendGrid API key not configured")

        from_email = from_email or self.config.get('from_email')
        from_name = from_name or self.config.get('from_name', '')

        # Create message
        message = Mail(
            from_email=Email(from_email, from_name),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=Content("text/plain", body)
        )

        if html_body:
            message.add_content(Content("text/html", html_body))

        # Add CC/BCC
        if cc:
            for email in cc:
                message.add_cc(email)

        if bcc:
            for email in bcc:
                message.add_bcc(email)

        # Add attachments
        if attachments:
            for filepath in attachments:
                if Path(filepath).exists():
                    with open(filepath, 'rb') as f:
                        data = f.read()
                        encoded = base64.b64encode(data).decode()

                        attachment = Attachment()
                        attachment.file_content = encoded
                        attachment.file_name = Path(filepath).name
                        attachment.disposition = "attachment"
                        message.add_attachment(attachment)

        # Send email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        logger.info(f"Email sent via SendGrid to {to_email}")

        return {
            'status': 'success',
            'provider': 'sendgrid',
            'to': to_email,
            'subject': subject,
            'message_id': response.headers.get('X-Message-Id')
        }


class EmailAgent:
    """
    Agent wrapper for email integration
    Compatible with workflow engine
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize email agent"""
        self.integration = EmailIntegration(config)
        self.name = "email_agent"
        self.description = "Send emails via SMTP or SendGrid"

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute email sending

        Context should contain:
            - to_email: Recipient email
            - subject: Email subject
            - body: Email body
            - html_body: HTML body (optional)
            - cc: CC list (optional)
            - bcc: BCC list (optional)
            - attachments: Attachment paths (optional)
        """
        try:
            to_email = context.get('to_email')
            subject = context.get('subject', 'No Subject')
            body = context.get('body', '')

            if not to_email:
                return {
                    'status': 'error',
                    'error': 'to_email is required'
                }

            result = self.integration.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                html_body=context.get('html_body'),
                cc=context.get('cc'),
                bcc=context.get('bcc'),
                attachments=context.get('attachments'),
                from_email=context.get('from_email'),
                from_name=context.get('from_name')
            )

            return result

        except Exception as e:
            logger.error(f"Email agent error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['EmailIntegration', 'EmailAgent']
