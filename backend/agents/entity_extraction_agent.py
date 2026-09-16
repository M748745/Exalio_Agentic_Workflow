"""
Entity Extraction Agent - Extract structured entities from text
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class EntityExtractionAgent:
    """Extract named entities from text"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from text

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for input text
                - entity_types: Types of entities to extract

        Returns:
            Extracted entities
        """
        input_key = config.get('input_key', 'intent_output')
        text = state_data.get(input_key, {}).get('text', '')
        entity_types = config.get('entity_types', ['PERSON', 'ORG', 'DATE', 'POLICY'])

        prompt = f"""Extract these entity types from the text:
{', '.join(entity_types)}

Text: {text}

JSON format:
{{
  "entities": [
    {{"type": "PERSON", "value": "John Doe", "context": "employee"}},
    {{"type": "DATE", "value": "2024-01-15", "context": "leave date"}}
  ]
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

        return {'entities': []}
