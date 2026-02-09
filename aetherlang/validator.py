"""
AetherLang Validator - Semantic validation για flows
"""
from typing import List, Dict, Any
from .parser import Flow, Node, NodeType


class ValidationError:
    """Αναπαράσταση validation error"""

    def __init__(self, severity: str, message: str, node: str = None):
        self.severity = severity  # ERROR, WARNING, INFO
        self.message = message
        self.node = node

    def __repr__(self):
        prefix = "❌" if self.severity == "ERROR" else "⚠️" if self.severity == "WARNING" else "ℹ️"
        node_info = f" [{self.node}]" if self.node else ""
        return f"{prefix} {self.message}{node_info}"


class AetherValidator:
    """
    Semantic Validator για AetherLang flows
    Ελέγχει:
    - Flow consistency
    - Node connections
    - Parameter validity
    - Execution feasibility
    """

    def __init__(self):
        self.errors: List[ValidationError] = []

    def validate(self, flow: Flow) -> bool:
        """Validate a flow and return True if valid"""
        self.errors = []

        # Check flow has nodes
        if not flow.nodes:
            self.errors.append(ValidationError("ERROR", "Το flow δεν έχει nodes"))
            return False

        # Check flow has outputs
        if not flow.outputs:
            self.errors.append(ValidationError("WARNING", "Το flow δεν έχει ορισμένα outputs"))

        # Validate nodes
        self._validate_nodes(flow)

        # Validate edges
        self._validate_edges(flow)

        # Validate execution order (no cycles)
        self._validate_execution_order(flow)

        # Validate inputs/outputs
        self._validate_inputs_outputs(flow)

        # Check for isolated nodes
        self._check_isolated_nodes(flow)

        return not self.has_errors()

    def _validate_nodes(self, flow: Flow):
        """Validate individual nodes"""
        for alias, node in flow.nodes.items():
            # Check LLM nodes have model specified
            if node.node_type == NodeType.LLM:
                if "model" not in node.params:
                    self.errors.append(ValidationError(
                        "WARNING",
                        "Το LLM node δεν έχει καθορισμένο model, θα χρησιμοποιηθεί το προεπιλεγμένο",
                        alias
                    ))

            # Check GUARD nodes have mode
            if node.node_type == NodeType.GUARD:
                if "mode" not in node.params:
                    self.errors.append(ValidationError(
                        "INFO",
                        "Το GUARD node θα χρησιμοποιήσει NORMAL mode",
                        alias
                    ))

            # Check RAG nodes have topk
            if node.node_type == NodeType.RAG:
                topk = node.params.get("topk", 3)
                if not isinstance(topk, int) or topk < 1:
                    self.errors.append(ValidationError(
                        "ERROR",
                        f"Το RAG node έχει μη έγκυρο topk: {topk}",
                        alias
                    ))

    def _validate_edges(self, flow: Flow):
        """Validate edges"""
        for edge in flow.edges:
            # Check source exists
            if edge.source not in flow.nodes:
                self.errors.append(ValidationError(
                    "ERROR",
                    f"Το source node '{edge.source}' δεν υπάρχει"
                ))

            # Check target exists
            if edge.target not in flow.nodes:
                self.errors.append(ValidationError(
                    "ERROR",
                    f"Το target node '{edge.target}' δεν υπάρχει"
                ))

    def _validate_execution_order(self, flow: Flow):
        """Check for cycles in the flow"""
        visited = set()
        rec_stack = set()

        def has_cycle(node_alias: str) -> bool:
            visited.add(node_alias)
            rec_stack.add(node_alias)

            # Get neighbors
            neighbors = [edge.target for edge in flow.edges if edge.source == node_alias]

            for neighbor in neighbors:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_alias)
            return False

        for node_alias in flow.nodes.keys():
            if node_alias not in visited:
                if has_cycle(node_alias):
                    self.errors.append(ValidationError(
                        "ERROR",
                        "Εντοπίστηκε κυκλική εξάρτηση στο flow"
                    ))
                    return

    def _validate_inputs_outputs(self, flow: Flow):
        """Validate inputs and outputs"""
        # Check that output sources exist
        for output_name, source_node in flow.outputs.items():
            if source_node not in flow.nodes:
                self.errors.append(ValidationError(
                    "ERROR",
                    f"Το output '{output_name}' αναφέρεται σε ανύπαρκτο node '{source_node}'"
                ))

    def _check_isolated_nodes(self, flow: Flow):
        """Check for nodes with no connections"""
        connected_nodes = set()

        for edge in flow.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)

        # Add output nodes as connected
        for source_node in flow.outputs.values():
            connected_nodes.add(source_node)

        for node_alias in flow.nodes.keys():
            if node_alias not in connected_nodes:
                self.errors.append(ValidationError(
                    "WARNING",
                    f"Το node '{node_alias}' δεν συνδέεται με κανένα άλλο node",
                    node_alias
                ))

    def has_errors(self) -> bool:
        """Check if there are errors (not warnings)"""
        return any(e.severity == "ERROR" for e in self.errors)

    def get_errors(self) -> List[ValidationError]:
        """Get all validation errors"""
        return self.errors

    def get_report(self) -> str:
        """Get validation report"""
        if not self.errors:
            return "✅ Το flow είναι έγκυρο"

        report = []
        errors = [e for e in self.errors if e.severity == "ERROR"]
        warnings = [e for e in self.errors if e.severity == "WARNING"]
        infos = [e for e in self.errors if e.severity == "INFO"]

        if errors:
            report.append(f"\n❌ Σφάλματα ({len(errors)}):")
            for e in errors:
                report.append(f"  {e}")

        if warnings:
            report.append(f"\n⚠️ Προειδοποιήσεις ({len(warnings)}):")
            for e in warnings:
                report.append(f"  {e}")

        if infos:
            report.append(f"\nℹ️ Πληροφορίες ({len(infos)}):")
            for e in infos:
                report.append(f"  {e}")

        return "\n".join(report)
