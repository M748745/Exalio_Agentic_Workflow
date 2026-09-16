"""
Scoring Agent - Score content based on criteria with confidence levels
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ScoringAgent:
    """Score content based on configurable criteria"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score content based on criteria

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for input data
                - criteria: List of scoring criteria
                - scoring_model: Model to use for scoring

        Returns:
            Scores with confidence levels
        """
        input_key = config.get('input_key', 'ai_detection_output')
        criteria = config.get('criteria', ['quality', 'originality', 'relevance'])

        # Gather data from previous steps
        ocr_data = state_data.get('ocr_output', {})
        similarity_data = state_data.get('similarity_output', {})
        ai_detection = state_data.get('ai_detection_output', {})

        text = ocr_data.get('text', '')
        similarity_score = similarity_data.get('matches', [{}])[0].get('overall_score', 0.0) if similarity_data.get('matches') else 0.0
        is_ai_generated = ai_detection.get('is_ai_generated', False)

        prompt = f"""Score the following content on these criteria (0-100 scale):
{', '.join(criteria)}

Content: {text[:1500]}

Additional context:
- Similarity to existing content: {similarity_score:.2f}
- AI-generated detection: {is_ai_generated}

Respond in JSON format:
{{
  "scores": {{"criterion1": score1, "criterion2": score2, ...}},
  "overall_score": 0-100,
  "confidence": 0.0-1.0,
  "explanation": "brief explanation"
}}"""

        response = await self.ollama_service.query(
            prompt=prompt,
            model=config.get('scoring_model', 'llama3.2:3b'),
            temperature=0.2,
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
            logger.error(f"Failed to parse scoring response: {e}")

        return {'scores': {}, 'overall_score': 0, 'confidence': 0.0, 'error': 'Parse failed'}
