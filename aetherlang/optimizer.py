"""
AetherLang AI-Powered Flow Optimizer
Analyzes flows and provides intelligent optimization suggestions
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from .parser import Flow, Node, Edge, NodeType


@dataclass
class Bottleneck:
    """Represents a performance bottleneck"""
    node: str
    node_type: str
    duration: float
    percentage: float
    severity: str  # "critical", "high", "medium", "low"
    suggestion: str
    estimated_improvement: str


@dataclass
class CachingOpportunity:
    """Represents a caching opportunity"""
    node: str
    node_type: str
    reason: str
    estimated_hit_rate: float
    estimated_savings: str


@dataclass
class ParallelizationOpportunity:
    """Represents nodes that can run in parallel"""
    nodes: List[str]
    reason: str
    estimated_time_saved: str


@dataclass
class CostOptimization:
    """Represents a cost optimization opportunity"""
    node: str
    current_model: str
    suggested_model: str
    reason: str
    estimated_savings: str
    quality_impact: str


@dataclass
class FlowAnalysis:
    """Complete flow analysis result"""
    flow_name: str
    total_duration: float
    total_cost: float
    efficiency_score: float
    bottlenecks: List[Bottleneck]
    caching_opportunities: List[CachingOpportunity]
    parallelization_opportunities: List[ParallelizationOpportunity]
    cost_optimizations: List[CostOptimization]
    predicted_duration: float
    predicted_cost: float
    predicted_efficiency: float


class FlowAnalyzer:
    """
    AI-powered flow analysis and optimization
    Detects bottlenecks, caching opportunities, parallelization, and cost optimizations
    """

    # Model costs (per 1M tokens) - approximate
    MODEL_COSTS = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self):
        self.analysis_cache = {}

    def analyze(
        self,
        flow: Flow,
        execution_history: Optional[List[Dict[str, Any]]] = None
    ) -> FlowAnalysis:
        """
        Analyze a flow and return optimization suggestions

        Args:
            flow: Parsed AetherLang flow
            execution_history: List of past execution results with timing data

        Returns:
            FlowAnalysis with all optimization suggestions
        """
        # Use execution history if available, otherwise simulate
        if execution_history and len(execution_history) > 0:
            latest_execution = execution_history[-1]
            node_timings = self._extract_node_timings(latest_execution)
            total_duration = latest_execution.get("duration_seconds", 0)
        else:
            # Simulate based on node types
            node_timings = self._simulate_node_timings(flow)
            total_duration = sum(node_timings.values())

        # Calculate total cost
        total_cost = self._calculate_total_cost(flow, node_timings)

        # Detect issues and opportunities
        bottlenecks = self._detect_bottlenecks(flow, node_timings, total_duration)
        caching_opps = self._find_caching_opportunities(flow, execution_history)
        parallel_opps = self._find_parallelization_opportunities(flow, node_timings)
        cost_opts = self._find_cost_optimizations(flow, node_timings)

        # Calculate efficiency score (0-100)
        efficiency_score = self._calculate_efficiency_score(
            flow, bottlenecks, caching_opps, parallel_opps
        )

        # Predict improvements if optimizations applied
        predicted_duration, predicted_cost = self._predict_improvements(
            total_duration, total_cost, bottlenecks, caching_opps,
            parallel_opps, cost_opts
        )

        predicted_efficiency = min(100.0, efficiency_score + 25)

        return FlowAnalysis(
            flow_name=flow.name,
            total_duration=total_duration,
            total_cost=total_cost,
            efficiency_score=efficiency_score,
            bottlenecks=bottlenecks,
            caching_opportunities=caching_opps,
            parallelization_opportunities=parallel_opps,
            cost_optimizations=cost_opts,
            predicted_duration=predicted_duration,
            predicted_cost=predicted_cost,
            predicted_efficiency=predicted_efficiency
        )

    def _extract_node_timings(self, execution: Dict[str, Any]) -> Dict[str, float]:
        """Extract node execution times from execution log"""
        timings = {}

        execution_log = execution.get("execution_log", [])
        node_starts = {}

        for entry in execution_log:
            node = entry.get("node")
            status = entry.get("status")
            timestamp = entry.get("timestamp")

            # Skip SYSTEM nodes (they're not part of the flow definition)
            if node == "SYSTEM":
                continue

            if status == "START":
                node_starts[node] = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif status == "SUCCESS" and node in node_starts:
                end_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                duration = (end_time - node_starts[node]).total_seconds()
                timings[node] = duration

        return timings

    def _simulate_node_timings(self, flow: Flow) -> Dict[str, float]:
        """Simulate node execution times based on node types"""
        # Estimated durations by node type (in seconds)
        base_durations = {
            NodeType.GUARD: 0.1,
            NodeType.CACHE: 0.1,
            NodeType.LLM: 8.0,  # Expensive!
            NodeType.RAG: 3.0,
            NodeType.SUMMARIZE: 4.0,
            NodeType.ANALYZE: 5.0,
            NodeType.HTTP: 1.0,
            NodeType.VALIDATE: 0.2,
            NodeType.TRANSFORM: 0.5,
            NodeType.FILTER: 0.3,
            NodeType.MERGE: 0.4,
            NodeType.SPLIT: 0.3,
        }

        timings = {}
        for alias, node in flow.nodes.items():
            # Get base duration
            base = base_durations.get(node.node_type, 1.0)

            # Add variance (±20%)
            import random
            variance = random.uniform(0.8, 1.2)

            timings[alias] = base * variance

        return timings

    def _calculate_total_cost(self, flow: Flow, node_timings: Dict[str, float]) -> float:
        """Calculate estimated total cost in USD"""
        total_cost = 0.0

        for alias, node in flow.nodes.items():
            if node.node_type == NodeType.LLM:
                # Estimate token usage based on duration
                duration = node_timings.get(alias, 8.0)
                estimated_tokens = int(duration * 200)  # ~200 tokens/second

                # Get model from params
                model = node.params.get("model", "gpt-4o-mini")

                if model in self.MODEL_COSTS:
                    # Assume 70% input, 30% output
                    input_tokens = estimated_tokens * 0.7
                    output_tokens = estimated_tokens * 0.3

                    cost = (
                        (input_tokens / 1_000_000) * self.MODEL_COSTS[model]["input"] +
                        (output_tokens / 1_000_000) * self.MODEL_COSTS[model]["output"]
                    )
                    total_cost += cost

        return total_cost

    def _detect_bottlenecks(
        self,
        flow: Flow,
        node_timings: Dict[str, float],
        total_duration: float
    ) -> List[Bottleneck]:
        """Detect performance bottlenecks"""
        bottlenecks = []

        if total_duration == 0:
            return bottlenecks

        for alias, duration in node_timings.items():
            percentage = (duration / total_duration) * 100

            # Bottleneck if >40% of total time
            if percentage > 40:
                # Skip if node doesn't exist in flow (safety check)
                if alias not in flow.nodes:
                    continue

                node = flow.nodes[alias]

                # Determine severity
                if percentage > 70:
                    severity = "critical"
                elif percentage > 55:
                    severity = "high"
                else:
                    severity = "medium"

                # Generate suggestion
                suggestion = self._generate_bottleneck_suggestion(node, percentage)

                bottlenecks.append(Bottleneck(
                    node=alias,
                    node_type=node.node_type.value,
                    duration=duration,
                    percentage=percentage,
                    severity=severity,
                    suggestion=suggestion,
                    estimated_improvement=f"-{int(percentage * 0.7)}% time"
                ))

        return sorted(bottlenecks, key=lambda b: b.percentage, reverse=True)

    def _generate_bottleneck_suggestion(self, node: Node, percentage: float) -> str:
        """Generate suggestion for bottleneck"""
        if node.node_type == NodeType.LLM:
            return f"Add cache node before this LLM call to avoid redundant API calls"
        elif node.node_type == NodeType.RAG:
            return f"Consider using faster vector search or reducing top_k parameter"
        elif node.node_type == NodeType.HTTP:
            return f"Add timeout and retry logic, or cache HTTP responses"
        else:
            return f"This node takes {percentage:.0f}% of execution time - consider optimization"

    def _find_caching_opportunities(
        self,
        flow: Flow,
        execution_history: Optional[List[Dict[str, Any]]]
    ) -> List[CachingOpportunity]:
        """Find nodes that would benefit from caching"""
        opportunities = []

        for alias, node in flow.nodes.items():
            # Check if expensive node without cache before it
            if node.node_type in [NodeType.LLM, NodeType.RAG, NodeType.HTTP]:
                # Check if there's already a cache node before it
                has_cache_before = self._has_cache_predecessor(flow, alias)

                if not has_cache_before:
                    # Estimate hit rate based on node type
                    hit_rate = 0.6 if node.node_type == NodeType.LLM else 0.4
                    savings = f"-{int(hit_rate * 70)}% cost"

                    opportunities.append(CachingOpportunity(
                        node=alias,
                        node_type=node.node_type.value,
                        reason=f"Expensive {node.node_type.value} calls can be cached",
                        estimated_hit_rate=hit_rate,
                        estimated_savings=savings
                    ))

        return opportunities

    def _has_cache_predecessor(self, flow: Flow, node_alias: str) -> bool:
        """Check if a node has a cache node before it"""
        # Find incoming edges to this node
        for edge in flow.edges:
            if edge.target == node_alias:
                # Check if source is a cache node
                source_node = flow.nodes.get(edge.source)
                if source_node and source_node.node_type == NodeType.CACHE:
                    return True
                # Recursively check predecessors
                if self._has_cache_predecessor(flow, edge.source):
                    return True
        return False

    def _find_parallelization_opportunities(
        self,
        flow: Flow,
        node_timings: Dict[str, float]
    ) -> List[ParallelizationOpportunity]:
        """Find nodes that can run in parallel"""
        opportunities = []

        # Find nodes that share the same source but don't depend on each other
        source_targets = {}
        for edge in flow.edges:
            if edge.source not in source_targets:
                source_targets[edge.source] = []
            source_targets[edge.source].append(edge.target)

        # Find sources with multiple targets
        for source, targets in source_targets.items():
            if len(targets) >= 2:
                # Check if targets are independent (no edges between them)
                independent = True
                for i, t1 in enumerate(targets):
                    for t2 in targets[i+1:]:
                        if self._has_path(flow, t1, t2) or self._has_path(flow, t2, t1):
                            independent = False
                            break
                    if not independent:
                        break

                if independent:
                    # Calculate potential time saved
                    target_times = [node_timings.get(t, 0) for t in targets]
                    sequential_time = sum(target_times)
                    parallel_time = max(target_times)
                    time_saved = sequential_time - parallel_time

                    if time_saved > 1.0:  # More than 1 second saved
                        opportunities.append(ParallelizationOpportunity(
                            nodes=targets,
                            reason=f"These paths from '{source}' are independent",
                            estimated_time_saved=f"-{time_saved:.1f}s ({int(time_saved/sequential_time*100)}%)"
                        ))

        return opportunities

    def _has_path(self, flow: Flow, start: str, end: str) -> bool:
        """Check if there's a path from start to end node"""
        if start == end:
            return True

        # BFS to find path
        visited = set()
        queue = [start]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current == end:
                return True

            # Add neighbors
            for edge in flow.edges:
                if edge.source == current and edge.target not in visited:
                    queue.append(edge.target)

        return False

    def _find_cost_optimizations(
        self,
        flow: Flow,
        node_timings: Dict[str, float]
    ) -> List[CostOptimization]:
        """Find opportunities to use cheaper models"""
        optimizations = []

        for alias, node in flow.nodes.items():
            if node.node_type == NodeType.LLM:
                current_model = node.params.get("model", "gpt-4o-mini")

                # If using expensive model for simple tasks
                if current_model == "gpt-4o":
                    # Check task complexity (simplified heuristic)
                    system_prompt = node.params.get("system", "")
                    is_simple = len(system_prompt) < 100  # Simple prompt

                    if is_simple:
                        optimizations.append(CostOptimization(
                            node=alias,
                            current_model=current_model,
                            suggested_model="gpt-4o-mini",
                            reason="Task appears simple enough for mini model",
                            estimated_savings="-94% cost",
                            quality_impact="Minimal (for simple tasks)"
                        ))

        return optimizations

    def _calculate_efficiency_score(
        self,
        flow: Flow,
        bottlenecks: List[Bottleneck],
        caching_opps: List[CachingOpportunity],
        parallel_opps: List[ParallelizationOpportunity]
    ) -> float:
        """Calculate efficiency score (0-100)"""
        score = 100.0

        # Deduct for bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.severity == "critical":
                score -= 20
            elif bottleneck.severity == "high":
                score -= 15
            elif bottleneck.severity == "medium":
                score -= 10

        # Deduct for missing caching
        score -= len(caching_opps) * 5

        # Deduct for missed parallelization
        score -= len(parallel_opps) * 8

        return max(0.0, min(100.0, score))

    def _predict_improvements(
        self,
        current_duration: float,
        current_cost: float,
        bottlenecks: List[Bottleneck],
        caching_opps: List[CachingOpportunity],
        parallel_opps: List[ParallelizationOpportunity],
        cost_opts: List[CostOptimization]
    ) -> tuple[float, float]:
        """Predict duration and cost after optimizations"""

        # Duration improvements
        duration_multiplier = 1.0

        # Caching can save 60% on cached calls
        if caching_opps:
            duration_multiplier *= 0.4

        # Parallelization can save time
        for opp in parallel_opps:
            # Extract percentage from string like "-45%"
            if "%" in opp.estimated_time_saved:
                try:
                    pct = float(opp.estimated_time_saved.split("(")[1].split("%")[0])
                    duration_multiplier *= (1 - pct/100)
                except:
                    duration_multiplier *= 0.7

        predicted_duration = current_duration * duration_multiplier

        # Cost improvements
        cost_multiplier = 1.0

        # Caching saves cost
        if caching_opps:
            avg_hit_rate = sum(o.estimated_hit_rate for o in caching_opps) / len(caching_opps)
            cost_multiplier *= (1 - avg_hit_rate * 0.6)

        # Model switching saves cost
        if cost_opts:
            cost_multiplier *= 0.2  # 80% savings

        predicted_cost = current_cost * cost_multiplier

        return (predicted_duration, predicted_cost)


class AIOptimizationSuggester:
    """
    Uses GPT-4o to generate human-readable optimization suggestions
    with specific code fixes
    """

    def __init__(self, openai_client):
        self.client = openai_client

    async def generate_suggestions(
        self,
        flow_code: str,
        analysis: FlowAnalysis
    ) -> Dict[str, Any]:
        """
        Generate AI-powered optimization suggestions

        Args:
            flow_code: Original AetherLang code
            analysis: FlowAnalysis result

        Returns:
            Dict with enhanced suggestions and code fixes
        """

        # Prepare analysis summary for GPT
        analysis_summary = {
            "flow_name": analysis.flow_name,
            "current_performance": {
                "duration": f"{analysis.total_duration:.2f}s",
                "cost": f"${analysis.total_cost:.4f}",
                "efficiency": f"{analysis.efficiency_score:.0f}%"
            },
            "bottlenecks": [
                {
                    "node": b.node,
                    "type": b.node_type,
                    "percentage": f"{b.percentage:.0f}%",
                    "severity": b.severity
                }
                for b in analysis.bottlenecks
            ],
            "caching_opportunities": len(analysis.caching_opportunities),
            "parallelization_opportunities": len(analysis.parallelization_opportunities),
            "cost_optimizations": len(analysis.cost_optimizations)
        }

        prompt = f"""
You are an expert AetherLang flow optimizer. Analyze this workflow and provide specific, actionable optimization suggestions.

FLOW CODE:
```aetherlang
{flow_code}
```

PERFORMANCE ANALYSIS:
{json.dumps(analysis_summary, indent=2)}

DETECTED ISSUES:
- {len(analysis.bottlenecks)} performance bottleneck(s)
- {len(analysis.caching_opportunities)} caching opportunity(ies)
- {len(analysis.parallelization_opportunities)} parallelization opportunity(ies)  
- {len(analysis.cost_optimizations)} cost optimization(s)

TASK:
Provide 3-5 specific optimization suggestions. For each suggestion:

1. **Title**: Short, clear description
2. **Problem**: What's wrong/inefficient  
3. **Solution**: Specific code change needed
4. **Code Fix**: Actual AetherLang code to add/change
5. **Impact**: Expected improvement (time/cost)
6. **Priority**: critical/high/medium/low
7. **Difficulty**: easy/medium/hard

Format as JSON array of suggestions. Be specific about node names and exact code changes.
Focus on the most impactful optimizations first.

Example response format:
[
  {{
    "title": "Add caching before LLM node",
    "problem": "LLM node makes expensive API calls without caching",
    "solution": "Insert cache node with 1-hour TTL before LLM",
    "code_fix": "node Cache: cache ttl=3600;\\nCache -> LLM;",
    "impact": "-60% cost, -70% time on cache hits",
    "priority": "high",
    "difficulty": "easy"
  }}
]
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert workflow optimization AI. Provide specific, actionable suggestions with exact code fixes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            content = response.choices[0].message.content

            # Try to extract JSON array
            try:
                result = json.loads(content)

                # Handle if wrapped in object
                if isinstance(result, dict) and "suggestions" in result:
                    suggestions = result["suggestions"]
                elif isinstance(result, list):
                    suggestions = result
                else:
                    suggestions = [result]

            except json.JSONDecodeError:
                # Fallback to basic suggestions
                suggestions = self._generate_fallback_suggestions(analysis)

            return {
                "suggestions": suggestions,
                "ai_generated": True,
                "model": "gpt-4o"
            }

        except Exception as e:
            print(f"GPT-4o suggestion generation failed: {e}")
            # Return fallback suggestions
            return {
                "suggestions": self._generate_fallback_suggestions(analysis),
                "ai_generated": False,
                "error": str(e)
            }

    def _generate_fallback_suggestions(self, analysis: FlowAnalysis) -> List[Dict[str, Any]]:
        """Generate basic suggestions without GPT-4o"""
        suggestions = []

        # Add suggestion for each bottleneck
        for bottleneck in analysis.bottlenecks[:2]:  # Top 2 bottlenecks
            suggestions.append({
                "title": f"Optimize {bottleneck.node} node",
                "problem": f"Node takes {bottleneck.percentage:.0f}% of total time",
                "solution": bottleneck.suggestion,
                "code_fix": f"# Add optimization for {bottleneck.node}",
                "impact": bottleneck.estimated_improvement,
                "priority": bottleneck.severity,
                "difficulty": "medium"
            })

        # Add caching suggestion
        if analysis.caching_opportunities:
            opp = analysis.caching_opportunities[0]
            suggestions.append({
                "title": f"Add caching for {opp.node}",
                "problem": opp.reason,
                "solution": f"Insert cache node before {opp.node}",
                "code_fix": f"node Cache: cache ttl=3600;\nCache -> {opp.node};",
                "impact": opp.estimated_savings,
                "priority": "high",
                "difficulty": "easy"
            })

        # Add parallelization suggestion
        if analysis.parallelization_opportunities:
            opp = analysis.parallelization_opportunities[0]
            nodes_str = ", ".join(opp.nodes)
            suggestions.append({
                "title": "Enable parallel execution",
                "problem": opp.reason,
                "solution": f"Run {nodes_str} in parallel",
                "code_fix": f"# These can run in parallel:\n" + "\n".join([f"Start -> {n} -> End;" for n in opp.nodes]),
                "impact": opp.estimated_time_saved,
                "priority": "medium",
                "difficulty": "medium"
            })

        return suggestions


class CodeOptimizer:
    """Automatically applies optimization fixes to AetherLang code"""

    def apply_caching_fix(self, code: str, node_name: str, ttl: int = 3600) -> str:
        """
        Add a cache node before the specified node

        Example:
            Input:  Guard -> LLM -> Summarize;
            Output: Guard -> Cache_LLM -> LLM -> Summarize;
                    node Cache_LLM: cache ttl=3600;
        """
        lines = code.split('\n')
        new_lines = []
        cache_node_name = f"Cache_{node_name}"
        cache_definition_added = False

        for line in lines:
            # Add cache node definition after other node definitions
            if 'node ' in line and not cache_definition_added and node_name in line:
                new_lines.append(line)
                new_lines.append(f"  node {cache_node_name}: cache ttl={ttl};")
                cache_definition_added = True
                continue

            # Update edges to include cache node
            if '->' in line and node_name in line and 'node ' not in line:
                # Find patterns like "X -> NodeName" and replace with "X -> Cache_NodeName -> NodeName"
                import re
                pattern = r'(\w+)\s*->\s*' + re.escape(node_name) + r'(?=\s*(?:->|;))'
                replacement = r'\1 -> ' + cache_node_name + ' -> ' + node_name
                line = re.sub(pattern, replacement, line)

            new_lines.append(line)

        return '\n'.join(new_lines)

    def apply_model_downgrade(self, code: str, node_name: str, new_model: str = "gpt-4o-mini") -> str:
        """
        Change the model of an LLM node to a cheaper alternative

        Example:
            Input:  node LLM: llm model="gpt-4o", temp=0.7;
            Output: node LLM: llm model="gpt-4o-mini", temp=0.7;
        """
        lines = code.split('\n')
        new_lines = []

        for line in lines:
            if f'node {node_name}:' in line and 'llm' in line:
                # Replace model value
                import re
                line = re.sub(r'model="[^"]*"', f'model="{new_model}"', line)
            new_lines.append(line)

        return '\n'.join(new_lines)

    def apply_parallelization(self, code: str, nodes: List[str], merge_node: str = "Merger") -> str:
        """
        Convert sequential execution to parallel

        Example:
            Input:  Start -> A -> B -> End;
            Output: Start -> A -> Merger;
                    Start -> B -> Merger;
                    Merger -> End;
                    node Merger: merge strategy="concat";
        """
        lines = code.split('\n')
        new_lines = []
        merge_node_added = False

        # Find the connection pattern and split it
        for line in lines:
            # Skip lines that connect these nodes sequentially
            if '->' in line and all(node in line for node in nodes):
                # Don't include this line - we'll rewrite it
                continue

            # Add merge node definition
            if 'node ' in line and not merge_node_added and any(node in line for node in nodes):
                new_lines.append(line)
                new_lines.append(f"  node {merge_node}: merge strategy=\"concat\";")
                merge_node_added = True
                continue

            new_lines.append(line)

        # Find where to insert new parallel connections
        # Look for the section with edges (after node definitions, before output)
        edge_section_idx = -1
        for i, line in enumerate(new_lines):
            if '->' in line and 'node ' not in line:
                edge_section_idx = i
                break

        if edge_section_idx != -1:
            # Find the source node (what feeds into the parallel nodes)
            source_node = None
            for line in new_lines:
                if '->' in line and nodes[0] in line:
                    import re
                    match = re.search(r'(\w+)\s*->\s*' + re.escape(nodes[0]), line)
                    if match:
                        source_node = match.group(1)
                        break

            if source_node:
                # Insert parallel connections
                parallel_edges = [f"  {source_node} -> {node} -> {merge_node};" for node in nodes]
                new_lines.insert(edge_section_idx, '\n'.join(parallel_edges))

        return '\n'.join(new_lines)

    def apply_all_fixes(self, code: str, analysis: FlowAnalysis) -> str:
        """
        Apply all recommended optimizations automatically

        Returns the optimized code with all fixes applied
        """
        optimized = code

        # 1. Add caching for all opportunities
        for opp in analysis.caching_opportunities:
            optimized = self.apply_caching_fix(optimized, opp.node)

        # 2. Downgrade models for cost optimization
        for cost_opt in analysis.cost_optimizations:
            optimized = self.apply_model_downgrade(optimized, cost_opt.node, cost_opt.suggested_model)

        # 3. Enable parallelization (only first opportunity to avoid complexity)
        if analysis.parallelization_opportunities:
            opp = analysis.parallelization_opportunities[0]
            optimized = self.apply_parallelization(optimized, opp.nodes)

        return optimized

    def generate_diff(self, original: str, optimized: str) -> Dict[str, Any]:
        """
        Generate a human-readable diff between original and optimized code

        Returns:
            {
                "original": original code,
                "optimized": optimized code,
                "changes": [list of changes],
                "lines_added": int,
                "lines_removed": int,
                "lines_modified": int
            }
        """
        import difflib

        original_lines = original.split('\n')
        optimized_lines = optimized.split('\n')

        differ = difflib.Differ()
        diff = list(differ.compare(original_lines, optimized_lines))

        changes = []
        lines_added = 0
        lines_removed = 0
        lines_modified = 0

        for i, line in enumerate(diff):
            if line.startswith('+ '):
                lines_added += 1
                changes.append({"type": "added", "line": i, "content": line[2:]})
            elif line.startswith('- '):
                lines_removed += 1
                changes.append({"type": "removed", "line": i, "content": line[2:]})
            elif line.startswith('? '):
                lines_modified += 1

        return {
            "original": original,
            "optimized": optimized,
            "changes": changes,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "lines_modified": lines_modified
        }
