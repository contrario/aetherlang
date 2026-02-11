"""
AetherLang Time-Travel Debugger

Comprehensive debugging system for flow execution:
- State snapshots at each node execution
- Full execution history recording
- Step-by-step replay capability
- State comparison between runs
- Breakpoint support
"""

import time
import json
import copy
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class StateSnapshot:
    """Complete state at a specific point in execution"""
    timestamp: float
    node_name: str
    node_type: str

    # Node state
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    context: Dict[str, Any]

    # Execution info
    status: str  # "pending", "running", "success", "error"
    error: Optional[str] = None
    duration: Optional[float] = None

    # Memory info
    memory_used: Optional[float] = None  # MB

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionStep:
    """Single step in execution history"""
    step_number: int
    timestamp: float
    action: str  # "start_node", "end_node", "error"
    node_name: str
    node_type: str
    snapshot: StateSnapshot

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "step_number": self.step_number,
            "timestamp": self.timestamp,
            "action": self.action,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "snapshot": self.snapshot.to_dict()
        }
        return result


@dataclass
class ExecutionHistory:
    """Complete execution history for time-travel"""
    session_id: str
    flow_name: str
    start_time: float
    end_time: Optional[float]

    steps: List[ExecutionStep] = field(default_factory=list)
    breakpoints: List[str] = field(default_factory=list)

    # Metadata
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "flow_name": self.flow_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "steps": [step.to_dict() for step in self.steps],
            "breakpoints": self.breakpoints,
            "total_nodes": self.total_nodes,
            "completed_nodes": self.completed_nodes,
            "failed_nodes": self.failed_nodes,
            "duration": self.end_time - self.start_time if self.end_time else None
        }


class TimeTravelDebugger:
    """
    Time-travel debugging system for AetherLang flows

    Features:
    - Record complete execution history
    - Capture state snapshots at each node
    - Replay execution step-by-step
    - Compare states between runs
    - Breakpoint support
    """

    def __init__(self):
        self.current_session: Optional[ExecutionHistory] = None
        self.sessions: Dict[str, ExecutionHistory] = {}
        self.step_counter = 0

    def start_session(self, flow_name: str, session_id: Optional[str] = None) -> str:
        """Start a new debugging session"""
        if session_id is None:
            session_id = f"{flow_name}_{int(time.time() * 1000)}"

        self.current_session = ExecutionHistory(
            session_id=session_id,
            flow_name=flow_name,
            start_time=time.time(),
            end_time=None
        )

        self.sessions[session_id] = self.current_session
        self.step_counter = 0

        return session_id

    def end_session(self):
        """End the current debugging session"""
        if self.current_session:
            self.current_session.end_time = time.time()
            self.current_session = None

    def record_node_start(
        self,
        node_name: str,
        node_type: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Record the start of a node execution"""
        if not self.current_session:
            return

        self.step_counter += 1

        snapshot = StateSnapshot(
            timestamp=time.time(),
            node_name=node_name,
            node_type=node_type,
            input_data=copy.deepcopy(input_data),
            output_data=None,
            context=copy.deepcopy(context),
            status="running"
        )

        step = ExecutionStep(
            step_number=self.step_counter,
            timestamp=time.time(),
            action="start_node",
            node_name=node_name,
            node_type=node_type,
            snapshot=snapshot
        )

        self.current_session.steps.append(step)
        self.current_session.total_nodes += 1

    def record_node_end(
        self,
        node_name: str,
        node_type: str,
        output_data: Dict[str, Any],
        context: Dict[str, Any],
        duration: float,
        memory_used: Optional[float] = None
    ):
        """Record the end of a node execution"""
        if not self.current_session:
            return

        self.step_counter += 1

        snapshot = StateSnapshot(
            timestamp=time.time(),
            node_name=node_name,
            node_type=node_type,
            input_data={},  # Already recorded in start
            output_data=copy.deepcopy(output_data),
            context=copy.deepcopy(context),
            status="success",
            duration=duration,
            memory_used=memory_used
        )

        step = ExecutionStep(
            step_number=self.step_counter,
            timestamp=time.time(),
            action="end_node",
            node_name=node_name,
            node_type=node_type,
            snapshot=snapshot
        )

        self.current_session.steps.append(step)
        self.current_session.completed_nodes += 1

    def record_node_error(
        self,
        node_name: str,
        node_type: str,
        error: str,
        context: Dict[str, Any]
    ):
        """Record a node execution error"""
        if not self.current_session:
            return

        self.step_counter += 1

        snapshot = StateSnapshot(
            timestamp=time.time(),
            node_name=node_name,
            node_type=node_type,
            input_data={},
            output_data=None,
            context=copy.deepcopy(context),
            status="error",
            error=error
        )

        step = ExecutionStep(
            step_number=self.step_counter,
            timestamp=time.time(),
            action="error",
            node_name=node_name,
            node_type=node_type,
            snapshot=snapshot
        )

        self.current_session.steps.append(step)
        self.current_session.failed_nodes += 1

    def get_session(self, session_id: str) -> Optional[ExecutionHistory]:
        """Get a specific debugging session"""
        return self.sessions.get(session_id)

    def get_current_session(self) -> Optional[ExecutionHistory]:
        """Get the current debugging session"""
        return self.current_session

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all debugging sessions"""
        return [
            {
                "session_id": session.session_id,
                "flow_name": session.flow_name,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "total_steps": len(session.steps),
                "total_nodes": session.total_nodes,
                "completed_nodes": session.completed_nodes,
                "failed_nodes": session.failed_nodes
            }
            for session in self.sessions.values()
        ]

    def get_step(self, session_id: str, step_number: int) -> Optional[ExecutionStep]:
        """Get a specific step from a session"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        for step in session.steps:
            if step.step_number == step_number:
                return step

        return None

    def get_steps_range(
        self,
        session_id: str,
        start_step: int,
        end_step: int
    ) -> List[ExecutionStep]:
        """Get a range of steps from a session"""
        session = self.sessions.get(session_id)
        if not session:
            return []

        return [
            step for step in session.steps
            if start_step <= step.step_number <= end_step
        ]

    def get_node_history(
        self,
        session_id: str,
        node_name: str
    ) -> List[ExecutionStep]:
        """Get all steps for a specific node"""
        session = self.sessions.get(session_id)
        if not session:
            return []

        return [
            step for step in session.steps
            if step.node_name == node_name
        ]

    def compare_sessions(
        self,
        session_id1: str,
        session_id2: str
    ) -> Dict[str, Any]:
        """Compare two execution sessions"""
        session1 = self.sessions.get(session_id1)
        session2 = self.sessions.get(session_id2)

        if not session1 or not session2:
            return {"error": "One or both sessions not found"}

        # Compare basic metrics
        comparison = {
            "session1": {
                "id": session1.session_id,
                "total_steps": len(session1.steps),
                "completed_nodes": session1.completed_nodes,
                "failed_nodes": session1.failed_nodes,
                "duration": session1.end_time - session1.start_time if session1.end_time else None
            },
            "session2": {
                "id": session2.session_id,
                "total_steps": len(session2.steps),
                "completed_nodes": session2.completed_nodes,
                "failed_nodes": session2.failed_nodes,
                "duration": session2.end_time - session2.start_time if session2.end_time else None
            },
            "differences": []
        }

        # Compare step counts
        if len(session1.steps) != len(session2.steps):
            comparison["differences"].append({
                "type": "step_count",
                "session1_steps": len(session1.steps),
                "session2_steps": len(session2.steps)
            })

        # Compare node completion
        if session1.completed_nodes != session2.completed_nodes:
            comparison["differences"].append({
                "type": "completion",
                "session1_completed": session1.completed_nodes,
                "session2_completed": session2.completed_nodes
            })

        # Compare durations
        if session1.end_time and session2.end_time:
            duration1 = session1.end_time - session1.start_time
            duration2 = session2.end_time - session2.start_time
            if abs(duration1 - duration2) > 0.1:
                comparison["differences"].append({
                    "type": "duration",
                    "session1_duration": duration1,
                    "session2_duration": duration2,
                    "difference": duration2 - duration1
                })

        return comparison

    def add_breakpoint(self, node_name: str):
        """Add a breakpoint at a specific node"""
        if self.current_session:
            if node_name not in self.current_session.breakpoints:
                self.current_session.breakpoints.append(node_name)

    def remove_breakpoint(self, node_name: str):
        """Remove a breakpoint"""
        if self.current_session:
            if node_name in self.current_session.breakpoints:
                self.current_session.breakpoints.remove(node_name)

    def should_break(self, node_name: str) -> bool:
        """Check if execution should break at this node"""
        if not self.current_session:
            return False
        return node_name in self.current_session.breakpoints

    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export a session as JSON"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return session.to_dict()

    def import_session(self, session_data: Dict[str, Any]):
        """Import a session from JSON"""
        session_id = session_data["session_id"]

        # Reconstruct session
        session = ExecutionHistory(
            session_id=session_id,
            flow_name=session_data["flow_name"],
            start_time=session_data["start_time"],
            end_time=session_data.get("end_time"),
            breakpoints=session_data.get("breakpoints", []),
            total_nodes=session_data.get("total_nodes", 0),
            completed_nodes=session_data.get("completed_nodes", 0),
            failed_nodes=session_data.get("failed_nodes", 0)
        )

        # Reconstruct steps
        for step_data in session_data.get("steps", []):
            snapshot_data = step_data["snapshot"]
            snapshot = StateSnapshot(
                timestamp=snapshot_data["timestamp"],
                node_name=snapshot_data["node_name"],
                node_type=snapshot_data["node_type"],
                input_data=snapshot_data["input_data"],
                output_data=snapshot_data.get("output_data"),
                context=snapshot_data["context"],
                status=snapshot_data["status"],
                error=snapshot_data.get("error"),
                duration=snapshot_data.get("duration"),
                memory_used=snapshot_data.get("memory_used")
            )

            step = ExecutionStep(
                step_number=step_data["step_number"],
                timestamp=step_data["timestamp"],
                action=step_data["action"],
                node_name=step_data["node_name"],
                node_type=step_data["node_type"],
                snapshot=snapshot
            )

            session.steps.append(step)

        self.sessions[session_id] = session
        return session_id


# Global debugger instance
_global_debugger = TimeTravelDebugger()


def get_debugger() -> TimeTravelDebugger:
    """Get the global debugger instance"""
    return _global_debugger
