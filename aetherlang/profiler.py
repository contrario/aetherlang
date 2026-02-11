"""
AetherLang Performance Profiler

Real-time execution profiling with node-by-node timing, memory tracking,
cost calculation, and comprehensive metrics collection.
"""

import time
import psutil
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class NodeMetrics:
    """Performance metrics for a single node execution"""
    node_name: str
    node_type: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float  # MB
    memory_after: float   # MB
    memory_delta: float   # MB
    cost: float = 0.0
    tokens_used: int = 0
    api_calls: int = 0
    status: str = "success"  # success, error, skipped
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_name": self.node_name,
            "node_type": self.node_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "memory_before": self.memory_before,
            "memory_after": self.memory_after,
            "memory_delta": self.memory_delta,
            "cost": self.cost,
            "tokens_used": self.tokens_used,
            "api_calls": self.api_calls,
            "status": self.status,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class ExecutionProfile:
    """Complete execution profile for a flow"""
    flow_name: str
    start_time: float
    end_time: float
    total_duration: float
    total_cost: float
    total_memory_used: float
    total_tokens: int
    total_api_calls: int
    node_metrics: List[NodeMetrics]
    peak_memory: float
    avg_node_duration: float
    slowest_node: Optional[str] = None
    most_expensive_node: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_name": self.flow_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.total_duration,
            "total_cost": self.total_cost,
            "total_memory_used": self.total_memory_used,
            "total_tokens": self.total_tokens,
            "total_api_calls": self.total_api_calls,
            "node_metrics": [m.to_dict() for m in self.node_metrics],
            "peak_memory": self.peak_memory,
            "avg_node_duration": self.avg_node_duration,
            "slowest_node": self.slowest_node,
            "most_expensive_node": self.most_expensive_node,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat()
        }


class PerformanceProfiler:
    """
    Profiles flow execution with detailed metrics

    Usage:
        profiler = PerformanceProfiler()
        profiler.start_execution("MyFlow")

        profiler.start_node("Guard", "guard")
        # ... execute node ...
        profiler.end_node("Guard", cost=0.0001, tokens=50)

        profile = profiler.end_execution()
    """

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.flow_name: Optional[str] = None
        self.execution_start: Optional[float] = None
        self.execution_end: Optional[float] = None
        self.node_metrics: List[NodeMetrics] = []
        self.current_node: Optional[Dict[str, Any]] = None

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def start_execution(self, flow_name: str):
        """Start profiling a flow execution"""
        self.flow_name = flow_name
        self.execution_start = time.time()
        self.node_metrics = []
        self.current_node = None

    def start_node(self, node_name: str, node_type: str):
        """Start profiling a node"""
        if self.current_node:
            # Previous node wasn't ended - auto-end it with error
            self.end_node(
                self.current_node["name"],
                status="error",
                error_message="Node execution interrupted"
            )

        self.current_node = {
            "name": node_name,
            "type": node_type,
            "start_time": time.time(),
            "memory_before": self._get_memory_usage()
        }

    def end_node(
        self,
        node_name: str,
        cost: float = 0.0,
        tokens: int = 0,
        api_calls: int = 0,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """End profiling a node"""
        if not self.current_node or self.current_node["name"] != node_name:
            # Mismatched node - create a placeholder metric
            return

        end_time = time.time()
        memory_after = self._get_memory_usage()

        metric = NodeMetrics(
            node_name=node_name,
            node_type=self.current_node["type"],
            start_time=self.current_node["start_time"],
            end_time=end_time,
            duration=end_time - self.current_node["start_time"],
            memory_before=self.current_node["memory_before"],
            memory_after=memory_after,
            memory_delta=memory_after - self.current_node["memory_before"],
            cost=cost,
            tokens_used=tokens,
            api_calls=api_calls,
            status=status,
            error_message=error_message,
            metadata=metadata or {}
        )

        self.node_metrics.append(metric)
        self.current_node = None

    def end_execution(self) -> ExecutionProfile:
        """End profiling and return complete profile"""
        self.execution_end = time.time()

        if not self.execution_start or not self.flow_name:
            raise ValueError("Execution not started")

        # Close any open node
        if self.current_node:
            self.end_node(
                self.current_node["name"],
                status="incomplete",
                error_message="Execution ended before node completion"
            )

        # Calculate aggregates
        total_duration = self.execution_end - self.execution_start
        total_cost = sum(m.cost for m in self.node_metrics)
        total_memory = sum(m.memory_delta for m in self.node_metrics)
        total_tokens = sum(m.tokens_used for m in self.node_metrics)
        total_api_calls = sum(m.api_calls for m in self.node_metrics)

        peak_memory = max(
            (m.memory_after for m in self.node_metrics),
            default=0.0
        )

        avg_duration = (
            sum(m.duration for m in self.node_metrics) / len(self.node_metrics)
            if self.node_metrics else 0.0
        )

        # Find slowest and most expensive nodes
        slowest = max(
            self.node_metrics,
            key=lambda m: m.duration,
            default=None
        )
        most_expensive = max(
            self.node_metrics,
            key=lambda m: m.cost,
            default=None
        )

        return ExecutionProfile(
            flow_name=self.flow_name,
            start_time=self.execution_start,
            end_time=self.execution_end,
            total_duration=total_duration,
            total_cost=total_cost,
            total_memory_used=total_memory,
            total_tokens=total_tokens,
            total_api_calls=total_api_calls,
            node_metrics=self.node_metrics,
            peak_memory=peak_memory,
            avg_node_duration=avg_duration,
            slowest_node=slowest.node_name if slowest else None,
            most_expensive_node=most_expensive.node_name if most_expensive else None
        )


class ProfileComparator:
    """Compare multiple execution profiles"""

    @staticmethod
    def compare_profiles(
        profile1: ExecutionProfile,
        profile2: ExecutionProfile
    ) -> Dict[str, Any]:
        """
        Compare two profiles and return differences

        Useful for A/B testing optimizations
        """
        return {
            "duration_diff": profile2.total_duration - profile1.total_duration,
            "duration_change_pct": (
                (profile2.total_duration - profile1.total_duration) / profile1.total_duration * 100
                if profile1.total_duration > 0 else 0
            ),
            "cost_diff": profile2.total_cost - profile1.total_cost,
            "cost_change_pct": (
                (profile2.total_cost - profile1.total_cost) / profile1.total_cost * 100
                if profile1.total_cost > 0 else 0
            ),
            "memory_diff": profile2.total_memory_used - profile1.total_memory_used,
            "tokens_diff": profile2.total_tokens - profile1.total_tokens,
            "improved": (
                profile2.total_duration < profile1.total_duration and
                profile2.total_cost < profile1.total_cost
            )
        }

    @staticmethod
    def aggregate_profiles(profiles: List[ExecutionProfile]) -> Dict[str, Any]:
        """
        Aggregate statistics from multiple profiles

        Useful for understanding typical performance
        """
        if not profiles:
            return {}

        return {
            "count": len(profiles),
            "avg_duration": sum(p.total_duration for p in profiles) / len(profiles),
            "min_duration": min(p.total_duration for p in profiles),
            "max_duration": max(p.total_duration for p in profiles),
            "avg_cost": sum(p.total_cost for p in profiles) / len(profiles),
            "total_cost": sum(p.total_cost for p in profiles),
            "avg_memory": sum(p.total_memory_used for p in profiles) / len(profiles),
            "peak_memory": max(p.peak_memory for p in profiles),
        }
