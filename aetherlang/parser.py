"""
AetherLang Parser - Βελτιωμένος Parser με AST Support
"""
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Τύποι nodes που υποστηρίζονται"""
    # Original node types
    GUARD = "guard"
    PLAN = "plan"
    RAG = "rag"
    LLM = "llm"
    TRANSFORM = "transform"
    FILTER = "filter"
    MERGE = "merge"
    ANALYZE = "analyze"
    EXTRACT = "extract"
    SUMMARIZE = "summarize"

    # Advanced control flow
    CONDITIONAL = "conditional"  # If/else logic
    LOOP = "loop"  # Iterate over data
    PARALLEL = "parallel"  # Execute multiple paths simultaneously
    SWITCH = "switch"  # Multi-way branching

    # Data operations
    MAP = "map"  # Transform arrays/lists
    REDUCE = "reduce"  # Aggregate data
    SPLIT = "split"  # Split data into multiple streams
    JOIN = "join"  # Join multiple data sources

    # Performance & reliability
    CACHE = "cache"  # Cache results
    RETRY = "retry"  # Retry on failure
    TIMEOUT = "timeout"  # Add execution timeout
    FALLBACK = "fallback"  # Fallback on error

    # External integrations
    WEBHOOK = "webhook"  # Call external APIs
    HTTP = "http"  # HTTP requests

    # Advanced processing
    VALIDATE = "validate"  # Data validation
    ENRICH = "enrich"  # Enrich data with external sources
    SLEEP = "sleep"  # Add delays
    RATE_LIMIT = "rate_limit"  # Rate limiting


@dataclass
class Node:
    """Αναπαράσταση ενός node"""
    alias: str
    node_type: NodeType
    params: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"Node({self.alias}:{self.node_type.value}, params={self.params})"


@dataclass
class Edge:
    """Αναπαράσταση μιας ακμής (edge) μεταξύ nodes"""
    source: str
    target: str

    def __repr__(self):
        return f"Edge({self.source} -> {self.target})"


@dataclass
class Flow:
    """Αναπαράσταση ενός πλήρους flow"""
    name: str
    target: str = "neuroaether"
    version: str = ">=0.2"
    inputs: Dict[str, str] = field(default_factory=dict)  # {name: dtype}
    outputs: Dict[str, str] = field(default_factory=dict)  # {name: source_node}
    nodes: Dict[str, Node] = field(default_factory=dict)  # {alias: Node}
    edges: List[Edge] = field(default_factory=list)

    def __repr__(self):
        return f"Flow({self.name}, nodes={len(self.nodes)}, edges={len(self.edges)})"


class AetherParser:
    """
    Βελτιωμένος Parser για AetherLang με υποστήριξη:
    - Ελληνικά και Αγγλικά keywords
    - Πλούσιος τύπος nodes
    - Σύνθετα parameters
    - Error handling με Greek messages
    """

    # Regex patterns
    FLOW_RE = re.compile(r'flow\s+(?P<name>\w+)\s*\{(?P<body>.*)\}', re.DOTALL)
    USING_RE = re.compile(r'using\s+target\s+"(?P<target>[^"]+)"\s+version\s+"(?P<ver>[^"]+)"\s*;')
    INPUT_RE = re.compile(r'input\s+(?P<dtype>\w+)\s+(?P<name>\w+)\s*;')
    OUTPUT_RE = re.compile(r'output\s+(?P<dtype>\w+)\s+(?P<name>\w+)\s+from\s+(?P<src>\w+)\s*;')
    NODE_RE = re.compile(r'node\s+(?P<alias>\w+)\s*:\s*(?P<type>\w+)(?:\s+(?P<params>[^;]+))?\s*;')
    EDGE_RE = re.compile(r'(?P<src>\w+)\s*->\s*(?P<dst>\w+)\s*;')
    COMMENT_RE = re.compile(r'//.*?$|/\*.*?\*/', re.MULTILINE | re.DOTALL)

    def __init__(self):
        self.errors: List[str] = []

    def parse(self, source: str) -> Optional[Flow]:
        """Parse AetherLang source code"""
        self.errors = []

        # Remove comments
        source = self._remove_comments(source)

        # Parse flow
        flow_match = self.FLOW_RE.search(source)
        if not flow_match:
            self.errors.append("❌ Δεν βρέθηκε ορισμός flow")
            return None

        flow_name = flow_match.group('name')
        flow_body = flow_match.group('body')

        flow = Flow(name=flow_name)

        # Parse using directive
        using_match = self.USING_RE.search(flow_body)
        if using_match:
            flow.target = using_match.group('target')
            flow.version = using_match.group('ver')

        # Parse inputs
        for match in self.INPUT_RE.finditer(flow_body):
            dtype = match.group('dtype')
            name = match.group('name')
            flow.inputs[name] = dtype

        # Parse nodes
        for match in self.NODE_RE.finditer(flow_body):
            alias = match.group('alias')
            node_type_str = match.group('type').lower()
            params_str = match.group('params') or ""

            try:
                node_type = NodeType(node_type_str)
            except ValueError:
                self.errors.append(f"⚠️ Άγνωστος τύπος node: {node_type_str}")
                continue

            params = self._parse_params(params_str)
            node = Node(alias=alias, node_type=node_type, params=params)
            flow.nodes[alias] = node

        # Parse edges
        for match in self.EDGE_RE.finditer(flow_body):
            src = match.group('src')
            dst = match.group('dst')

            if src not in flow.nodes:
                self.errors.append(f"⚠️ Το node '{src}' δεν έχει οριστεί")
                continue
            if dst not in flow.nodes:
                self.errors.append(f"⚠️ Το node '{dst}' δεν έχει οριστεί")
                continue

            edge = Edge(source=src, target=dst)
            flow.edges.append(edge)

        # Parse outputs
        for match in self.OUTPUT_RE.finditer(flow_body):
            dtype = match.group('dtype')
            name = match.group('name')
            src = match.group('src')

            if src not in flow.nodes:
                self.errors.append(f"⚠️ Το output node '{src}' δεν έχει οριστεί")
                continue

            flow.outputs[name] = src

        return flow

    def _remove_comments(self, source: str) -> str:
        """Remove comments from source"""
        return self.COMMENT_RE.sub('', source)

    def _parse_params(self, params_str: str) -> Dict[str, Any]:
        """Parse node parameters"""
        params = {}

        # Split by comma but respect quotes
        parts = []
        current = []
        in_quotes = False
        quote_char = None

        for char in params_str:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current).strip())

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                # Try to convert to number
                elif value.replace('.', '', 1).isdigit():
                    value = float(value) if '.' in value else int(value)
                # Boolean
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'

                params[key] = value
            else:
                # Flag parameter (e.g., "STRICT")
                params[part] = True

        return params

    def get_errors(self) -> List[str]:
        """Get parsing errors"""
        return self.errors

    def has_errors(self) -> bool:
        """Check if there are parsing errors"""
        return len(self.errors) > 0
