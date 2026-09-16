"""
Trace Service - Observability and monitoring for AI workflows
Tracks execution, costs, performance, and errors
"""

import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import asyncio


class TraceService:
    """
    Workflow execution tracing and observability
    - Execution traces (node-level)
    - Cost tracking (token usage, API calls)
    - Performance metrics (latency, throughput)
    - Error tracking and debugging
    """

    def __init__(self):
        self.traces = {}  # workflow_id -> trace data
        self.metrics = defaultdict(lambda: {
            "total_executions": 0,
            "total_duration_ms": 0,
            "total_cost_usd": 0.0,
            "error_count": 0,
            "success_count": 0
        })

    # ==================== TRACE MANAGEMENT ====================

    def start_trace(self, workflow_id: str, workflow_name: str, nodes: List[Dict]) -> str:
        """Start a new workflow trace"""

        trace_id = f"{workflow_id}_{int(time.time() * 1000)}"

        self.traces[trace_id] = {
            "trace_id": trace_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "nodes": {node['id']: {
                "id": node['id'],
                "type": node['data'].get('nodeType', 'unknown'),
                "label": node['data'].get('label', 'Unknown'),
                "status": "pending",
                "start_time": None,
                "end_time": None,
                "duration_ms": 0,
                "input_data": None,
                "output_data": None,
                "error": None,
                "metadata": {}
            } for node in nodes},
            "edges": [],
            "total_duration_ms": 0,
            "total_cost_usd": 0.0,
            "node_count": len(nodes),
            "errors": []
        }

        return trace_id

    def start_node(
        self,
        trace_id: str,
        node_id: str,
        input_data: Any = None
    ) -> None:
        """Mark node execution start"""

        if trace_id not in self.traces:
            return

        node_trace = self.traces[trace_id]["nodes"].get(node_id)
        if node_trace:
            node_trace["status"] = "running"
            node_trace["start_time"] = datetime.now().isoformat()
            node_trace["input_data"] = self._sanitize_data(input_data)

    def end_node(
        self,
        trace_id: str,
        node_id: str,
        output_data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Mark node execution end"""

        if trace_id not in self.traces:
            return

        node_trace = self.traces[trace_id]["nodes"].get(node_id)
        if node_trace:
            end_time = datetime.now()
            node_trace["end_time"] = end_time.isoformat()

            # Calculate duration
            if node_trace["start_time"]:
                start = datetime.fromisoformat(node_trace["start_time"])
                duration_ms = (end_time - start).total_seconds() * 1000
                node_trace["duration_ms"] = round(duration_ms, 2)

            # Set status
            if error:
                node_trace["status"] = "failed"
                node_trace["error"] = str(error)
                self.traces[trace_id]["errors"].append({
                    "node_id": node_id,
                    "node_label": node_trace["label"],
                    "error": str(error),
                    "timestamp": end_time.isoformat()
                })
            else:
                node_trace["status"] = "success"
                node_trace["output_data"] = self._sanitize_data(output_data)

            # Add metadata (token usage, costs, etc.)
            if metadata:
                node_trace["metadata"] = metadata

                # Track costs
                if "cost_usd" in metadata:
                    self.traces[trace_id]["total_cost_usd"] += metadata["cost_usd"]

    def end_trace(self, trace_id: str, status: str = "completed") -> Dict[str, Any]:
        """Complete workflow trace"""

        if trace_id not in self.traces:
            return {"success": False, "error": "Trace not found"}

        trace = self.traces[trace_id]
        trace["end_time"] = datetime.now().isoformat()
        trace["status"] = status

        # Calculate total duration
        if trace["start_time"]:
            start = datetime.fromisoformat(trace["start_time"])
            end = datetime.fromisoformat(trace["end_time"])
            trace["total_duration_ms"] = round((end - start).total_seconds() * 1000, 2)

        # Update metrics
        workflow_id = trace["workflow_id"]
        self.metrics[workflow_id]["total_executions"] += 1
        self.metrics[workflow_id]["total_duration_ms"] += trace["total_duration_ms"]
        self.metrics[workflow_id]["total_cost_usd"] += trace["total_cost_usd"]

        if status == "completed":
            self.metrics[workflow_id]["success_count"] += 1
        else:
            self.metrics[workflow_id]["error_count"] += 1

        return {"success": True, "trace": trace}

    # ==================== COST TRACKING ====================

    def track_llm_call(
        self,
        trace_id: str,
        node_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0
    ) -> Dict[str, Any]:
        """Track LLM API call costs"""

        cost_input = (input_tokens / 1000.0) * cost_per_1k_input
        cost_output = (output_tokens / 1000.0) * cost_per_1k_output
        total_cost = cost_input + cost_output

        metadata = {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": round(total_cost, 6),
            "cost_breakdown": {
                "input_cost": round(cost_input, 6),
                "output_cost": round(cost_output, 6)
            }
        }

        # Update node metadata
        if trace_id in self.traces:
            node_trace = self.traces[trace_id]["nodes"].get(node_id)
            if node_trace:
                node_trace["metadata"].update(metadata)
                self.traces[trace_id]["total_cost_usd"] += total_cost

        return metadata

    # ==================== QUERY TRACES ====================

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get single trace"""
        return self.traces.get(trace_id)

    def get_workflow_traces(
        self,
        workflow_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent traces for a workflow"""

        workflow_traces = [
            trace for trace in self.traces.values()
            if trace["workflow_id"] == workflow_id
        ]

        # Sort by start time (most recent first)
        workflow_traces.sort(
            key=lambda x: x["start_time"],
            reverse=True
        )

        return workflow_traces[:limit]

    def get_metrics(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated metrics"""

        if workflow_id:
            return self.metrics.get(workflow_id, {})
        else:
            return dict(self.metrics)

    # ==================== ANALYTICS ====================

    def get_node_performance(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Analyze node performance across all executions"""

        node_stats = defaultdict(lambda: {
            "executions": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0,
            "failures": 0,
            "success_rate": 0.0
        })

        # Aggregate stats from all traces
        for trace in self.traces.values():
            if trace["workflow_id"] != workflow_id:
                continue

            for node_id, node_trace in trace["nodes"].items():
                if node_trace["status"] in ["success", "failed"]:
                    stats = node_stats[node_id]
                    stats["executions"] += 1
                    stats["total_duration_ms"] += node_trace["duration_ms"]

                    if node_trace["status"] == "failed":
                        stats["failures"] += 1

        # Calculate averages
        for node_id, stats in node_stats.items():
            if stats["executions"] > 0:
                stats["avg_duration_ms"] = round(
                    stats["total_duration_ms"] / stats["executions"],
                    2
                )
                stats["success_rate"] = round(
                    (stats["executions"] - stats["failures"]) / stats["executions"] * 100,
                    2
                )

        # Convert to list and sort by duration
        performance_list = [
            {"node_id": k, **v}
            for k, v in node_stats.items()
        ]
        performance_list.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

        return performance_list

    def get_cost_breakdown(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cost breakdown by node type"""

        cost_by_type = defaultdict(float)
        total_cost = 0.0

        for trace in self.traces.values():
            if workflow_id and trace["workflow_id"] != workflow_id:
                continue

            for node_trace in trace["nodes"].values():
                node_type = node_trace["type"]
                node_cost = node_trace["metadata"].get("cost_usd", 0.0)

                cost_by_type[node_type] += node_cost
                total_cost += node_cost

        return {
            "total_cost_usd": round(total_cost, 4),
            "by_node_type": {
                k: round(v, 4)
                for k, v in sorted(
                    cost_by_type.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            }
        }

    # ==================== UTILITIES ====================

    def _sanitize_data(self, data: Any, max_length: int = 1000) -> Any:
        """Sanitize data for storage (prevent huge traces)"""

        if data is None:
            return None

        try:
            # Convert to JSON string
            json_str = json.dumps(data, default=str)

            # Truncate if too long
            if len(json_str) > max_length:
                return f"{json_str[:max_length]}... [truncated]"

            return json.loads(json_str)

        except:
            return str(data)[:max_length]

    def clear_old_traces(self, keep_last_n: int = 100) -> int:
        """Clear old traces to prevent memory bloat"""

        if len(self.traces) <= keep_last_n:
            return 0

        # Sort by start time
        sorted_traces = sorted(
            self.traces.items(),
            key=lambda x: x[1]["start_time"],
            reverse=True
        )

        # Keep only last N
        to_keep = dict(sorted_traces[:keep_last_n])
        removed_count = len(self.traces) - len(to_keep)

        self.traces = to_keep

        return removed_count

    def export_trace(self, trace_id: str) -> Optional[str]:
        """Export trace as JSON"""

        trace = self.get_trace(trace_id)
        if not trace:
            return None

        return json.dumps(trace, indent=2, default=str)


# Global instance
trace_service = TraceService()
