"""
LLMOps Monitoring & Observability (AI Planet Feature)
Track performance, costs, latency, and errors in real-time
Features:
- Cost monitoring & optimization (0.5-60x savings)
- Latency tracking
- Token usage analytics
- Error monitoring
- Performance dashboard
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class LLMMetrics:
    """Metrics for a single LLM call"""
    timestamp: datetime
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    success: bool
    error: Optional[str] = None
    user_id: Optional[str] = None
    workflow_id: Optional[str] = None


@dataclass
class AggregateLLMMetrics:
    """Aggregated metrics over a time period"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    calls_per_minute: float = 0.0
    error_rate: float = 0.0
    cost_per_1k_tokens: float = 0.0
    provider_breakdown: Dict[str, int] = field(default_factory=dict)
    model_breakdown: Dict[str, int] = field(default_factory=dict)


# Cost table ($/1M tokens) - Updated 2024/2025 pricing
LLM_COSTS = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1-preview": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},

    # Anthropic Claude
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},

    # Cohere
    "command-r-plus": {"input": 3.00, "output": 15.00},
    "command-r": {"input": 0.50, "output": 1.50},
    "command": {"input": 1.00, "output": 2.00},

    # Google VertexAI
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},

    # Ollama / Local (free but consider infrastructure costs)
    "ollama": {"input": 0.0, "output": 0.0},

    # Default for unknown models
    "default": {"input": 1.00, "output": 2.00}
}


class LLMMonitor:
    """
    Monitor and track LLM usage, costs, and performance
    Based on AI Planet's observability features
    """

    def __init__(self):
        self.metrics: List[LLMMetrics] = []
        self._lock = threading.Lock()
        self._cache = {}
        logger.info("LLM Monitor initialized")

    def record_call(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ):
        """Record a single LLM API call"""

        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        metric = LLMMetrics(
            timestamp=datetime.utcnow(),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
            success=success,
            error=error,
            user_id=user_id,
            workflow_id=workflow_id
        )

        with self._lock:
            self.metrics.append(metric)

        logger.debug(f"Recorded LLM call: {provider}/{model} - {total_tokens} tokens, ${cost:.4f}, {latency_ms:.2f}ms")

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for a single LLM call"""

        # Get pricing for model
        pricing = LLM_COSTS.get(model, LLM_COSTS["default"])

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def get_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> AggregateLLMMetrics:
        """Get aggregated metrics for a time period"""

        # Filter metrics
        filtered = self.metrics

        if start_time:
            filtered = [m for m in filtered if m.timestamp >= start_time]
        if end_time:
            filtered = [m for m in filtered if m.timestamp <= end_time]
        if provider:
            filtered = [m for m in filtered if m.provider == provider]
        if model:
            filtered = [m for m in filtered if m.model == model]
        if user_id:
            filtered = [m for m in filtered if m.user_id == user_id]
        if workflow_id:
            filtered = [m for m in filtered if m.workflow_id == workflow_id]

        if not filtered:
            return AggregateLLMMetrics()

        # Calculate aggregates
        total_calls = len(filtered)
        successful_calls = sum(1 for m in filtered if m.success)
        failed_calls = total_calls - successful_calls

        total_tokens = sum(m.total_tokens for m in filtered)
        total_cost = sum(m.cost_usd for m in filtered)

        latencies = [m.latency_ms for m in filtered]
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        # Calculate time span
        if len(filtered) > 1:
            time_span_seconds = (filtered[-1].timestamp - filtered[0].timestamp).total_seconds()
            calls_per_minute = (total_calls / time_span_seconds) * 60 if time_span_seconds > 0 else 0
            tokens_per_second = total_tokens / time_span_seconds if time_span_seconds > 0 else 0
        else:
            calls_per_minute = 0
            tokens_per_second = 0

        error_rate = failed_calls / total_calls if total_calls > 0 else 0
        cost_per_1k_tokens = (total_cost / total_tokens) * 1000 if total_tokens > 0 else 0

        # Provider breakdown
        provider_counts = defaultdict(int)
        model_counts = defaultdict(int)
        for m in filtered:
            provider_counts[m.provider] += 1
            model_counts[m.model] += 1

        return AggregateLLMMetrics(
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            avg_latency_ms=avg_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            tokens_per_second=tokens_per_second,
            calls_per_minute=calls_per_minute,
            error_rate=error_rate,
            cost_per_1k_tokens=cost_per_1k_tokens,
            provider_breakdown=dict(provider_counts),
            model_breakdown=dict(model_counts)
        )

    def get_cost_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        Analyze usage and provide cost optimization suggestions
        AI Planet feature: 0.5-60x cost savings
        """

        suggestions = []

        # Get recent metrics (last 7 days)
        recent = self.get_metrics(start_time=datetime.utcnow() - timedelta(days=7))

        if recent.total_calls == 0:
            return suggestions

        # Check if using expensive models for simple tasks
        for model, count in recent.model_breakdown.items():
            if model in ["gpt-4", "claude-3-opus-20240229", "gpt-4-turbo"]:
                cheaper_alternatives = {
                    "gpt-4": "gpt-4o-mini (15-40x cheaper, similar quality for most tasks)",
                    "gpt-4-turbo": "gpt-4o (4x cheaper)",
                    "claude-3-opus-20240229": "claude-3-5-haiku (18x cheaper)"
                }

                if model in cheaper_alternatives:
                    suggestions.append({
                        "type": "model_downgrade",
                        "severity": "high",
                        "model": model,
                        "usage_count": count,
                        "suggestion": f"Consider using {cheaper_alternatives[model]}",
                        "potential_savings": "60-90%"
                    })

        # Check for caching opportunities
        if recent.total_tokens > 100000:
            suggestions.append({
                "type": "caching",
                "severity": "medium",
                "suggestion": "Enable prompt caching for repeated queries",
                "potential_savings": "50-80% on cached calls"
            })

        # Check for batch processing opportunities
        if recent.calls_per_minute > 10:
            suggestions.append({
                "type": "batching",
                "severity": "medium",
                "suggestion": "Consider batching similar requests to reduce API calls",
                "potential_savings": "20-40%"
            })

        # Check for Ollama/local model opportunities
        if recent.total_cost_usd > 100 and "ollama" not in recent.provider_breakdown:
            suggestions.append({
                "type": "local_deployment",
                "severity": "high",
                "suggestion": "Consider Ollama/local models for non-critical tasks",
                "potential_savings": "90-100% (infrastructure costs apply)"
            })

        return suggestions

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for observability dashboard"""

        # Last 24 hours
        last_24h = self.get_metrics(start_time=datetime.utcnow() - timedelta(hours=24))

        # Last 7 days
        last_7d = self.get_metrics(start_time=datetime.utcnow() - timedelta(days=7))

        # Last 30 days
        last_30d = self.get_metrics(start_time=datetime.utcnow() - timedelta(days=30))

        return {
            "last_24_hours": last_24h.__dict__,
            "last_7_days": last_7d.__dict__,
            "last_30_days": last_30d.__dict__,
            "cost_optimization": self.get_cost_optimization_suggestions(),
            "total_metrics_recorded": len(self.metrics)
        }

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics for analysis"""

        if format == "json":
            import json
            return json.dumps([
                {
                    "timestamp": m.timestamp.isoformat(),
                    "provider": m.provider,
                    "model": m.model,
                    "tokens": m.total_tokens,
                    "cost": m.cost_usd,
                    "latency_ms": m.latency_ms,
                    "success": m.success
                }
                for m in self.metrics
            ], indent=2)

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(["timestamp", "provider", "model", "tokens", "cost", "latency_ms", "success"])

            for m in self.metrics:
                writer.writerow([
                    m.timestamp.isoformat(),
                    m.provider,
                    m.model,
                    m.total_tokens,
                    m.cost_usd,
                    m.latency_ms,
                    m.success
                ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}")


# Global monitor instance
llm_monitor = LLMMonitor()
