"""
Recommendation Agent - Generate recommendations based on evaluation
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class RecommendationAgent:
    """Generate recommendations from evaluation data"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - include_rationale: Include detailed rationale

        Returns:
            Recommendation with ranking and rationale
        """
        rubric_scores = state_data.get('rubric_output', {})
        benchmark = state_data.get('benchmark_output', {})

        prompt = f"""Based on this evaluation, provide a recommendation:

Rubric Scores: {rubric_scores.get('category_scores', {})}
Overall Score: {rubric_scores.get('weighted_score', 0)}
Benchmark Percentile: {benchmark.get('percentile', 0)}%

Provide:
1. Recommendation (accept/reject/revise)
2. Confidence level (0-1)
3. Rationale (brief)
4. Suggested improvements (if any)

JSON format:
{{
  "recommendation": "accept/reject/revise",
  "confidence": 0.0-1.0,
  "rationale": "explanation",
  "improvements": ["suggestion1", "suggestion2"]
}}"""

        response = await self.ollama_service.query(
            prompt=prompt,
            model=config.get('model', 'llama3.2:3b'),
            temperature=0.2,
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

        return {'recommendation': 'unknown', 'confidence': 0.0}
