"""
Slack Service
Handles Slack message sending and integration via Slack Web API
"""

from typing import Dict, List, Optional, Any
import requests


class SlackService:
    """Service for sending Slack messages via webhooks or Web API"""

    def __init__(self):
        """Initialize Slack service"""
        pass

    def send_message(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        channel: Optional[str] = None,
        message: str = "",
        username: Optional[str] = "Workflow Bot",
        icon_emoji: Optional[str] = ":robot_face:",
        thread_ts: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Slack

        Args:
            webhook_url: Incoming webhook URL (simpler method)
            bot_token: Bot User OAuth Token (for more features)
            channel: Channel ID or name (e.g., #general, C1234567890)
            message: Message text
            username: Display name for the bot
            icon_emoji: Emoji icon for the bot
            thread_ts: Parent message timestamp (for threading)
            attachments: Message attachments (legacy)
            blocks: Block Kit blocks (modern formatting)

        Returns:
            Dictionary with status and result
        """
        try:
            # Validate inputs
            if not message:
                return {
                    "status": "error",
                    "message": "Message text is required"
                }

            # Use webhook method if webhook_url is provided
            if webhook_url:
                return self._send_via_webhook(
                    webhook_url=webhook_url,
                    message=message,
                    username=username,
                    icon_emoji=icon_emoji,
                    attachments=attachments,
                    blocks=blocks
                )

            # Use Web API method if bot_token is provided
            elif bot_token and channel:
                return self._send_via_web_api(
                    bot_token=bot_token,
                    channel=channel,
                    message=message,
                    username=username,
                    icon_emoji=icon_emoji,
                    thread_ts=thread_ts,
                    attachments=attachments,
                    blocks=blocks
                )

            else:
                return {
                    "status": "error",
                    "message": "Either webhook_url OR (bot_token + channel) must be provided"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Slack message failed: {str(e)}",
                "error": str(e)
            }

    def _send_via_webhook(
        self,
        webhook_url: str,
        message: str,
        username: Optional[str],
        icon_emoji: Optional[str],
        attachments: Optional[List[Dict]],
        blocks: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Send message via Incoming Webhook"""
        try:
            payload = {
                "text": message
            }

            if username:
                payload["username"] = username

            if icon_emoji:
                payload["icon_emoji"] = icon_emoji

            if attachments:
                payload["attachments"] = attachments

            if blocks:
                payload["blocks"] = blocks

            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 and response.text == "ok":
                return {
                    "status": "success",
                    "message": "Slack message sent via webhook",
                    "method": "webhook"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Webhook failed: {response.text}",
                    "status_code": response.status_code
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Webhook error: {str(e)}",
                "error": str(e)
            }

    def _send_via_web_api(
        self,
        bot_token: str,
        channel: str,
        message: str,
        username: Optional[str],
        icon_emoji: Optional[str],
        thread_ts: Optional[str],
        attachments: Optional[List[Dict]],
        blocks: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Send message via Slack Web API (chat.postMessage)"""
        try:
            url = "https://slack.com/api/chat.postMessage"

            headers = {
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "channel": channel,
                "text": message
            }

            if username:
                payload["username"] = username

            if icon_emoji:
                payload["icon_emoji"] = icon_emoji

            if thread_ts:
                payload["thread_ts"] = thread_ts

            if attachments:
                payload["attachments"] = attachments

            if blocks:
                payload["blocks"] = blocks

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )

            response_data = response.json()

            if response_data.get("ok"):
                return {
                    "status": "success",
                    "message": "Slack message sent via Web API",
                    "method": "web_api",
                    "channel": response_data.get("channel"),
                    "ts": response_data.get("ts")
                }
            else:
                error = response_data.get("error", "Unknown error")
                return {
                    "status": "error",
                    "message": f"Slack API error: {error}",
                    "error": error
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Web API error: {str(e)}",
                "error": str(e)
            }

    def validate_config(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate Slack configuration

        Returns:
            Dictionary with validation status
        """
        try:
            if webhook_url:
                # Validate webhook URL format
                if not webhook_url.startswith("https://hooks.slack.com"):
                    return {
                        "status": "error",
                        "message": "Invalid webhook URL format. Should start with https://hooks.slack.com"
                    }
                return {
                    "status": "success",
                    "message": "Webhook URL format is valid"
                }

            elif bot_token and channel:
                # Validate bot token format
                if not bot_token.startswith("xoxb-"):
                    return {
                        "status": "error",
                        "message": "Invalid bot token format. Should start with xoxb-"
                    }
                return {
                    "status": "success",
                    "message": "Bot token and channel configuration is valid"
                }

            else:
                return {
                    "status": "error",
                    "message": "Either webhook_url OR (bot_token + channel) must be provided"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Validation error: {str(e)}"
            }

    def create_blocks(self, text: str, title: Optional[str] = None) -> List[Dict]:
        """
        Create Block Kit blocks for richer formatting

        Args:
            text: Main message text
            title: Optional title/header

        Returns:
            List of Block Kit blocks
        """
        blocks = []

        if title:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            })

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })

        return blocks


# Global Slack service instance
slack_service = SlackService()
