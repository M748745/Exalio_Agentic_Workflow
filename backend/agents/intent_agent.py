"""
Intent Agent - Understand user intent and extract entities
For HR Assistant and conversational workflows
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class IntentAgent:
    """Understand user intent from natural language"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Understand intent from user query

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for user query
                - supported_intents: List of supported intents

        Returns:
            Intent classification and entities
        """
        input_key = config.get('input_key', 'input')
        query = state_data.get(input_key, {}).get('question', '')
        supported_intents = config.get('supported_intents', ['query', 'request', 'update'])

        prompt = f"""Analyze this user query and identify:
1. Primary intent from: {', '.join(supported_intents)}
2. Key entities (people, dates, policies, etc.)
3. Required actions

Query: {query}

JSON format:
{{
  "intent": "primary_intent",
  "confidence": 0.0-1.0,
  "entities": {{"entity_type": "value"}},
  "actions": ["action1", "action2"]
}}"""

        response = await self.ollama_service.query(
            prompt=prompt,
            model=config.get('model', 'llama3.2:3b'),
            temperature=0.1,
            num_predict=512
        )

        # Parse JSON
        import json
        import re
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Parse failed: {e}")

        return {'intent': 'unknown', 'confidence': 0.0, 'entities': {}}
