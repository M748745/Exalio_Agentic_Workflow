"""
Benchmarking Agent - Compare entry against historical data
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BenchmarkingAgent:
    """Compare entries against historical benchmarks"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Benchmark against historical data

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for current entry scores
                - historical_data_key: Key for historical entries
                - comparison_metrics: Metrics to compare

        Returns:
            Benchmark comparison results
        """
        input_key = config.get('input_key', 'rubric_output')
        historical_key = config.get('historical_data_key', 'historical_entries')

        current_scores = state_data.get(input_key, {})
        historical_data = state_data.get(historical_key, [])

        if not historical_data:
            return {'percentile': 0, 'rank': 0, 'comparison': 'No historical data'}

        # Compute percentile
        current_score = current_scores.get('weighted_score', 0)
        historical_scores = [h.get('weighted_score', 0) for h in historical_data]

        percentile = sum(1 for s in historical_scores if s <= current_score) / len(historical_scores) * 100

        return {
            'percentile': percentile,
            'rank': sum(1 for s in historical_scores if s > current_score) + 1,
            'total_entries': len(historical_data),
            'average_score': sum(historical_scores) / len(historical_scores),
            'current_score': current_score,
            'comparison': f"Top {100-percentile:.1f}%"
        }
