"""
AI Detection Agent - Detect AI-generated content
Uses LLM-based analysis for pattern recognition
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AIDetectionAgent:
    """Detect AI-generated content using pattern analysis"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if content is AI-generated

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for input text
                - detection_model: Model to use for detection

        Returns:
            Detection results with confidence score
        """
        input_key = config.get('input_key', 'similarity_output')
        text = state_data.get(input_key, {}).get('text', '')

        if not text:
            return {'is_ai_generated': False, 'confidence': 0.0, 'error': 'No input text'}

        prompt = f"""Analyze this text and determine if it was AI-generated.
Consider: repetitive patterns, unusual phrasing, overly formal tone, lack of personal touches.

Text:
{text[:2000]}

Respond in JSON format:
{{
  "is_ai_generated": true/false,
  "confidence": 0.0-1.0,
  "indicators": ["list", "of", "indicators"],
  "explanation": "brief explanation"
}}"""

        response = await self.ollama_service.query(
            prompt=prompt,
            model=config.get('detection_model', 'llama3.2:3b'),
            temperature=0.1,
            num_predict=512
        )

        # Parse JSON response
        import json
        import re
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except Exception as e:
            logger.error(f"Failed to parse AI detection response: {e}")

        return {'is_ai_generated': False, 'confidence': 0.0, 'error': 'Parse failed'}
