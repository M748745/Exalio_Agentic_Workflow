"""
Integration modules for external services
Email, Slack, SMS, Discord, Database integrations
"""

from .email_integration import EmailIntegration, EmailAgent
from .slack_integration import SlackIntegration, SlackAgent
from .sms_integration import SMSIntegration, SMSAgent
from .discord_integration import DiscordIntegration, DiscordAgent
from .database_integration import DatabaseIntegration, DatabaseAgent

__all__ = [
    'EmailIntegration', 'EmailAgent',
    'SlackIntegration', 'SlackAgent',
    'SMSIntegration', 'SMSAgent',
    'DiscordIntegration', 'DiscordAgent',
    'DatabaseIntegration', 'DatabaseAgent'
]
