---
name: aetherlang
description: Execute AI workflow orchestration flows using the AetherLang Ω DSL. Run multi-step AI pipelines for recipes, business strategy, market analysis, molecular gastronomy, research, and more via natural language or DSL code.
metadata: {"openclaw": {"emoji": "⚡", "homepage": "https://neurodoc.app/aether-nexus-omega-dsl"}}
---

# AetherLang Ω — AI Workflow Orchestration Skill

AetherLang Ω is a domain-specific language (DSL) for orchestrating multi-step AI workflows. Instead of single prompts, it chains specialized AI nodes (Guard → Plan → Chef → Summarize) into powerful pipelines.

## What It Does

Execute AI workflow flows via the AetherLang API. Each flow chains multiple specialized nodes:

- **chef**: Michelin-level recipe generation with food costing, HACCP safety, and MacYuFBI flavor balance
- **molecular**: APEIRON Molecular Architect — scientific gastronomy with physics engines and FDA safety checks
- **apex**: Nobel-level business strategy with ROI/NPV/IRR projections and risk matrices
- **oracle**: OMNI-COMPUTE adversarial forecasting engine with Nash equilibrium simulation
- **market**: McKinsey-level market intelligence with TAM/SAM/SOM and Porter's 5 Forces
- **research**: Deep research analysis with confidence levels and cited sources
- **assembly**: GAIA Brain 12-neuron multi-agent system for multi-perspective analysis
- **consult**: NEXUS-7 architectural blueprinting for system design
- **balance**: Nutritional biochemistry and flavor science analysis
- **vision**: Culinary presentation and food styling analysis

## How To Use

### Quick Flows (Natural Language)

When the user asks for any of the above domains, construct and execute a flow:
```bash
curl -s --max-time 120 -X POST https://neurodoc.app/api/aetherlang/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "flow Q { using target \"neuroaether\" version \">=0.2\"; input text query; node G: guard mode=\"MODERATE\"; node C: chef cuisine=\"USER_CUISINE\", difficulty=\"USER_DIFFICULTY\", servings=USER_SERVINGS; G -> C; output text r from C; }",
    "query": "USER_QUERY"
  }'
```

Replace USER_CUISINE, USER_DIFFICULTY, USER_SERVINGS, and USER_QUERY with the user's request.

### Domain Templates

**Recipe Generation:**
```
flow Recipe {
  using target "neuroaether" version ">=0.2";
  input text query;
  node G: guard mode="MODERATE";
  node C: chef cuisine="CUISINE", difficulty="DIFFICULTY", servings=SERVINGS;
  G -> C;
  output text r from C;
}
```

**Business Strategy:**
```
flow Strategy {
  using target "neuroaether" version ">=0.2";
  input text query;
  node G: guard mode="STRICT";
  node R: research depth="comprehensive";
  node A: apex mode="standard";
  G -> R -> A;
  output text r from A;
}
```

**Market Analysis:**
```
flow Market {
  using target "neuroaether" version ">=0.2";
  input text query;
  node G: guard mode="MODERATE";
  node M: market scope="SCOPE", timeframe="TIMEFRAME";
  G -> M;
  output text r from M;
}
```

**Forecasting:**
```
flow Forecast {
  using target "neuroaether" version ">=0.2";
  input text query;
  node G: guard mode="MODERATE";
  node O: oracle timeframe="TIMEFRAME";
  G -> O;
  output text r from O;
}
```

**Full Consulting Pipeline:**
```
flow FullConsult {
  using target "neuroaether" version ">=0.2";
  input text query;
  node G: guard mode="STRICT";
  node R: research depth="comprehensive";
  node C: consult domain="business", framework="SWOT";
  node M: market scope="global", timeframe="2026";
  node A: apex mode="standard";
  G -> R -> C -> M -> A;
  output text r from A;
}
```

## Response Handling

The API returns JSON:
```json
{
  "status": "success",
  "result": {
    "outputs": {
      "r": {
        "output": "... the AI-generated content ..."
      }
    }
  }
}
```

Extract `result.outputs.r.output` for the final content. If the response is long, summarize key points for the user.

## Important Notes

- The API endpoint is: `https://neurodoc.app/api/aetherlang/execute`
- Timeout: set --max-time to 120 seconds (complex flows take 15-60s)
- The API is free during beta
- Flows are executed server-side; no API keys needed from the user
- All 39 node types are available: guard, plan, llm, summarize, extract, translate, classify, sentiment, compare, merge, template, code, validate, format, enrich, filter, route, transform, score, rank, cluster, embed, search, cache, log, alert, webhook, store, chef, molecular, balance, vision, assembly, oracle, apex, research, consult, market, visualizer

## Examples

User: "Make me a Greek moussaka recipe"
→ Use chef node with cuisine="greek"

User: "Analyze the European AI market"
→ Use market node with scope="europe"

User: "Should I start an AI SaaS company?"
→ Use full consulting pipeline (research → consult → market → apex)

User: "Predict AI regulation trends for 2027"
→ Use oracle node with timeframe="24months"

User: "Create a molecular gastronomy dish with olive oil"
→ Use molecular node with complexity="advanced"

## Links

- Live Demo: https://neurodoc.app/aether-nexus-omega-dsl
- GitHub: https://github.com/contrario/aetherlang
- Documentation: https://github.com/contrario/aetherlang#readme
