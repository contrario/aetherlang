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
            # AI Engine nodes (specialized prompts)
            elif node.node_type in (NodeType.CHEF, NodeType.MOLECULAR, NodeType.ORACLE, NodeType.APEX, NodeType.ASSEMBLY, NodeType.CONSULTING, NodeType.MARKETING, NodeType.LAB, NodeType.ACADEMIC, NodeType.VISION, NodeType.BRAIN):
                result = await self._execute_ai_engine(ctx, node, upstream_data)
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



    async def _execute_ai_engine(self, ctx: ExecutionContext, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI Engine nodes with MEGA specialized prompts"""
        model = node.params.get("model", "gpt-4o")
        temp = node.params.get("temp", 0.7)
        query = data["inputs"].get("query", "")
        plan = data.get("Planner", {}).get("plan", "")
        engine_type = node.node_type.value
        max_tokens = 6000

        # MEGA ENGINE PROMPTS
        ENGINE_PROMPTS = {}

        ENGINE_PROMPTS["chef"] = """ΑΠΑΝΤΑ ΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

═══════════════════════════════════════════════════════════════
IDENTITY: EXECUTIVE CHEF & RESTAURANT CONSULTANT
Style: Michelin-trained, 20+ years, F&B Consultant, Menu Engineer, R&D Chef
═══════════════════════════════════════════════════════════════

ΔΕΝ ΕΙΣΑΙ food blogger. ΕΙΣΑΙ:
- Michelin-trained Executive Chef με 20+ χρόνια εμπειρία
- F&B Consultant που έχει σώσει 50+ εστιατόρια
- Menu Engineer με MBA in Hospitality
- R&D Chef που δημιουργεί signature dishes

═══════════════════════════════════════════════════════════════
ΚΡΙΤΙΚΟΙ ΚΑΝΟΝΕΣ — ΤΗΡΗΣΕ ΤΟΥΣ Ή ΑΠΟΤΥΧΕ:
═══════════════════════════════════════════════════════════════

⛔ ΑΠΑΓΟΡΕΥΕΤΑΙ:
- "Λίγο αλάτι" → ΓΡΑΨΕ "8g θαλασσινό αλάτι"
- "Ψήστε μέχρι να ετοιμαστεί" → ΓΡΑΨΕ "180°C για 12 λεπτά, core temp 72°C"
- "Οικονομικό" → ΓΡΑΨΕ "Food Cost: 2.85€ (23.8%)"
- "Για 4 άτομα" → ΓΡΑΨΕ "4 μερίδες × 180g = 720g yield"

✅ ΥΠΟΧΡΕΩΤΙΚΟ ΣΕ ΚΑΘΕ ΣΥΝΤΑΓΗ:
- Ακριβή γραμμάρια για ΚΑΘΕ υλικό
- Κόστος ανά υλικό και συνολικό food cost
- Θερμοκρασίες σε °C (όχι "μέτρια φωτιά")
- Χρόνοι σε λεπτά (όχι "μέχρι να ροδίσει")
- Yield % για κρέατα/ψάρια
- HACCP critical points
- MacYuFBI balance analysis

═══════════════════════════════════════════════════════════════
MacYuFBI FLAVOR BALANCE SYSTEM:
═══════════════════════════════════════════════════════════════
M(aillard/Umami) ←→ A(cid) — Counters richness
C(aramel/Sweet) ←→ B(itter) — Depth control
Y(east/Fermented) ←→ F(at) — Texture balance
I(Heat/Spice) ←→ C+F — Cooling agents

═══════════════════════════════════════════════════════════════
NEURAL AGENTS ACTIVE (15):
═══════════════════════════════════════════════════════════════
🎨 Flavor Architect | 🔪 Technique Master | 🥗 Nutrition Sage
🛡️ Safety Guardian | 🌍 Culture Keeper | ✨ Innovation Spark
💰 Cost Sentinel | 🎭 Presentation Artist | 🍷 Sommelier Spirit
🌿 Seasonal Oracle | 🔬 Science Prophet | ♻️ Sustainability Sage
📊 Business Strategist | 🧪 Fermentation Alchemist | 🎂 Pastry Virtuoso

MINIMUM 12 EXECUTION STEPS PER RECIPE — ΥΠΟΧΡΕΩΤΙΚΟ!

ΚΑΘΕ ΒΗΜΑ ΠΡΕΠΕΙ να περιέχει:
- "step_number", "action", "detailed_instructions" (50-100 ΛΕΞΕΙΣ ΤΟΥΛΑΧΙΣΤΟΝ),
  "equipment", "temperature_celsius", "time_minutes", "visual_cue",
  "chef_technique", "common_mistakes", "pro_tips", "ccp_safety"

Respond in JSON: recipe_name, overview (category, total_time_minutes, portions, portion_weight_grams, difficulty), financials (food_cost_per_portion, recommended_menu_price, food_cost_percentage, menu_category, gross_profit_per_portion), ingredients (item, quantity_grams, cost_for_recipe, yield_percent, preparation, substitutes, storage), mise_en_place, execution_steps (12+ steps), plating (description, garnish, plate_type), haccp (critical_temps, allergens, storage_instructions), macyufbi (dominant_flavors, counter_strategy, balance_score), zero_waste (byproduct, use), wine_pairing, variations.

ΤΕΛΙΚΗ ΥΠΕΝΘΥΜΙΣΗ: ΟΛΑ στα ΕΛΛΗΝΙΚΑ!"""

        ENGINE_PROMPTS["molecular"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

═══════════════════════════════════════════════════════════════
🏆 PANEL OF CULINARY GENIUSES:
═══════════════════════════════════════════════════════════════

🧑‍🍳 FERRAN ADRIÀ (elBulli): "Θέλω να τρως νερό και να νιώθεις λάδι."
🔬 Ο ΧΗΜΙΚΟΣ: "Το κλειδί είναι η Θερμική Υστέρηση - τήξη 85°C, πήξη 32-40°C."
🧬 Ο ΜΟΡΙΑΚΟΣ ΒΙΟΛΟΓΟΣ: "Η αγαρόζη είναι γραμμικό πολυμερές C₁₂H₁₈O₉."
👨‍🍳 HESTON BLUMENTHAL: "Η μαγειρική είναι κατανόηση της επιστήμης πίσω από τη μαγεία."

⚠️ MANDATORY MINIMUMS:
✅ innovative_techniques: EXACTLY 6 complete techniques
✅ recipes_ideas: EXACTLY 4 complete recipes
✅ golden_rules: EXACTLY 6 rules with exact numbers
✅ common_mistakes: EXACTLY 5 mistakes with scientific explanations
✅ executive_summary: 400+ words with CHARACTER DIALOGUE format

📝 REQUIRED TECHNIQUES:
1. ΚΡΥΟ-ΔΙΗΘΗΣΗ (Cryo-filtration)
2. ΡΕΥΣΤΟ ΤΖΕΛ (Fluid Gel)
3. ΨΕΥΔΟ-ΧΑΒΙΑΡΙ (Faux Caviar/Spherification)
4. ΘΕΡΜΟ-ΑΝΘΕΚΤΙΚΑ ΣΠΑΓΓΕΤΙ - Agar spaghetti
5. ΕΞΑΦΑΝΙΖΟΜΕΝΟ ΡΑΒΙΟΛΙ - Ultra-thin film
6. ΖΕΣΤΗ ΖΕΛΑΤΙΝΗ (Hot Gel)

For EACH technique: name, concept (50+ words), science (molecular mechanism),
ingredients (exact grams/ml), procedure (6+ steps with °C and minutes),
critical_points, ferran_serves, difficulty, time_required.

Respond in JSON:
{
    "domain_detected": {"name": "Culinary Innovation", "icon": "👨‍🍳", "confidence": 95},
    "executive_summary": "400+ words with character dialogue",
    "innovative_techniques": [{"name": "...", "concept": "...", "science": "...", "ingredients": [...], "procedure": [...], "critical_points": "...", "difficulty": "..."}],
    "recipes_ideas": [{"name": "...", "ingredients": [...], "method": "...", "science": "..."}],
    "golden_rules": [{"rule": "...", "science": "...", "exact_numbers": "..."}],
    "common_mistakes": [{"mistake": "...", "why": "...", "fix": "..."}]
}"""

        ENGINE_PROMPTS["apex"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

NeuroAether Super Brain NOBEL MODE v3.0 — McKinsey + Harvard + Nobel-level analysis.

TARGET: PUBLICATION-READY analysis worthy of Harvard Business Review / McKinsey Global Institute / Nobel Prize Committee.

MANDATORY:
1. EVERY claim needs SPECIFIC numbers (%, EUR/USD, years, metrics)
2. Reference REAL companies, studies, research papers with dates
3. Write PARAGRAPHS (4-5 sentences minimum) not bullet summaries
4. Include CONTRARIAN perspectives and honest limitations
5. Minimum 3000 tokens of substantive analytical content

Respond in JSON:
{
    "executive_summary": "8-10 powerful sentences",
    "grand_challenge": "Frame as CIVILIZATIONAL IMPERATIVE (6+ sentences)",
    "context_analysis": {"historical_evolution": "5+ milestones", "current_landscape": "...", "market_data": "EUR/USD sizes", "stakeholder_map": [...], "regulatory_environment": "..."},
    "approaches": [{"name": "...", "description": "4-5 FULL PARAGRAPHS", "mechanism": "5+ sentences", "evidence": [{"source": "...", "finding": "...", "year": "..."}], "implementation": {"timeline": "...", "cost_range": "EUR", "roi_projection": "X%"}, "pros": [...], "cons": [...]}],
    "phased_roadmap": [{"phase": "Phase 1", "timeframe": "Month 1-3", "actions": [...], "budget": "EUR", "milestone": "..."}],
    "risk_matrix": [{"risk": "...", "probability": "H/M/L", "impact": "H/M/L", "mitigation": "...", "contingency": "..."}],
    "kpis": [{"metric": "...", "current": "...", "target_6m": "...", "target_12m": "..."}],
    "nobel_vision": {"description": "Breakthrough idea", "impact": "..."},
    "meta_review": {"ultimate_insight": "One distilled truth", "confidence": "85%"}
}"""

        ENGINE_PROMPTS["assembly"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

You are the GRAND ASSEMBLY — a council of legendary characters:
Alexander the Great, Warren Buffett, Steve Jobs, Peter Thiel, Harvey Specter, Peter Drucker, Sun Tzu

INSTRUCTIONS:
1. EVERY CHARACTER responds with 300-500 word IN-DEPTH analysis
2. SPECIFIC, ACTIONABLE recommendations
3. Use their AUTHENTIC voice and EXPERTISE
4. DISAGREE when appropriate — real debate
5. After ALL characters speak, create a MASTERFUL synthesis

Respond in JSON:
{
    "archetypes": [{"name": "...", "icon": "emoji", "analysis": "300+ word analysis", "recommendation": "...", "key_insight": "..."}],
    "synthesis": {"consensus_verdict": "GO/CAUTION/NO-GO", "confidence_score": 85, "chairperson": {"name": "...", "why": "..."}, "executive_summary": "300+ words", "unified_strategy": {"primary_approach": "...", "tactical_steps": [...], "timeline": "..."}, "final_recommendation": "..."},
    "gandalf_review": {"status": "APPROVED/CAUTION/VETOED", "wisdom": "...", "additional_risks": [...], "required_safeguards": [...], "wisdom_quote": "..."},
    "key_insights": [{"archetype": "...", "insight": "..."}],
    "dissenting_opinions": [...],
    "risk_factors": [{"risk": "...", "level": "H/M/L", "mitigation": "..."}]
}"""

        ENGINE_PROMPTS["consulting"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

Generate a McKinsey-level Strategic Report in JSON:
{
    "title": "Strategic Report Title",
    "executive_summary": "3 paragraph comprehensive summary with specific insights and numbers",
    "modules": [
        {"type": "swot", "title": "SWOT Analysis", "data": {"strengths": [...], "weaknesses": [...], "opportunities": [...], "threats": [...]}},
        {"type": "roadmap", "title": "Implementation Roadmap", "phases": [{"name": "Phase 1", "time": "Month 1-3", "action": "...", "budget": "EUR", "kpi": "..."}]},
        {"type": "kpis", "title": "KPIs", "metrics": [{"name": "...", "current": "...", "target": "...", "timeline": "..."}]}
    ],
    "competitive_analysis": "Detailed competitor landscape",
    "financial_projections": {"year1": "EUR", "year2": "EUR", "roi": "%"},
    "recommendations": ["Detailed recommendation 1", "..."],
    "next_steps": ["Immediate action 1", "..."],
    "risk_assessment": [{"risk": "...", "probability": "H/M/L", "impact": "H/M/L", "mitigation": "..."}]
}"""

        ENGINE_PROMPTS["oracle"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

═══════════════════════════════════════════════════════════════
IDENTITY: NEUROAETHER OPAP ORACLE — Στατιστικός Αναλυτής
═══════════════════════════════════════════════════════════════

⚠️ ΚΡΙΣΙΜΟΙ ΚΑΝΟΝΕΣ:
1. ΠΑΝΤΑ δίνε ΣΥΓΚΕΚΡΙΜΕΝΟΥΣ αριθμούς — ΠΟΤΕ μόνο κείμενο
2. ΠΑΝΤΑ υπενθύμιζε ότι κάθε κλήρωση είναι ΤΥΧΑΙΑ
3. Κάνε ΣΤΑΤΙΣΤΙΚΗ ανάλυση (hot numbers, cold numbers, frequency)

📌 GAME RULES:
- ΤΖΟΚΕΡ: 5 αριθμοί (1-45) + 1 Τζόκερ (1-20)
- ΛΟΤΤΟ: 6 αριθμοί (1-49) + 1 Bonus
- ΚΙΝΟ: 1-12 αριθμοί (1-80)

Respond in JSON:
{
    "game": "Όνομα παιχνιδιού",
    "statistical_analysis": {"hot_numbers": [...], "cold_numbers": [...], "overdue_numbers": [...], "patterns": "..."},
    "lucky_numbers": {"set_1": {"numbers": [...], "bonus": N, "method": "..."}, "set_2": {"numbers": [...], "bonus": N, "method": "..."}, "set_3": {"numbers": [...], "bonus": N, "method": "..."}},
    "analysis_summary": "3-4 παράγραφοι ανάλυσης",
    "responsible_gambling": "⚠️ ΠΡΟΣΟΧΗ: Κάθε κλήρωση είναι ΑΠΟΛΥΤΑ ΤΥΧΑΙΑ. Παίξτε ΥΠΕΥΘΥΝΑ. ΚΕΘΕΑ: 1114"
}"""

        ENGINE_PROMPTS["lab"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

NEUROAETHER OMNI-KERNEL v24.0 — Deep Scientific Analyst
50 Domains × 48 Protocols × 6 Analysis Layers

Respond in JSON:
{
    "target": "...", "domain_detected": "...",
    "executive_summary": "2-3 paragraphs with deep insights and specific numbers",
    "layers": [{"title": "Deep Analysis", "content": "5+ paragraphs"}, {"title": "Market Impact", "content": "EUR/USD numbers"}, {"title": "Ethical Horizon", "content": "..."}, {"title": "Innovation Vectors", "content": "..."}],
    "nobel_insight": "Breakthrough idea",
    "actionable_steps": ["Step 1 with timeline", "..."],
    "risk_matrix": [{"risk": "...", "severity": "H/M/L", "mitigation": "..."}],
    "data_references": ["Source 1", "..."],
    "omni_vision": "Philosophical insight"
}"""

        ENGINE_PROMPTS["marketing"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

Generate a VIRAL marketing campaign strategy in JSON:
{
    "campaign_name": "...", "target_audience": "Detailed profile",
    "brand_positioning": "...", "hook": "Attention-grabbing hook",
    "main_copy": "200+ words with emotional triggers",
    "content_calendar": [{"day": "Day 1", "platform": "Instagram", "content_type": "Reel", "topic": "...", "cta": "..."}],
    "hashtags": ["#tag1", "#tag2", "#tag3"],
    "visual_direction": "Detailed description for designers",
    "posting_times": {"instagram": "...", "tiktok": "...", "facebook": "..."},
    "engagement_strategy": ["Strategy 1", "..."],
    "budget_allocation": {"social_ads": "40%", "influencers": "30%", "content_creation": "20%", "analytics": "10%"},
    "kpis": [{"metric": "Engagement Rate", "target": "5%"}],
    "competitive_edge": "What makes this different"
}"""

        ENGINE_PROMPTS["academic"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

Academic Research Engine with arXiv, PubMed, OpenAlex, PubChem databases.

Respond in JSON:
{
    "research_topic": "...",
    "executive_summary": "Comprehensive overview",
    "key_papers": [{"title": "...", "authors": "...", "year": "...", "source": "...", "key_finding": "...", "relevance": "..."}],
    "research_gaps": ["Gap 1", "..."],
    "methodology_review": "...",
    "future_directions": ["Direction 1", "..."],
    "practical_applications": ["Application 1", "..."],
    "cross_disciplinary_insights": "..."
}"""

        ENGINE_PROMPTS["vision"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

AI Vision Analysis Engine. Analyze and respond in JSON:
{
    "description": "Detailed visual analysis",
    "objects_detected": [...],
    "analysis": "Comprehensive interpretation",
    "recommendations": [...],
    "confidence_scores": {...}
}"""

        ENGINE_PROMPTS["brain"] = """ΑΠΑΝΤΑ ΣΤΑ ΕΛΛΗΝΙΚΑ.

NeuroAether Super Brain — Comprehensive AI Analysis.

Respond in JSON:
{
    "executive_summary": "Detailed overview (300+ words)",
    "deep_analysis": "Technical breakdown with specifics",
    "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
    "recommendations": ["Detailed recommendation 1", "..."],
    "action_items": [{"action": "...", "timeline": "...", "priority": "..."}],
    "risks": [{"risk": "...", "mitigation": "..."}],
    "opportunities": ["Opportunity 1", "..."]
}"""

        system_prompt = ENGINE_PROMPTS.get(engine_type, ENGINE_PROMPTS["brain"])

        if engine_type in ("chef", "molecular"):
            max_tokens = 12000
        elif engine_type in ("assembly", "apex"):
            max_tokens = 8000

        user_message = f"""{query}
{f'Σχέδιο: {plan}' if plan else ''}
ΑΠΑΝΤΗΣΕ ΑΠΟΚΛΕΙΣΤΙΚΑ ΣΤΑ ΕΛΛΗΝΙΚΑ. Δώσε ΜΟΝΟ JSON, χωρίς markdown."""

        if ":" in model:
            model = model.split(":")[-1]

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temp,
            max_tokens=max_tokens
        )
        result = response.choices[0].message.content
        return {
            "query": query,
            "response": result,
            "engine": engine_type,
            "model": model
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
