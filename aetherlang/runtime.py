"""
AetherLang Runtime - Execution Engine για AetherLang flows
"""
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from .parser import Flow, Node, NodeType, Edge
from openai import AsyncOpenAI
from services.aetherlang.v2_prompts import V2_PROMPTS


@dataclass
class ExecutionContext:
    """Context για την εκτέλεση ενός flow"""
    flow: Flow
    inputs: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

    def log(self, node_alias: str, status: str, message: str, data: Any = None):
        """Log execution event"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "node": node_alias,
            "status": status,
            "message": message,
            "data": data
        })


class AetherRuntime:
    """
    Runtime Engine για εκτέλεση AetherLang flows
    Υποστηρίζει:
    - Async execution
    - OpenAI integration
    - Node orchestration
    - Error handling
    """

    def __init__(self, openai_api_key: str):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.execution_history: List[ExecutionContext] = []
        self.profiler = None  # Optional profiler for performance tracking
        self.debugger = None  # Optional time-travel debugger

    async def execute(self, flow: Flow, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete flow"""
        ctx = ExecutionContext(flow=flow, inputs=inputs)
        ctx.log("SYSTEM", "START", f"Εκκίνηση flow '{flow.name}'")

        try:
            # Validate inputs
            for input_name, input_type in flow.inputs.items():
                if input_name not in inputs:
                    raise ValueError(f"Λείπει το input '{input_name}' τύπου {input_type}")

            # Build execution order (topological sort)
            execution_order = self._build_execution_order(flow)
            ctx.log("SYSTEM", "INFO", f"Σειρά εκτέλεσης: {' -> '.join(execution_order)}")

            # Execute nodes in order
            for node_alias in execution_order:
                node = flow.nodes[node_alias]
                await self._execute_node(ctx, node)

            # Collect outputs
            outputs = {}
            for output_name, source_node in flow.outputs.items():
                if source_node in ctx.node_outputs:
                    outputs[output_name] = ctx.node_outputs[source_node]
                else:
                    ctx.log("SYSTEM", "WARNING", f"Output '{output_name}' από node '{source_node}' δεν βρέθηκε")

            ctx.log("SYSTEM", "SUCCESS", "Flow ολοκληρώθηκε επιτυχώς")
            self.execution_history.append(ctx)

            return {
                "status": "success",
                "outputs": outputs,
                "execution_log": ctx.execution_log,
                "duration_seconds": (datetime.now() - ctx.start_time).total_seconds()
            }

        except Exception as e:
            ctx.log("SYSTEM", "ERROR", f"Σφάλμα εκτέλεσης: {str(e)}")
            self.execution_history.append(ctx)
            return {
                "status": "error",
                "error": str(e),
                "execution_log": ctx.execution_log,
                "duration_seconds": (datetime.now() - ctx.start_time).total_seconds()
            }

    async def _execute_node(self, ctx: ExecutionContext, node: Node):
        """Execute a single node"""
        ctx.log(node.alias, "START", f"Εκτέλεση node τύπου {node.node_type.value}")

        # Start profiling if profiler is enabled
        if self.profiler:
            self.profiler.start_node(node.alias, node.node_type.value)

        # Record debugger snapshot at node start
        if self.debugger:
            upstream_data_preview = self._get_upstream_data(ctx, node)
            self.debugger.record_node_start(
                node_name=node.alias,
                node_type=node.node_type.value,
                input_data=upstream_data_preview,
                context={"node_outputs": dict(ctx.node_outputs), "inputs": dict(ctx.inputs)}
            )

        try:
            # Get inputs from upstream nodes
            upstream_data = self._get_upstream_data(ctx, node)

            # Execute based on node type
            if node.node_type == NodeType.GUARD:
                result = await self._execute_guard(ctx, node, upstream_data)
            elif node.node_type == NodeType.PLAN:
                result = await self._execute_plan(ctx, node, upstream_data)
            elif node.node_type == NodeType.RAG:
                result = await self._execute_rag(ctx, node, upstream_data)
            elif node.node_type == NodeType.LLM:
                result = await self._execute_llm(ctx, node, upstream_data)
            elif node.node_type == NodeType.TRANSFORM:
                result = await self._execute_transform(ctx, node, upstream_data)
            elif node.node_type == NodeType.FILTER:
                result = await self._execute_filter(ctx, node, upstream_data)
            elif node.node_type == NodeType.MERGE:
                result = await self._execute_merge(ctx, node, upstream_data)
            elif node.node_type == NodeType.ANALYZE:
                result = await self._execute_analyze(ctx, node, upstream_data)
            elif node.node_type == NodeType.EXTRACT:
                result = await self._execute_extract(ctx, node, upstream_data)
            elif node.node_type == NodeType.SUMMARIZE:
                result = await self._execute_summarize(ctx, node, upstream_data)
            # Advanced control flow
            elif node.node_type == NodeType.CONDITIONAL:
                result = await self._execute_conditional(ctx, node, upstream_data)
            elif node.node_type == NodeType.LOOP:
                result = await self._execute_loop(ctx, node, upstream_data)
            elif node.node_type == NodeType.PARALLEL:
                result = await self._execute_parallel(ctx, node, upstream_data)
            elif node.node_type == NodeType.SWITCH:
                result = await self._execute_switch(ctx, node, upstream_data)
            # Data operations
            elif node.node_type == NodeType.MAP:
                result = await self._execute_map(ctx, node, upstream_data)
            elif node.node_type == NodeType.REDUCE:
                result = await self._execute_reduce(ctx, node, upstream_data)
            elif node.node_type == NodeType.SPLIT:
                result = await self._execute_split(ctx, node, upstream_data)
            elif node.node_type == NodeType.JOIN:
                result = await self._execute_join(ctx, node, upstream_data)
            # Performance & reliability
            elif node.node_type == NodeType.CACHE:
                result = await self._execute_cache(ctx, node, upstream_data)
            elif node.node_type == NodeType.RETRY:
                result = await self._execute_retry(ctx, node, upstream_data)
            elif node.node_type == NodeType.TIMEOUT:
                result = await self._execute_timeout(ctx, node, upstream_data)
            elif node.node_type == NodeType.FALLBACK:
                result = await self._execute_fallback(ctx, node, upstream_data)
            # External integrations
            elif node.node_type == NodeType.WEBHOOK:
                result = await self._execute_webhook(ctx, node, upstream_data)
            elif node.node_type == NodeType.HTTP:
                result = await self._execute_http(ctx, node, upstream_data)
            # Advanced processing
            elif node.node_type == NodeType.VALIDATE:
                result = await self._execute_validate(ctx, node, upstream_data)
            elif node.node_type == NodeType.ENRICH:
                result = await self._execute_enrich(ctx, node, upstream_data)
            elif node.node_type == NodeType.SLEEP:
                result = await self._execute_sleep(ctx, node, upstream_data)
            elif node.node_type == NodeType.RATE_LIMIT:
                result = await self._execute_rate_limit(ctx, node, upstream_data)
            # V2 Domain-specific nodes
            elif node.node_type == NodeType.CHEF:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'chef')
            elif node.node_type == NodeType.MOLECULAR:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'molecular')
            elif node.node_type == NodeType.BALANCE:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'balance')
            elif node.node_type == NodeType.VISION:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'vision')
            elif node.node_type == NodeType.ASSEMBLY:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'assembly')
            elif node.node_type == NodeType.ORACLE:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'oracle')
            elif node.node_type == NodeType.APEX:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'apex')
            elif node.node_type == NodeType.RESEARCH:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'research')
            elif node.node_type == NodeType.CONSULT:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'consult')
            elif node.node_type == NodeType.MARKET:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'market')
            elif node.node_type == NodeType.VISUALIZER:
                result = await self._execute_v2_domain(ctx, node, upstream_data, 'visualizer')
            else:
                raise ValueError(f"Άγνωστος τύπος node: {node.node_type}")

            ctx.node_outputs[node.alias] = result
            ctx.log(node.alias, "SUCCESS", f"Επιτυχής εκτέλεση", result)

            # End profiling on success
            if self.profiler:
                # Estimate cost for LLM nodes (simplified)
                cost = 0.0
                tokens = 0
                api_calls = 0
                if node.node_type.value == "llm":
                    # Rough estimate: $0.01 per 1K tokens, assume ~500 tokens per call
                    tokens = 500
                    cost = 0.005
                    api_calls = 1
                self.profiler.end_node(node.alias, cost=cost, tokens=tokens, api_calls=api_calls, status="success")

            # Record debugger snapshot at node end
            if self.debugger:
                node_start_time = None
                for log_entry in ctx.execution_log:
                    if log_entry.get("node") == node.alias and log_entry.get("status") == "START":
                        from datetime import datetime
                        node_start_time = datetime.fromisoformat(log_entry["timestamp"])
                        break

                duration = 0.0
                if node_start_time:
                    duration = (datetime.now() - node_start_time).total_seconds()

                self.debugger.record_node_end(
                    node_name=node.alias,
                    node_type=node.node_type.value,
                    output_data={"result": result},
                    context={"node_outputs": dict(ctx.node_outputs), "inputs": dict(ctx.inputs)},
                    duration=duration
                )

        except Exception as e:
            ctx.log(node.alias, "ERROR", f"Σφάλμα: {str(e)}")

            # End profiling on error
            if self.profiler:
                self.profiler.end_node(node.alias, status="error", error_message=str(e))

            # Record debugger error
            if self.debugger:
                self.debugger.record_node_error(
                    node_name=node.alias,
                    node_type=node.node_type.value,
                    error=str(e),
                    context={"node_outputs": dict(ctx.node_outputs), "inputs": dict(ctx.inputs)}
                )

            raise

    def _get_upstream_data(self, ctx: ExecutionContext, node: Node) -> Dict[str, Any]:
        """Get data from upstream nodes"""
        data = {"inputs": ctx.inputs}

        # Find upstream nodes
        for edge in ctx.flow.edges:
            if edge.target == node.alias:
                if edge.source in ctx.node_outputs:
                    data[edge.source] = ctx.node_outputs[edge.source]

        return data

    async def _execute_guard(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GUARD node - validates and filters input"""
        mode = node.params.get("mode", "NORMAL")
        query = data["inputs"].get("query", "")

        # Simple content filtering
        dangerous_patterns = ["hack", "exploit", "malware", "virus"]

        if mode == "STRICT":
            for pattern in dangerous_patterns:
                if pattern.lower() in query.lower():
                    return {
                        "status": "blocked",
                        "reason": f"Εντοπίστηκε μη επιτρεπτό περιεχόμενο: {pattern}",
                        "query": None
                    }

        return {
            "status": "approved",
            "query": query,
            "mode": mode
        }

    async def _execute_plan(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PLAN node - creates execution plan"""
        steps = node.params.get("steps", 3)
        query = data.get("Guardian", {}).get("query") or data["inputs"].get("query", "")

        # Use LLM to create plan
        system_prompt = f"""Είσαι ένας AI planner. Δημιούργησε ένα σχέδιο δράσης με {steps} βήματα
        για να απαντήσεις στο ερώτημα του χρήστη. Απάντησε σε JSON format με λίστα steps."""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.3
        )

        plan_text = response.choices[0].message.content

        return {
            "query": query,
            "plan": plan_text,
            "steps": steps
        }

    async def _execute_rag(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RAG node - retrieves relevant context"""
        topk = node.params.get("topk", 3)
        query = data["inputs"].get("query", "")

        # Simplified RAG - in production would use vector DB
        context = f"""
        Σχετικό πλαίσιο για: {query}

        [Εδώ θα υπήρχαν τα {topk} πιο σχετικά αποτελέσματα από vector database]

        Γενικές πληροφορίες:
        - Το NeuroDoc είναι AI-powered document processing platform
        - Υποστηρίζει Ελληνικά και OCR
        - Χρησιμοποιει OpenAI GPT-4o models
        """

        return {
            "query": query,
            "context": context,
            "sources": topk
        }

    async def _execute_llm(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM node - main AI processing"""
        model = node.params.get("model", "gpt-4o")
        temp = node.params.get("temp", 0.7)

        # Get query and context
        query = data["inputs"].get("query", "")
        plan = data.get("Planner", {}).get("plan", "")
        context = data.get("RAG", {}).get("context", "")

        # Build comprehensive prompt
        system_prompt = """Είσαι το NeuroLab Ω, ένα προηγμένο AI σύστημα για ανάλυση και επεξεργασία.
        Παρέχεις λεπτομερείς, δομημένες απαντήσεις με:
        - Executive Summary
        - Deep Dive Analysis
        - Comparative Approaches
        - Risks & Mitigations
        - Action Plan
        - KPIs & Metrics"""

        user_message = f"""Ερώτημα: {query}

{f'Σχέδιο δράσης: {plan}' if plan else ''}

{f'Πλαίσιο: {context}' if context else ''}

Παρακαλώ δώσε μια ολοκληρωμένη απάντηση ακολουθώντας τη δομή που περιγράφεται."""

        # Extract model name (handle "openai:gpt-4o" format)
        if ":" in model:
            model = model.split(":")[-1]

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temp
        )

        result = response.choices[0].message.content

        return {
            "query": query,
            "response": result,
            "model": model,
            "temperature": temp
        }

    async def _execute_transform(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TRANSFORM node - data transformation"""
        # Get previous output
        prev_data = None
        for key, value in data.items():
            if key != "inputs" and isinstance(value, dict):
                prev_data = value
                break

        transform_type = node.params.get("type", "json")

        return {
            "transformed": True,
            "type": transform_type,
            "data": prev_data
        }

    async def _execute_filter(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute FILTER node - filters data based on criteria"""
        criteria = node.params.get("criteria", "")

        return {
            "filtered": True,
            "criteria": criteria,
            "data": data
        }

    async def _execute_merge(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MERGE node - merges multiple inputs"""
        merged = {}
        for key, value in data.items():
            if key != "inputs":
                merged[key] = value

        return {
            "merged": True,
            "sources": list(merged.keys()),
            "data": merged
        }

    async def _execute_analyze(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ANALYZE node - deep analysis"""
        query = data["inputs"].get("query", "")

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Είσαι ένας expert αναλυτής. Κάνε σε βάθος ανάλυση."},
                {"role": "user", "content": f"Ανάλυσε: {query}"}
            ],
            temperature=0.5
        )

        return {
            "analysis": response.choices[0].message.content,
            "query": query
        }

    async def _execute_extract(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute EXTRACT node - extracts structured data"""
        extract_type = node.params.get("type", "entities")

        return {
            "extracted": True,
            "type": extract_type,
            "data": data
        }

    async def _execute_summarize(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SUMMARIZE node - creates summary"""
        # Get text to summarize
        text_to_summarize = ""
        for key, value in data.items():
            if isinstance(value, dict) and "response" in value:
                text_to_summarize = value["response"]
                break

        if not text_to_summarize:
            text_to_summarize = str(data)

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Δημιούργησε μια σύντομη περίληψη του κειμένου."},
                {"role": "user", "content": text_to_summarize}
            ],
            temperature=0.3
        )

        return {
            "summary": response.choices[0].message.content,
            "original_length": len(text_to_summarize)
        }

    # ============================================================================
    # ADVANCED NODE TYPES - New Implementations
    # ============================================================================

    async def _execute_conditional(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CONDITIONAL node - if/else logic"""
        condition = node.params.get("condition", "true")

        # Simple condition evaluation
        result_value = eval(condition, {}, {"data": data, "len": len, "str": str})

        return {
            "condition_met": bool(result_value),
            "condition": condition,
            "data": data
        }

    async def _execute_loop(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LOOP node - iterate over data"""
        iterations = node.params.get("iterations", 1)
        max_iterations = min(iterations, 100)  # Safety limit

        results = []
        for i in range(max_iterations):
            results.append({
                "iteration": i + 1,
                "data": data
            })

        return {
            "iterations": max_iterations,
            "results": results
        }

    async def _execute_parallel(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PARALLEL node - execute multiple paths simultaneously"""
        # Simplified parallel execution - would need actual parallel node execution
        return {
            "status": "parallel_ready",
            "data": data,
            "note": "Parallel execution support"
        }

    async def _execute_switch(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SWITCH node - multi-way branching"""
        key = node.params.get("key", "default")
        cases = node.params.get("cases", {})

        selected_case = cases.get(key, cases.get("default", "no_match"))

        return {
            "selected_case": selected_case,
            "key": key,
            "data": data
        }

    async def _execute_map(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MAP node - transform arrays"""
        operation = node.params.get("operation", "identity")
        items = data.get("items", [])

        if operation == "uppercase":
            mapped = [str(item).upper() for item in items]
        elif operation == "double":
            mapped = [item * 2 for item in items if isinstance(item, (int, float))]
        else:
            mapped = items

        return {
            "mapped": mapped,
            "count": len(mapped),
            "operation": operation
        }

    async def _execute_reduce(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute REDUCE node - aggregate data"""
        operation = node.params.get("operation", "sum")
        items = data.get("items", [])

        if operation == "sum":
            result = sum(items) if all(isinstance(x, (int, float)) for x in items) else 0
        elif operation == "count":
            result = len(items)
        elif operation == "join":
            result = ", ".join(str(x) for x in items)
        else:
            result = items

        return {
            "result": result,
            "operation": operation,
            "item_count": len(items)
        }

    async def _execute_split(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SPLIT node - split data into multiple streams"""
        delimiter = node.params.get("delimiter", ",")
        text = str(data.get("inputs", {}).get("query", ""))

        parts = text.split(delimiter)

        return {
            "parts": parts,
            "count": len(parts),
            "delimiter": delimiter
        }

    async def _execute_join(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JOIN node - join multiple data sources"""
        separator = node.params.get("separator", " ")

        # Collect all upstream data
        parts = []
        for key, value in data.items():
            if key != "inputs" and isinstance(value, dict):
                parts.append(str(value.get("data", value)))

        joined = separator.join(parts)

        return {
            "joined": joined,
            "sources": len(parts)
        }

    async def _execute_cache(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CACHE node - cache results"""
        ttl = node.params.get("ttl", 300)  # Time to live in seconds

        # Simple cache implementation (in-memory)
        cache_key = str(hash(str(data)))

        return {
            "cached": True,
            "cache_key": cache_key,
            "ttl": ttl,
            "data": data
        }

    async def _execute_retry(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RETRY node - retry on failure"""
        max_attempts = node.params.get("attempts", 3)

        return {
            "attempts": max_attempts,
            "status": "success",
            "data": data
        }

    async def _execute_timeout(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TIMEOUT node - add execution timeout"""
        timeout_seconds = node.params.get("timeout", 30)

        return {
            "timeout": timeout_seconds,
            "status": "within_timeout",
            "data": data
        }

    async def _execute_fallback(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute FALLBACK node - fallback on error"""
        fallback_value = node.params.get("fallback", "default")

        return {
            "status": "success",
            "fallback_value": fallback_value,
            "data": data
        }

    async def _execute_webhook(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute WEBHOOK node - call external APIs"""
        url = node.params.get("url", "https://example.com/webhook")
        method = node.params.get("method", "POST")

        # Simplified webhook - in production would make actual HTTP call
        return {
            "status": "webhook_called",
            "url": url,
            "method": method,
            "payload": data,
            "note": "Webhook support - would make actual HTTP call in production"
        }

    async def _execute_http(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP node - HTTP requests"""
        url = node.params.get("url", "https://api.example.com")
        method = node.params.get("method", "GET")

        return {
            "status": "http_request",
            "url": url,
            "method": method,
            "note": "HTTP support - would make actual request in production"
        }

    async def _execute_validate(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute VALIDATE node - data validation"""
        schema = node.params.get("schema", {})

        # Simple validation
        is_valid = True
        errors = []

        if schema:
            # Would use jsonschema or similar in production
            is_valid = True
            errors = []

        return {
            "valid": is_valid,
            "errors": errors,
            "data": data
        }

    async def _execute_enrich(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ENRICH node - enrich data with external sources"""
        source = node.params.get("source", "database")

        # Simplified enrichment
        enrichment = {
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "metadata": {"enriched": True}
        }

        return {
            **data,
            "enrichment": enrichment
        }

    async def _execute_sleep(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SLEEP node - add delays"""
        duration = node.params.get("duration", 1)
        max_sleep = min(duration, 10)  # Max 10 seconds for safety

        await asyncio.sleep(max_sleep)

        return {
            "slept": max_sleep,
            "data": data
        }

    async def _execute_rate_limit(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RATE_LIMIT node - rate limiting"""
        requests_per_second = node.params.get("rps", 10)

        return {
            "rate_limit": requests_per_second,
            "status": "within_limit",
            "data": data
        }

    def _build_execution_order(self, flow: Flow) -> List[str]:
        """Build topological execution order"""
        # Create adjacency list
        graph = {node_alias: [] for node_alias in flow.nodes.keys()}
        in_degree = {node_alias: 0 for node_alias in flow.nodes.keys()}

        for edge in flow.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Topological sort (Kahn's algorithm)
        queue = [node for node, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(flow.nodes):
            raise ValueError("Εντοπίστηκε κυκλική εξάρτηση στο flow")

        return order

    def get_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return [
            {
                "flow_name": ctx.flow.name,
                "start_time": ctx.start_time.isoformat(),
                "inputs": ctx.inputs,
                "log": ctx.execution_log
            }
            for ctx in self.execution_history
        ]

    async def _execute_v2_domain(self, ctx, node, data, domain):
        params = node.params
        query = data.get("query", data.get("message", ctx.inputs.get("query", "")))
        upstream_text = str(data)[:2000]
        cuisine = str(params.get("cuisine", "greek"))
        difficulty = str(params.get("difficulty", "medium"))
        servings = str(params.get("servings", 4))

        # Use enhanced V2 prompts from v2_prompts.py
        base_prompt = V2_PROMPTS.get(domain, domain + " analysis")
        
        # Add dynamic context
        context_parts = [base_prompt]
        if domain == "chef":
            context_parts.append("Cuisine: " + cuisine + ", Difficulty: " + difficulty + ", Servings: " + servings + ".")
        if domain == "molecular":
            context_parts.append("Complexity: " + str(params.get("complexity", "advanced")) + ".")
        if domain == "consult":
            context_parts.append("Domain: " + str(params.get("domain", "business")) + ", Framework: " + str(params.get("framework", "SWOT")) + ".")
        if domain == "market":
            context_parts.append("Scope: " + str(params.get("scope", "global")) + ", Timeframe: " + str(params.get("timeframe", "6months")) + ".")
        if domain == "oracle":
            context_parts.append("Timeframe: " + str(params.get("timeframe", "6months")) + ".")
        if domain == "research":
            context_parts.append("Depth: " + str(params.get("depth", "comprehensive")) + ".")
        if domain == "balance":
            context_parts.append("Focus: " + str(params.get("focus", "both")) + ".")
        
        context_parts.append("Query: " + str(query))
        if upstream_text and len(upstream_text) > 10:
            context_parts.append("Context from previous nodes: " + upstream_text[:1500])
        
        prompt = " ".join(context_parts)
        system_msg = "You are AetherLang " + domain + " node. Provide detailed, professional output."

        try:
            response = await self.openai_client.chat.completions.create(
                model=params.get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=float(params.get("temp", 0.7)),
                max_tokens=int(params.get("max_tokens", 3000))
            )
            return {"output": response.choices[0].message.content, "domain": domain, "params": dict(params)}
        except Exception as e:
            ctx.log(node.alias, "ERROR", str(domain) + " node error: " + str(e))
            return {"output": "[" + domain.upper() + "] Error: " + str(e), "domain": domain}
