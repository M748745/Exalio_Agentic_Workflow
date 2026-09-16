"""
Discord Integration - Post messages via webhooks
Send messages and embeds to Discord channels
"""

import requests
import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


class DiscordIntegration:
    """
    Discord integration using webhooks
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Discord integration

        Args:
            config: Configuration dict with:
                - webhook_url: Discord webhook URL
                - default_username: Bot username
                - default_avatar_url: Bot avatar URL
        """
        self.config = config
        self.webhook_url = config.get('webhook_url')
        self.default_username = config.get('default_username', 'Workflow Bot')
        self.default_avatar_url = config.get('default_avatar_url')

    def send_message(
        self,
        content: str,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        embeds: Optional[List[Dict]] = None,
        tts: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message to Discord

        Args:
            content: Message content (up to 2000 chars)
            username: Override webhook username
            avatar_url: Override webhook avatar
            embeds: List of Discord embeds
            tts: Text-to-speech

        Returns:
            Dict with status
        """
        if not self.webhook_url:
            return {
                'status': 'error',
                'error': 'Discord webhook_url not configured'
            }

        try:
            payload = {
                'content': content,
                'username': username or self.default_username,
                'tts': tts
            }

            if avatar_url or self.default_avatar_url:
                payload['avatar_url'] = avatar_url or self.default_avatar_url

            if embeds:
                payload['embeds'] = embeds

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code in [200, 204]:
                logger.info(f"Message sent to Discord")
                return {
                    'status': 'success',
                    'content': content[:50] + '...' if len(content) > 50 else content
                }
            else:
                raise Exception(f"Discord webhook failed: {response.text}")

        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def create_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00FF00,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Discord embed

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex integer, e.g., 0x00FF00 for green)
            fields: List of fields {name, value, inline}
            footer: Footer text
            thumbnail_url: Thumbnail image URL
            image_url: Large image URL
            url: Title URL

        Returns:
            Discord embed dict
        """
        embed = {
            'title': title,
            'description': description,
            'color': color
        }

        if url:
            embed['url'] = url

        if fields:
            embed['fields'] = fields

        if footer:
            embed['footer'] = {'text': footer}

        if thumbnail_url:
            embed['thumbnail'] = {'url': thumbnail_url}

        if image_url:
            embed['image'] = {'url': image_url}

        return embed

    def send_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00FF00,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a rich embed message

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            fields: Embed fields
            footer: Footer text

        Returns:
            Dict with status
        """
        embed = self.create_embed(title, description, color, fields, footer)
        return self.send_message(content='', embeds=[embed])


class DiscordAgent:
    """
    Agent wrapper for Discord integration
    Compatible with workflow engine
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Discord agent"""
        self.integration = DiscordIntegration(config)
        self.name = "discord_agent"
        self.description = "Send messages to Discord channels"

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Discord message sending

        Context should contain:
            - content: Message content
            - username: Bot username (optional)
            - avatar_url: Bot avatar (optional)
            - embeds: List of embeds (optional)
            - tts: Text-to-speech (optional)
        """
        try:
            content = context.get('content', '')

            if not content and not context.get('embeds'):
                return {
                    'status': 'error',
                    'error': 'content or embeds is required'
                }

            result = self.integration.send_message(
                content=content,
                username=context.get('username'),
                avatar_url=context.get('avatar_url'),
                embeds=context.get('embeds'),
                tts=context.get('tts', False)
            )

            return result

        except Exception as e:
            logger.error(f"Discord agent error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['DiscordIntegration', 'DiscordAgent']
