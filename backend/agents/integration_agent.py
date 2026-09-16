"""
Integration & Connectivity Agents (HIGH PRIORITY)
14 nodes for external system integration

Features:
- HTTP/REST API calls (GET, POST, PUT, DELETE)
- Webhooks (send/receive)
- Email (SMTP, SendGrid, Mailgun)
- SMS (Twilio)
- Messaging platforms (Slack, Discord, WhatsApp, Teams)
- File operations (read, write, move, delete)
- FTP/SFTP transfers
- Database operations (raw SQL)
- GraphQL queries
- WebSocket real-time communication

This enables workflows to interact with any external system.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import logging
import asyncio
import aiohttp
import smtplib
import ftplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import sqlite3
import base64
import re

logger = logging.getLogger(__name__)


# ============================================================================
# 1. HTTP REQUEST NODE
# ============================================================================

class HTTPRequestAgent:
    """
    Make HTTP/REST API calls
    Supports GET, POST, PUT, DELETE, PATCH
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute HTTP request

        Config:
            method: GET, POST, PUT, DELETE, PATCH
            url: Request URL (supports variable substitution)
            headers: Request headers dict
            body: Request body (for POST/PUT/PATCH)
            query_params: Query parameters dict
            timeout: Request timeout (seconds)
            auth: Authentication dict {type: 'basic'/'bearer', credentials: ...}
            retry: Retry config {max_retries: 3, backoff_factor: 2}
            verify_ssl: Verify SSL certificates (default: True)

        Returns:
            status_code, headers, body, success, response_time
        """
        try:
            method = self.config.get('method', 'GET').upper()
            url = self._substitute_variables(self.config.get('url', ''), inputs)
            headers = self.config.get('headers', {})
            body = inputs.get('body') or self.config.get('body')
            query_params = self.config.get('query_params', {})
            timeout = self.config.get('timeout', 30)
            verify_ssl = self.config.get('verify_ssl', True)
            auth_config = self.config.get('auth')
            retry_config = self.config.get('retry', {'max_retries': 3, 'backoff_factor': 2})

            # Add authentication
            if auth_config:
                headers = self._add_auth(headers, auth_config)

            # Execute with retry logic
            start_time = datetime.utcnow()
            response_data = await self._execute_with_retry(
                method, url, headers, body, query_params, timeout, verify_ssl, retry_config
            )
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()

            return {
                'success': True,
                'status_code': response_data['status_code'],
                'headers': response_data['headers'],
                'body': response_data['body'],
                'response_time': response_time,
                'url': url,
                'method': method
            }

        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'method': method
            }

    async def _execute_with_retry(
        self, method, url, headers, body, params, timeout, verify_ssl, retry_config
    ):
        """Execute HTTP request with retry logic"""
        max_retries = retry_config.get('max_retries', 3)
        backoff_factor = retry_config.get('backoff_factor', 2)

        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=body if isinstance(body, dict) else None,
                        data=body if isinstance(body, str) else None,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                        ssl=verify_ssl
                    ) as response:
                        response_body = await response.text()
                        try:
                            response_body = json.loads(response_body)
                        except:
                            pass

                        return {
                            'status_code': response.status,
                            'headers': dict(response.headers),
                            'body': response_body
                        }

            except Exception as e:
                if attempt == max_retries:
                    raise e
                wait_time = backoff_factor ** attempt
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

    def _add_auth(self, headers: Dict, auth_config: Dict) -> Dict:
        """Add authentication to headers"""
        auth_type = auth_config.get('type', 'bearer').lower()
        headers = headers.copy()

        if auth_type == 'bearer':
            token = auth_config.get('token')
            headers['Authorization'] = f"Bearer {token}"
        elif auth_type == 'basic':
            username = auth_config.get('username')
            password = auth_config.get('password')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f"Basic {credentials}"
        elif auth_type == 'api_key':
            key_name = auth_config.get('key_name', 'X-API-Key')
            api_key = auth_config.get('api_key')
            headers[key_name] = api_key

        return headers

    def _substitute_variables(self, text: str, inputs: Dict) -> str:
        """Substitute {variable} in text with values from inputs"""
        for key, value in inputs.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text


# ============================================================================
# 2. WEBHOOK SENDER NODE
# ============================================================================

class WebhookSenderAgent:
    """Send webhooks to external URLs"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send webhook

        Config:
            webhook_url: URL to send webhook to
            method: POST (default) or PUT
            payload: Webhook payload (JSON)
            headers: Custom headers
            secret: Webhook signing secret
            retry_on_failure: Whether to retry

        Returns:
            success, status_code, response
        """
        try:
            webhook_url = self.config.get('webhook_url')
            method = self.config.get('method', 'POST')
            payload = inputs.get('payload') or self.config.get('payload', {})
            headers = self.config.get('headers', {'Content-Type': 'application/json'})
            secret = self.config.get('secret')
            retry = self.config.get('retry_on_failure', True)

            # Add webhook signature if secret provided
            if secret:
                import hmac
                import hashlib
                payload_bytes = json.dumps(payload).encode()
                signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
                headers['X-Webhook-Signature'] = signature

            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=webhook_url,
                    json=payload,
                    headers=headers
                ) as response:
                    response_text = await response.text()

                    return {
                        'success': response.status < 400,
                        'status_code': response.status,
                        'response': response_text,
                        'webhook_url': webhook_url,
                        'timestamp': datetime.utcnow().isoformat()
                    }

        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'webhook_url': webhook_url
            }


# ============================================================================
# 3. WEBHOOK RECEIVER NODE
# ============================================================================

class WebhookReceiverAgent:
    """Receive and validate incoming webhooks"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive and validate webhook

        Config:
            secret: Webhook secret for signature validation
            validate_signature: Whether to validate signature
            allowed_sources: List of allowed IP addresses/domains

        Inputs:
            payload: Webhook payload
            headers: Request headers
            source_ip: Source IP address

        Returns:
            valid, payload, headers, source
        """
        try:
            payload = inputs.get('payload', {})
            headers = inputs.get('headers', {})
            source_ip = inputs.get('source_ip')

            validate_signature = self.config.get('validate_signature', True)
            secret = self.config.get('secret')
            allowed_sources = self.config.get('allowed_sources', [])

            # Validate signature
            signature_valid = True
            if validate_signature and secret:
                signature = headers.get('X-Webhook-Signature')
                if signature:
                    import hmac
                    import hashlib
                    payload_bytes = json.dumps(payload).encode()
                    expected_signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
                    signature_valid = hmac.compare_digest(signature, expected_signature)
                else:
                    signature_valid = False

            # Validate source
            source_valid = True
            if allowed_sources and source_ip:
                source_valid = source_ip in allowed_sources

            valid = signature_valid and source_valid

            return {
                'valid': valid,
                'signature_valid': signature_valid,
                'source_valid': source_valid,
                'payload': payload,
                'headers': headers,
                'source_ip': source_ip,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Webhook receive failed: {e}")
            return {
                'valid': False,
                'error': str(e)
            }


# ============================================================================
# 4. EMAIL NODE
# ============================================================================

class EmailAgent:
    """Send emails via SMTP, SendGrid, or Mailgun"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email

        Config:
            provider: 'smtp', 'sendgrid', 'mailgun'
            smtp_host: SMTP server (for SMTP provider)
            smtp_port: SMTP port (default: 587)
            smtp_username: SMTP username
            smtp_password: SMTP password
            api_key: API key (for SendGrid/Mailgun)
            from_email: Sender email
            from_name: Sender name

        Inputs:
            to: Recipient email(s) (string or list)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            subject: Email subject
            body: Email body (HTML or plain text)
            attachments: List of attachment file paths
            is_html: Whether body is HTML (default: False)

        Returns:
            success, message_id, error
        """
        try:
            provider = self.config.get('provider', 'smtp').lower()
            to_emails = inputs.get('to')
            if isinstance(to_emails, str):
                to_emails = [to_emails]

            subject = inputs.get('subject', '')
            body = inputs.get('body', '')
            cc = inputs.get('cc', [])
            bcc = inputs.get('bcc', [])
            attachments = inputs.get('attachments', [])
            is_html = inputs.get('is_html', False)

            if provider == 'smtp':
                result = await self._send_smtp(to_emails, subject, body, cc, bcc, attachments, is_html)
            elif provider == 'sendgrid':
                result = await self._send_sendgrid(to_emails, subject, body, cc, bcc, attachments, is_html)
            elif provider == 'mailgun':
                result = await self._send_mailgun(to_emails, subject, body, cc, bcc, attachments, is_html)
            else:
                raise ValueError(f"Unknown email provider: {provider}")

            return result

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _send_smtp(self, to_emails, subject, body, cc, bcc, attachments, is_html):
        """Send email via SMTP"""
        smtp_host = self.config.get('smtp_host')
        smtp_port = self.config.get('smtp_port', 587)
        smtp_username = self.config.get('smtp_username')
        smtp_password = self.config.get('smtp_password')
        from_email = self.config.get('from_email')
        from_name = self.config.get('from_name', from_email)

        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = ', '.join(cc)
        if bcc:
            msg['Bcc'] = ', '.join(bcc)

        # Attach body
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

        # Attach files
        for filepath in attachments:
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={Path(filepath).name}')
                msg.attach(part)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        return {
            'success': True,
            'provider': 'smtp',
            'to': to_emails,
            'subject': subject
        }

    async def _send_sendgrid(self, to_emails, subject, body, cc, bcc, attachments, is_html):
        """Send email via SendGrid API"""
        api_key = self.config.get('api_key')
        from_email = self.config.get('from_email')

        payload = {
            'personalizations': [{
                'to': [{'email': email} for email in to_emails],
                'subject': subject
            }],
            'from': {'email': from_email},
            'content': [{
                'type': 'text/html' if is_html else 'text/plain',
                'value': body
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.sendgrid.com/v3/mail/send',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload
            ) as response:
                return {
                    'success': response.status == 202,
                    'provider': 'sendgrid',
                    'status_code': response.status,
                    'to': to_emails
                }

    async def _send_mailgun(self, to_emails, subject, body, cc, bcc, attachments, is_html):
        """Send email via Mailgun API"""
        api_key = self.config.get('api_key')
        domain = self.config.get('mailgun_domain')
        from_email = self.config.get('from_email')

        data = {
            'from': from_email,
            'to': to_emails,
            'subject': subject,
            'html' if is_html else 'text': body
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'https://api.mailgun.net/v3/{domain}/messages',
                auth=aiohttp.BasicAuth('api', api_key),
                data=data
            ) as response:
                return {
                    'success': response.status == 200,
                    'provider': 'mailgun',
                    'status_code': response.status,
                    'to': to_emails
                }


# ============================================================================
# 5. SMS NODE (Twilio)
# ============================================================================

class SMSAgent:
    """Send SMS via Twilio"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send SMS

        Config:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Twilio phone number

        Inputs:
            to: Recipient phone number
            message: SMS message text
            media_url: Optional media URL (MMS)

        Returns:
            success, message_sid, status
        """
        try:
            account_sid = self.config.get('account_sid')
            auth_token = self.config.get('auth_token')
            from_number = self.config.get('from_number')

            to_number = inputs.get('to')
            message = inputs.get('message')
            media_url = inputs.get('media_url')

            # Twilio API endpoint
            url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'

            data = {
                'From': from_number,
                'To': to_number,
                'Body': message
            }

            if media_url:
                data['MediaUrl'] = media_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    auth=aiohttp.BasicAuth(account_sid, auth_token),
                    data=data
                ) as response:
                    response_data = await response.json()

                    return {
                        'success': response.status == 201,
                        'message_sid': response_data.get('sid'),
                        'status': response_data.get('status'),
                        'to': to_number,
                        'from': from_number
                    }

        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 6. SLACK NODE
# ============================================================================

class SlackAgent:
    """Send messages to Slack"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Slack message

        Config:
            bot_token: Slack bot token
            webhook_url: Slack webhook URL (alternative to bot token)

        Inputs:
            channel: Channel ID or name (#general)
            text: Message text
            blocks: Slack blocks (rich formatting)
            thread_ts: Thread timestamp (for replies)

        Returns:
            success, message_ts, channel
        """
        try:
            bot_token = self.config.get('bot_token')
            webhook_url = self.config.get('webhook_url')

            channel = inputs.get('channel')
            text = inputs.get('text')
            blocks = inputs.get('blocks')
            thread_ts = inputs.get('thread_ts')

            if webhook_url:
                # Use webhook
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook_url,
                        json={'text': text, 'blocks': blocks} if blocks else {'text': text}
                    ) as response:
                        return {
                            'success': response.status == 200,
                            'method': 'webhook'
                        }
            else:
                # Use bot token
                url = 'https://slack.com/api/chat.postMessage'
                payload = {
                    'channel': channel,
                    'text': text
                }
                if blocks:
                    payload['blocks'] = blocks
                if thread_ts:
                    payload['thread_ts'] = thread_ts

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers={
                            'Authorization': f'Bearer {bot_token}',
                            'Content-Type': 'application/json'
                        },
                        json=payload
                    ) as response:
                        response_data = await response.json()

                        return {
                            'success': response_data.get('ok', False),
                            'message_ts': response_data.get('ts'),
                            'channel': response_data.get('channel'),
                            'method': 'bot_token'
                        }

        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 7. DISCORD NODE
# ============================================================================

class DiscordAgent:
    """Send messages to Discord"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Discord message

        Config:
            webhook_url: Discord webhook URL
            bot_token: Discord bot token (alternative)

        Inputs:
            content: Message content
            embeds: Discord embeds (rich formatting)
            username: Override webhook username
            avatar_url: Override webhook avatar

        Returns:
            success, message_id
        """
        try:
            webhook_url = self.config.get('webhook_url')

            content = inputs.get('content')
            embeds = inputs.get('embeds', [])
            username = inputs.get('username')
            avatar_url = inputs.get('avatar_url')

            payload = {'content': content}
            if embeds:
                payload['embeds'] = embeds
            if username:
                payload['username'] = username
            if avatar_url:
                payload['avatar_url'] = avatar_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload
                ) as response:
                    return {
                        'success': response.status in [200, 204],
                        'status_code': response.status
                    }

        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 8. WHATSAPP NODE
# ============================================================================

class WhatsAppAgent:
    """Send WhatsApp messages via Twilio"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send WhatsApp message

        Config:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: WhatsApp-enabled Twilio number

        Inputs:
            to: Recipient WhatsApp number (whatsapp:+1234567890)
            message: Message text
            media_url: Optional media URL

        Returns:
            success, message_sid, status
        """
        try:
            account_sid = self.config.get('account_sid')
            auth_token = self.config.get('auth_token')
            from_number = self.config.get('from_number')

            to_number = inputs.get('to')
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'

            message = inputs.get('message')
            media_url = inputs.get('media_url')

            url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'

            data = {
                'From': f'whatsapp:{from_number}',
                'To': to_number,
                'Body': message
            }

            if media_url:
                data['MediaUrl'] = media_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    auth=aiohttp.BasicAuth(account_sid, auth_token),
                    data=data
                ) as response:
                    response_data = await response.json()

                    return {
                        'success': response.status == 201,
                        'message_sid': response_data.get('sid'),
                        'status': response_data.get('status'),
                        'to': to_number
                    }

        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 9. MICROSOFT TEAMS NODE
# ============================================================================

class TeamsAgent:
    """Send messages to Microsoft Teams"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Teams message

        Config:
            webhook_url: Teams incoming webhook URL

        Inputs:
            title: Message title
            text: Message text
            theme_color: Hex color for message theme
            sections: List of message sections

        Returns:
            success, status_code
        """
        try:
            webhook_url = self.config.get('webhook_url')

            title = inputs.get('title')
            text = inputs.get('text')
            theme_color = inputs.get('theme_color', '0078D4')
            sections = inputs.get('sections', [])

            # Teams message card format
            payload = {
                '@type': 'MessageCard',
                '@context': 'https://schema.org/extensions',
                'summary': title,
                'themeColor': theme_color,
                'title': title,
                'text': text,
                'sections': sections
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload
                ) as response:
                    return {
                        'success': response.status == 200,
                        'status_code': response.status
                    }

        except Exception as e:
            logger.error(f"Teams send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 10. FILE OPERATIONS NODE
# ============================================================================

class FileOperationsAgent:
    """Read, write, move, delete files"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        File operations

        Config:
            operation: 'read', 'write', 'append', 'move', 'copy', 'delete', 'list', 'exists'
            base_path: Base directory (security constraint)

        Inputs:
            path: File/directory path
            content: Content to write (for write/append)
            destination: Destination path (for move/copy)
            encoding: File encoding (default: utf-8)
            mode: Read mode - 'text' or 'binary'

        Returns:
            success, content (for read), files (for list), exists (for exists)
        """
        try:
            operation = self.config.get('operation', 'read')
            base_path = Path(self.config.get('base_path', '.'))

            file_path = Path(inputs.get('path', ''))

            # Security: Ensure path is within base_path
            full_path = (base_path / file_path).resolve()
            if not str(full_path).startswith(str(base_path.resolve())):
                raise ValueError("Path outside allowed base directory")

            if operation == 'read':
                mode = inputs.get('mode', 'text')
                encoding = inputs.get('encoding', 'utf-8')

                if mode == 'binary':
                    with open(full_path, 'rb') as f:
                        content = base64.b64encode(f.read()).decode()
                else:
                    with open(full_path, 'r', encoding=encoding) as f:
                        content = f.read()

                return {
                    'success': True,
                    'content': content,
                    'path': str(full_path),
                    'size': full_path.stat().st_size,
                    'mode': mode
                }

            elif operation == 'write':
                content = inputs.get('content', '')
                encoding = inputs.get('encoding', 'utf-8')
                mode = inputs.get('mode', 'text')

                full_path.parent.mkdir(parents=True, exist_ok=True)

                if mode == 'binary':
                    with open(full_path, 'wb') as f:
                        f.write(base64.b64decode(content))
                else:
                    with open(full_path, 'w', encoding=encoding) as f:
                        f.write(content)

                return {
                    'success': True,
                    'path': str(full_path),
                    'bytes_written': len(content)
                }

            elif operation == 'append':
                content = inputs.get('content', '')
                encoding = inputs.get('encoding', 'utf-8')

                with open(full_path, 'a', encoding=encoding) as f:
                    f.write(content)

                return {
                    'success': True,
                    'path': str(full_path)
                }

            elif operation == 'move':
                destination = Path(inputs.get('destination', ''))
                dest_full = (base_path / destination).resolve()

                if not str(dest_full).startswith(str(base_path.resolve())):
                    raise ValueError("Destination outside allowed base directory")

                dest_full.parent.mkdir(parents=True, exist_ok=True)
                full_path.rename(dest_full)

                return {
                    'success': True,
                    'from': str(full_path),
                    'to': str(dest_full)
                }

            elif operation == 'copy':
                import shutil
                destination = Path(inputs.get('destination', ''))
                dest_full = (base_path / destination).resolve()

                if not str(dest_full).startswith(str(base_path.resolve())):
                    raise ValueError("Destination outside allowed base directory")

                dest_full.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_path, dest_full)

                return {
                    'success': True,
                    'from': str(full_path),
                    'to': str(dest_full)
                }

            elif operation == 'delete':
                if full_path.is_file():
                    full_path.unlink()
                elif full_path.is_dir():
                    import shutil
                    shutil.rmtree(full_path)

                return {
                    'success': True,
                    'deleted': str(full_path)
                }

            elif operation == 'list':
                pattern = inputs.get('pattern', '*')
                files = [str(p) for p in full_path.glob(pattern)]

                return {
                    'success': True,
                    'files': files,
                    'count': len(files),
                    'directory': str(full_path)
                }

            elif operation == 'exists':
                exists = full_path.exists()

                return {
                    'success': True,
                    'exists': exists,
                    'path': str(full_path),
                    'is_file': full_path.is_file() if exists else False,
                    'is_dir': full_path.is_dir() if exists else False
                }

        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'operation': operation
            }


# ============================================================================
# 11. FTP/SFTP NODE
# ============================================================================

class FTPAgent:
    """FTP/SFTP file transfer"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        FTP/SFTP operations

        Config:
            protocol: 'ftp' or 'sftp'
            host: FTP server hostname
            port: FTP server port (21 for FTP, 22 for SFTP)
            username: FTP username
            password: FTP password
            operation: 'upload', 'download', 'list', 'delete'

        Inputs:
            local_path: Local file path
            remote_path: Remote file path
            passive: Use passive mode (FTP only)

        Returns:
            success, transferred_bytes, files (for list)
        """
        try:
            protocol = self.config.get('protocol', 'ftp').lower()
            host = self.config.get('host')
            port = self.config.get('port', 21 if protocol == 'ftp' else 22)
            username = self.config.get('username')
            password = self.config.get('password')
            operation = self.config.get('operation', 'upload')

            local_path = inputs.get('local_path')
            remote_path = inputs.get('remote_path')

            if protocol == 'ftp':
                return await self._ftp_operation(
                    host, port, username, password, operation, local_path, remote_path
                )
            elif protocol == 'sftp':
                return await self._sftp_operation(
                    host, port, username, password, operation, local_path, remote_path
                )

        except Exception as e:
            logger.error(f"FTP operation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _ftp_operation(self, host, port, username, password, operation, local_path, remote_path):
        """FTP operations"""
        with ftplib.FTP() as ftp:
            ftp.connect(host, port)
            ftp.login(username, password)

            if operation == 'upload':
                with open(local_path, 'rb') as f:
                    ftp.storbinary(f'STOR {remote_path}', f)
                size = Path(local_path).stat().st_size
                return {
                    'success': True,
                    'operation': 'upload',
                    'transferred_bytes': size,
                    'local_path': local_path,
                    'remote_path': remote_path
                }

            elif operation == 'download':
                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {remote_path}', f.write)
                size = Path(local_path).stat().st_size
                return {
                    'success': True,
                    'operation': 'download',
                    'transferred_bytes': size,
                    'local_path': local_path,
                    'remote_path': remote_path
                }

            elif operation == 'list':
                files = ftp.nlst(remote_path)
                return {
                    'success': True,
                    'operation': 'list',
                    'files': files,
                    'count': len(files)
                }

            elif operation == 'delete':
                ftp.delete(remote_path)
                return {
                    'success': True,
                    'operation': 'delete',
                    'remote_path': remote_path
                }

    async def _sftp_operation(self, host, port, username, password, operation, local_path, remote_path):
        """SFTP operations (placeholder - requires paramiko)"""
        # Note: This would require paramiko library
        # For now, return not implemented
        return {
            'success': False,
            'error': 'SFTP requires paramiko library (not installed)'
        }


# ============================================================================
# 12. DATABASE OPERATIONS NODE
# ============================================================================

class DatabaseOperationsAgent:
    """Execute SQL queries on databases"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SQL query

        Config:
            db_type: 'sqlite', 'postgresql', 'mysql'
            connection_string: Database connection string
            database: Database file path (for SQLite)

        Inputs:
            query: SQL query to execute
            params: Query parameters (for parameterized queries)
            operation: 'select', 'insert', 'update', 'delete', 'execute'

        Returns:
            success, rows (for select), affected_rows (for insert/update/delete)
        """
        try:
            db_type = self.config.get('db_type', 'sqlite').lower()
            query = inputs.get('query')
            params = inputs.get('params', [])
            operation = inputs.get('operation', 'select')

            if db_type == 'sqlite':
                return await self._sqlite_operation(query, params, operation)
            else:
                return {
                    'success': False,
                    'error': f'{db_type} not yet implemented (requires additional libraries)'
                }

        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _sqlite_operation(self, query, params, operation):
        """SQLite operations"""
        database = self.config.get('database', 'workflow.db')

        conn = sqlite3.connect(database)
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)

            if operation == 'select':
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                # Convert to list of dicts
                results = [dict(zip(columns, row)) for row in rows]

                return {
                    'success': True,
                    'rows': results,
                    'row_count': len(results),
                    'columns': columns
                }
            else:
                conn.commit()
                return {
                    'success': True,
                    'affected_rows': cursor.rowcount
                }

        finally:
            cursor.close()
            conn.close()


# ============================================================================
# 13. GRAPHQL NODE
# ============================================================================

class GraphQLAgent:
    """Execute GraphQL queries"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute GraphQL query

        Config:
            endpoint: GraphQL endpoint URL
            headers: Request headers (for authentication)

        Inputs:
            query: GraphQL query string
            variables: Query variables dict
            operation_name: Operation name (optional)

        Returns:
            success, data, errors
        """
        try:
            endpoint = self.config.get('endpoint')
            headers = self.config.get('headers', {'Content-Type': 'application/json'})

            query = inputs.get('query')
            variables = inputs.get('variables', {})
            operation_name = inputs.get('operation_name')

            payload = {
                'query': query,
                'variables': variables
            }
            if operation_name:
                payload['operationName'] = operation_name

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=headers
                ) as response:
                    response_data = await response.json()

                    return {
                        'success': 'errors' not in response_data,
                        'data': response_data.get('data'),
                        'errors': response_data.get('errors', []),
                        'status_code': response.status
                    }

        except Exception as e:
            logger.error(f"GraphQL query failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# 14. WEBSOCKET NODE
# ============================================================================

class WebSocketAgent:
    """WebSocket real-time communication"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        WebSocket operations

        Config:
            url: WebSocket URL (ws:// or wss://)
            operation: 'send', 'receive', 'connect', 'disconnect'

        Inputs:
            message: Message to send
            timeout: Receive timeout (seconds)

        Returns:
            success, message (for receive), status
        """
        try:
            url = self.config.get('url')
            operation = self.config.get('operation', 'send')

            message = inputs.get('message')
            timeout = inputs.get('timeout', 30)

            if operation == 'send':
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(url) as ws:
                        await ws.send_str(json.dumps(message) if isinstance(message, dict) else message)

                        return {
                            'success': True,
                            'operation': 'send',
                            'message': message
                        }

            elif operation == 'receive':
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(url) as ws:
                        msg = await asyncio.wait_for(ws.receive(), timeout=timeout)

                        return {
                            'success': True,
                            'operation': 'receive',
                            'message': msg.data,
                            'type': str(msg.type)
                        }

        except Exception as e:
            logger.error(f"WebSocket operation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'HTTPRequestAgent',
    'WebhookSenderAgent',
    'WebhookReceiverAgent',
    'EmailAgent',
    'SMSAgent',
    'SlackAgent',
    'DiscordAgent',
    'WhatsAppAgent',
    'TeamsAgent',
    'FileOperationsAgent',
    'FTPAgent',
    'DatabaseOperationsAgent',
    'GraphQLAgent',
    'WebSocketAgent'
]
