"""
Email Service
Handles sending emails via SMTP with support for multiple providers
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""

    # Common SMTP configurations
    SMTP_CONFIGS = {
        'gmail': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True
        },
        'outlook': {
            'host': 'smtp-mail.outlook.com',
            'port': 587,
            'use_tls': True
        },
        'yahoo': {
            'host': 'smtp.mail.yahoo.com',
            'port': 587,
            'use_tls': True
        },
        'custom': {
            'host': None,  # Must be provided
            'port': 587,
            'use_tls': True
        }
    }

    def __init__(self, provider: str = 'gmail',
                 smtp_host: Optional[str] = None,
                 smtp_port: Optional[int] = None,
                 use_tls: bool = True):
        """
        Initialize Email Service

        Args:
            provider: Email provider ('gmail', 'outlook', 'yahoo', 'custom')
            smtp_host: Custom SMTP host (required if provider='custom')
            smtp_port: Custom SMTP port
            use_tls: Whether to use TLS encryption
        """
        if provider in self.SMTP_CONFIGS:
            config = self.SMTP_CONFIGS[provider].copy()
            if smtp_host:
                config['host'] = smtp_host
            if smtp_port:
                config['port'] = smtp_port
            config['use_tls'] = use_tls

            self.smtp_host = config['host']
            self.smtp_port = config['port']
            self.use_tls = config['use_tls']
        else:
            raise ValueError(f"Unknown email provider: {provider}")

        if not self.smtp_host:
            raise ValueError("SMTP host must be provided")

    def send_email(self,
                   from_email: str,
                   from_password: str,
                   to_emails: List[str],
                   subject: str,
                   body: str,
                   html: bool = False,
                   cc_emails: Optional[List[str]] = None,
                   bcc_emails: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Send an email

        Args:
            from_email: Sender email address
            from_password: Sender email password or app password
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content
            html: Whether body is HTML (default: False for plain text)
            cc_emails: List of CC recipients
            bcc_emails: List of BCC recipients
            attachments: List of file paths to attach

        Returns:
            Dict with status and message
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # Add body
            body_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, body_type))

            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            msg.attach(part)
                    else:
                        logger.warning(f"Attachment not found: {file_path}")

            # Combine all recipients
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(from_email, from_password)
                server.sendmail(from_email, all_recipients, msg.as_string())

            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")

            return {
                'status': 'success',
                'message': f'Email sent to {len(all_recipients)} recipients',
                'recipients': len(all_recipients)
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return {
                'status': 'error',
                'message': 'Authentication failed. Check email and password/app password.',
                'error': str(e)
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                'status': 'error',
                'message': f'SMTP error: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                'status': 'error',
                'message': f'Error: {str(e)}',
                'error': str(e)
            }

    def validate_config(self, from_email: str, from_password: str) -> Dict[str, any]:
        """
        Validate email configuration by testing connection

        Args:
            from_email: Email address to test
            from_password: Password or app password

        Returns:
            Dict with validation status
        """
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(from_email, from_password)

            return {
                'status': 'success',
                'message': 'Email configuration is valid'
            }
        except smtplib.SMTPAuthenticationError:
            return {
                'status': 'error',
                'message': 'Authentication failed. Check email and password.'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)}'
            }


# Global email service instance
email_service = EmailService()
