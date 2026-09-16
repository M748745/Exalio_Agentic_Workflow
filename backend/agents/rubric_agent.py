"""
Rubric Agent - Evaluate entries based on predefined rubrics
For use in judging/scoring systems
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RubricAgent:
    """Evaluate content using structured rubrics"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate using rubric

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for input entry
                - rubric: Rubric definition (categories, weights, criteria)
                - industry: Industry/domain context

        Returns:
            Rubric evaluation with category scores
        """
        input_key = config.get('input_key', 'input')
        entry = state_data.get(input_key, {})
        rubric = config.get('rubric', {})
        industry = config.get('industry', 'general')

        prompt = f"""Evaluate this entry using the following rubric for {industry}.

Entry:
{entry.get('text', '')}

Rubric:
{self._format_rubric(rubric)}

Score each category (0-10) and provide rationale.

Respond in JSON format:
{{
  "category_scores": {{"category1": score, "category2": score, ...}},
  "weighted_score": 0-10,
  "rationale": {{"category1": "explanation", ...}}
}}"""

        response = await self.ollama_service.query(
            prompt=prompt,
            model=config.get('rubric_model', 'llama3.2:3b'),
            temperature=0.1,
            num_predict=1024
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
            logger.error(f"Failed to parse rubric response: {e}")

        return {'category_scores': {}, 'weighted_score': 0, 'error': 'Parse failed'}

    def _format_rubric(self, rubric: Dict[str, Any]) -> str:
        """Format rubric for prompt"""
        lines = []
        for category, details in rubric.items():
            weight = details.get('weight', 1.0)
            criteria = details.get('criteria', '')
            lines.append(f"- {category} (weight: {weight}): {criteria}")
        return '\n'.join(lines)
