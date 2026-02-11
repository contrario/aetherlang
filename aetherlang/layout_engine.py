"""
AetherLang Layout Engine

Intelligent layout algorithms for flow visualization:
- Hierarchical (top-to-bottom)
- Circular (nodes in circle)
- Grid (aligned grid)
- Tree (branching structure)
- Force-Directed (physics-based)
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from .parser import Flow, Node


@dataclass
class NodePosition:
    """Position of a node in 2D space"""
    node_id: str
    x: float
    y: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "x": self.x,
            "y": self.y
        }


class LayoutEngine:
    """
    Intelligent layout engine for flow visualization

    Supports multiple layout algorithms optimized for different flow types
    """

    def __init__(self):
        self.node_width = 180
        self.node_height = 80
        self.horizontal_spacing = 200
        self.vertical_spacing = 120
        self.canvas_width = 1200
        self.canvas_height = 800

    def calculate_layout(
        self,
        flow: Flow,
        layout_type: str = "hierarchical"
    ) -> Dict[str, NodePosition]:
        """
        Calculate node positions based on layout type

        Args:
            flow: The flow to layout
            layout_type: Type of layout algorithm

        Returns:
            Dictionary mapping node_id to NodePosition
        """
        if layout_type == "hierarchical":
            return self.hierarchical_layout(flow)
        elif layout_type == "circular":
            return self.circular_layout(flow)
        elif layout_type == "grid":
            return self.grid_layout(flow)
        elif layout_type == "tree":
            return self.tree_layout(flow)
        elif layout_type == "force":
            return self.force_directed_layout(flow)
        else:
            # Default to hierarchical
            return self.hierarchical_layout(flow)

    def hierarchical_layout(self, flow: Flow) -> Dict[str, NodePosition]:
        """
        Hierarchical layout (top-to-bottom)

        Organizes nodes in layers based on their distance from input
        Good for: Sequential workflows, pipelines
        """
        # Build adjacency list
        graph = {node_id: [] for node_id in flow.nodes.keys()}
        for edge in flow.edges:
            graph[edge.source].append(edge.target)

        # Calculate layers using BFS
        layers = self._calculate_layers(flow, graph)

        # Position nodes
        positions = {}

        for layer_idx, layer_nodes in enumerate(layers):
            layer_width = len(layer_nodes) * self.horizontal_spacing
            start_x = (self.canvas_width - layer_width) / 2
            y = 100 + layer_idx * self.vertical_spacing

            for node_idx, node_id in enumerate(layer_nodes):
                x = start_x + node_idx * self.horizontal_spacing + self.horizontal_spacing / 2
                positions[node_id] = NodePosition(node_id, x, y)

        return positions

    def circular_layout(self, flow: Flow) -> Dict[str, NodePosition]:
        """
        Circular layout

        Arranges nodes in a circle
        Good for: Cyclic workflows, hub-and-spoke patterns
        """
        nodes = list(flow.nodes.keys())
        n = len(nodes)

        if n == 0:
            return {}

        # Calculate circle parameters
        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2
        radius = min(center_x, center_y) * 0.7

        positions = {}

        for i, node_id in enumerate(nodes):
            angle = 2 * math.pi * i / n - math.pi / 2  # Start from top
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[node_id] = NodePosition(node_id, x, y)

        return positions

    def grid_layout(self, flow: Flow) -> Dict[str, NodePosition]:
        """
        Grid layout

        Arranges nodes in a grid pattern
        Good for: Large flows, uniform display
        """
        nodes = list(flow.nodes.keys())
        n = len(nodes)

        if n == 0:
            return {}

        # Calculate grid dimensions (aim for roughly square)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        # Calculate spacing
        available_width = self.canvas_width - 100
        available_height = self.canvas_height - 100

        col_spacing = available_width / (cols + 1)
        row_spacing = available_height / (rows + 1)

        positions = {}

        for i, node_id in enumerate(nodes):
            row = i // cols
            col = i % cols

            x = 50 + (col + 1) * col_spacing
            y = 50 + (row + 1) * row_spacing

            positions[node_id] = NodePosition(node_id, x, y)

        return positions

    def tree_layout(self, flow: Flow) -> Dict[str, NodePosition]:
        """
        Tree layout

        Hierarchical tree structure for branching flows
        Good for: Decision trees, branching pipelines
        """
        # Build adjacency list
        graph = {node_id: [] for node_id in flow.nodes.keys()}
        in_degree = {node_id: 0 for node_id in flow.nodes.keys()}

        for edge in flow.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Find root (node with no incoming edges)
        roots = [node_id for node_id, degree in in_degree.items() if degree == 0]

        if not roots:
            # No clear root, use first node
            roots = [list(flow.nodes.keys())[0]]

        root = roots[0]

        # Calculate tree structure
        tree = self._build_tree(root, graph)

        # Position nodes
        positions = {}
        self._position_tree(tree, positions, self.canvas_width / 2, 100, self.canvas_width * 0.8)

        return positions

    def force_directed_layout(self, flow: Flow) -> Dict[str, NodePosition]:
        """
        Force-directed layout (physics simulation)

        Simulates physical forces between nodes
        Good for: Complex graphs, organic layouts

        Note: This is a simplified version. Full implementation
        would be done in the frontend with real-time animation.
        """
        nodes = list(flow.nodes.keys())
        n = len(nodes)

        if n == 0:
            return {}

        # Initialize with circular layout as starting point
        positions = self.circular_layout(flow)

        # Simple force-directed adjustment (few iterations)
        for iteration in range(50):
            forces = {node_id: [0.0, 0.0] for node_id in nodes}

            # Repulsion between all nodes
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i >= j:
                        continue

                    pos1 = positions[node1]
                    pos2 = positions[node2]

                    dx = pos2.x - pos1.x
                    dy = pos2.y - pos1.y
                    distance = math.sqrt(dx*dx + dy*dy) or 1

                    # Repulsion force (inverse square)
                    force = 5000 / (distance * distance)
                    fx = force * dx / distance
                    fy = force * dy / distance

                    forces[node1][0] -= fx
                    forces[node1][1] -= fy
                    forces[node2][0] += fx
                    forces[node2][1] += fy

            # Attraction along edges
            for edge in flow.edges:
                pos1 = positions[edge.source]
                pos2 = positions[edge.target]

                dx = pos2.x - pos1.x
                dy = pos2.y - pos1.y
                distance = math.sqrt(dx*dx + dy*dy) or 1

                # Spring force
                force = distance * 0.01
                fx = force * dx / distance
                fy = force * dy / distance

                forces[edge.source][0] += fx
                forces[edge.source][1] += fy
                forces[edge.target][0] -= fx
                forces[edge.target][1] -= fy

            # Apply forces
            for node_id in nodes:
                pos = positions[node_id]
                pos.x += forces[node_id][0] * 0.1
                pos.y += forces[node_id][1] * 0.1

                # Keep within bounds
                pos.x = max(100, min(self.canvas_width - 100, pos.x))
                pos.y = max(100, min(self.canvas_height - 100, pos.y))

        return positions

    def _calculate_layers(self, flow: Flow, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Calculate node layers using BFS"""
        # Find nodes with no incoming edges (start nodes)
        has_incoming = set()
        for targets in graph.values():
            has_incoming.update(targets)

        start_nodes = [node_id for node_id in flow.nodes.keys() if node_id not in has_incoming]

        if not start_nodes:
            # Circular graph, use first node
            start_nodes = [list(flow.nodes.keys())[0]]

        # BFS to calculate layers
        visited = set()
        layers = []
        current_layer = start_nodes

        while current_layer:
            layers.append(current_layer[:])
            visited.update(current_layer)

            next_layer = []
            for node_id in current_layer:
                for target in graph[node_id]:
                    if target not in visited and target not in next_layer:
                        next_layer.append(target)

            current_layer = next_layer

        # Add any orphaned nodes
        all_nodes = set(flow.nodes.keys())
        orphans = list(all_nodes - visited)
        if orphans:
            layers.append(orphans)

        return layers

    def _build_tree(self, root: str, graph: Dict[str, List[str]], visited: Optional[set] = None) -> Dict[str, Any]:
        """Build tree structure from graph"""
        if visited is None:
            visited = set()

        if root in visited:
            return {"node": root, "children": []}

        visited.add(root)

        children = []
        for child in graph[root]:
            if child not in visited:
                children.append(self._build_tree(child, graph, visited))

        return {
            "node": root,
            "children": children
        }

    def _position_tree(
        self,
        tree: Dict[str, Any],
        positions: Dict[str, NodePosition],
        x: float,
        y: float,
        width: float
    ):
        """Position nodes in tree layout"""
        node_id = tree["node"]
        positions[node_id] = NodePosition(node_id, x, y)

        children = tree["children"]
        if not children:
            return

        # Distribute children horizontally
        child_width = width / len(children)
        start_x = x - width / 2 + child_width / 2
        child_y = y + self.vertical_spacing

        for i, child_tree in enumerate(children):
            child_x = start_x + i * child_width
            self._position_tree(child_tree, positions, child_x, child_y, child_width * 0.8)


def detect_optimal_layout(flow: Flow) -> str:
    """
    Auto-detect the best layout type for a given flow

    Based on flow structure characteristics:
    - Linear flows → hierarchical
    - Branching flows → tree
    - Cyclic flows → circular
    - Complex flows → force-directed
    """
    nodes = list(flow.nodes.keys())
    n = len(nodes)

    if n <= 3:
        return "hierarchical"

    # Build graph
    graph = {node_id: [] for node_id in nodes}
    in_degree = {node_id: 0 for node_id in nodes}

    for edge in flow.edges:
        graph[edge.source].append(edge.target)
        in_degree[edge.target] += 1

    # Check for cycles
    has_cycle = any(in_degree[node] > 1 for node in nodes)

    # Check for branching (nodes with multiple outgoing edges)
    max_out_degree = max(len(targets) for targets in graph.values())

    # Calculate average connectivity
    avg_degree = sum(len(targets) for targets in graph.values()) / n

    # Decision logic
    if has_cycle:
        return "circular"
    elif max_out_degree >= 3:
        return "tree"
    elif avg_degree < 1.5:
        return "hierarchical"
    else:
        return "force"
