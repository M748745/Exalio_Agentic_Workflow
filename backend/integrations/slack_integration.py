"""
Slack Integration - Post messages, upload files, manage channels
Uses Slack Webhook and API
"""

import requests
import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


class SlackIntegration:
    """
    Slack integration supporting webhooks and API
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Slack integration

        Args:
            config: Configuration dict with:
                - webhook_url: Slack webhook URL (for simple posting)
                - bot_token: Slack bot token (for advanced API)
                - default_channel: Default channel to post to
        """
        self.config = config
        self.webhook_url = config.get('webhook_url')
        self.bot_token = config.get('bot_token')
        self.default_channel = config.get('default_channel', '#general')

    def post_message(
        self,
        text: str,
        channel: Optional[str] = None,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Post a message to Slack

        Args:
            text: Message text
            channel: Channel to post to (override default)
            username: Bot username to display
            icon_emoji: Bot icon emoji (e.g., :robot_face:)
            blocks: Slack Block Kit blocks
            attachments: Slack message attachments

        Returns:
            Dict with status
        """
        try:
            if self.webhook_url:
                return self._post_via_webhook(
                    text, channel, username, icon_emoji, blocks, attachments
                )
            elif self.bot_token:
                return self._post_via_api(
                    text, channel, username, icon_emoji, blocks, attachments
                )
            else:
                raise ValueError("Neither webhook_url nor bot_token configured")

        except Exception as e:
            logger.error(f"Failed to post to Slack: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _post_via_webhook(
        self,
        text: str,
        channel: Optional[str] = None,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Post message via webhook"""

        payload = {
            'text': text
        }

        if channel:
            payload['channel'] = channel

        if username:
            payload['username'] = username

        if icon_emoji:
            payload['icon_emoji'] = icon_emoji

        if blocks:
            payload['blocks'] = blocks

        if attachments:
            payload['attachments'] = attachments

        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            logger.info(f"Message posted to Slack via webhook")
            return {
                'status': 'success',
                'method': 'webhook',
                'text': text
            }
        else:
            raise Exception(f"Webhook failed: {response.text}")

    def _post_via_api(
        self,
        text: str,
        channel: Optional[str] = None,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Post message via Slack API"""

        channel = channel or self.default_channel

        payload = {
            'channel': channel,
            'text': text
        }

        if username:
            payload['username'] = username

        if icon_emoji:
            payload['icon_emoji'] = icon_emoji

        if blocks:
            payload['blocks'] = blocks

        if attachments:
            payload['attachments'] = attachments

        response = requests.post(
            'https://slack.com/api/chat.postMessage',
            json=payload,
            headers={
                'Authorization': f'Bearer {self.bot_token}',
                'Content-Type': 'application/json'
            }
        )

        data = response.json()

        if data.get('ok'):
            logger.info(f"Message posted to Slack via API to {channel}")
            return {
                'status': 'success',
                'method': 'api',
                'channel': channel,
                'text': text,
                'ts': data.get('ts')
            }
        else:
            raise Exception(f"API failed: {data.get('error')}")

    def upload_file(
        self,
        file_path: str,
        channels: Optional[List[str]] = None,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Slack

        Args:
            file_path: Path to file to upload
            channels: List of channels to share with
            title: File title
            initial_comment: Comment to add with file

        Returns:
            Dict with status
        """
        if not self.bot_token:
            raise ValueError("Bot token required for file upload")

        try:
            channels = channels or [self.default_channel]

            with open(file_path, 'rb') as f:
                response = requests.post(
                    'https://slack.com/api/files.upload',
                    headers={'Authorization': f'Bearer {self.bot_token}'},
                    files={'file': f},
                    data={
                        'channels': ','.join(channels),
                        'title': title or file_path,
                        'initial_comment': initial_comment or ''
                    }
                )

            data = response.json()

            if data.get('ok'):
                logger.info(f"File uploaded to Slack: {file_path}")
                return {
                    'status': 'success',
                    'file_id': data['file']['id'],
                    'channels': channels
                }
            else:
                raise Exception(f"Upload failed: {data.get('error')}")

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def create_rich_message(
        self,
        title: str,
        text: str,
        color: str = '#36a64f',
        fields: Optional[List[Dict[str, str]]] = None,
        footer: Optional[str] = None
    ) -> List[Dict]:
        """
        Create a rich message with attachments

        Args:
            title: Message title
            text: Message text
            color: Sidebar color (hex)
            fields: List of fields {title, value, short}
            footer: Footer text

        Returns:
            List of attachments for Slack
        """
        attachment = {
            'color': color,
            'title': title,
            'text': text,
            'footer': footer or 'Agentic Workflow',
            'ts': int(__import__('time').time())
        }

        if fields:
            attachment['fields'] = fields

        return [attachment]


class SlackAgent:
    """
    Agent wrapper for Slack integration
    Compatible with workflow engine
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Slack agent"""
        self.integration = SlackIntegration(config)
        self.name = "slack_agent"
        self.description = "Post messages and files to Slack"

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Slack action

        Context should contain:
            - action: 'post_message' or 'upload_file'
            - text: Message text (for post_message)
            - channel: Channel name (optional)
            - file_path: File path (for upload_file)
            - title: Message/file title (optional)
            - blocks: Slack blocks (optional)
            - attachments: Slack attachments (optional)
        """
        try:
            action = context.get('action', 'post_message')

            if action == 'post_message':
                text = context.get('text', '')
                if not text:
                    return {
                        'status': 'error',
                        'error': 'text is required for post_message'
                    }

                result = self.integration.post_message(
                    text=text,
                    channel=context.get('channel'),
                    username=context.get('username'),
                    icon_emoji=context.get('icon_emoji'),
                    blocks=context.get('blocks'),
                    attachments=context.get('attachments')
                )

            elif action == 'upload_file':
                file_path = context.get('file_path')
                if not file_path:
                    return {
                        'status': 'error',
                        'error': 'file_path is required for upload_file'
                    }

                result = self.integration.upload_file(
                    file_path=file_path,
                    channels=context.get('channels'),
                    title=context.get('title'),
                    initial_comment=context.get('initial_comment')
                )

            else:
                return {
                    'status': 'error',
                    'error': f'Unknown action: {action}'
                }

            return result

        except Exception as e:
            logger.error(f"Slack agent error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['SlackIntegration', 'SlackAgent']
