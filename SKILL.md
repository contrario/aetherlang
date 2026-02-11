# AetherLang Ω — AI Workflow Orchestration Skill

> Production-grade DSL for building AI workflows with 39 node types and enterprise security.

## Overview

AetherLang Ω is a domain-specific language for AI that orchestrates multi-model workflows with built-in safety, debugging, and real-time collaboration.

**IMPORTANT**: All user inputs are sanitized server-side before processing. The skill NEVER interpolates raw user input into API payloads — all input passes through validation middleware first.

## Supported Engines

| Engine | Trigger Keywords | Description |
|--------|-----------------|-------------|
| `chef` | recipe, cook, food | Michelin-grade recipes with HACCP, costs, MacYuFBI |
| `molecular` | molecular, spherification | Molecular gastronomy with Ferran Adrià techniques |
| `apex` | strategy, business, analysis | Nobel-level analysis (McKinsey/HBR quality) |
| `assembly` | debate, perspectives, council | 26 legendary AI archetypes with Gandalf Veto |
| `consulting` | consulting, SWOT, roadmap | Strategic consulting with KPIs and phases |
| `lab` | science, research, experiment | Scientific analysis across 50 domains |
| `marketing` | campaign, viral, social media | Campaign generation with content calendars |
| `oracle` | lottery, OPAP, lucky numbers | Greek lottery statistics and analysis |
| `cyber` | security, threat, vulnerability | Threat assessment with defense strategies |
| `academic` | paper, arXiv, PubMed | Multi-source research synthesis |
| `vision` | image, analyze, detect | Computer vision analysis |
| `brain` | think, analyze, comprehensive | General AI analysis |

## API Endpoint
```
POST https://api.neurodoc.app/aetherlang/execute
Content-Type: application/json
```

### Request Format
```json
{
  "code": "<aetherlang_flow>",
  "query": "<sanitized_user_input>"
}
```

### Building Flows
```
flow <FlowName> {
  using target "neuroaether" version ">=0.2";
  input text query;
  node <NodeName>: <engine_type> <parameters>;
  output text result from <NodeName>;
}
```

#### Chef Flow
```
flow Chef {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Chef: chef cuisine="auto", difficulty="medium", servings=4, language="el";
  output text recipe from Chef;
}
```

#### APEX Strategy Flow
```
flow Strategy {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="MODERATE";
  node Planner: plan steps=4;
  node LLM: apex model="gpt-4o", temp=0.7;
  Guard -> Planner -> LLM;
  output text report from LLM;
}
```

#### Assembly Flow
```
flow Assembly {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="MODERATE";
  node Council: assembly model="gpt-4o", temp=0.9;
  Guard -> Council;
  output text report from Council;
}
```

## Security Architecture

### Input Validation (Server-Side)
- **Field whitelist**: Only `code`, `query`, `language` fields accepted
- **Length enforcement**: Query max 5000 chars, Code max 10000 chars, Body max 50KB
- **Type validation**: All fields type-checked before processing
- **Character filtering**: Non-printable characters stripped

### Injection Prevention
All inputs pass through pattern detection that blocks:
- Code execution: `eval()`, `exec()`, `__import__()`, `compile()`
- SQL injection: `; DROP`, `; DELETE`, `UNION SELECT`
- XSS: `<script>`, `javascript:`, `onerror=`
- Template injection: `{{`, `${`, `<%`
- OS commands: `os.system`, `subprocess`, `; rm`, `| cat`
- Prompt manipulation: `ignore previous`, `system prompt`

### Rate Limiting
| Tier | Limit | Burst |
|------|-------|-------|
| Free | 100 req/hour | 10 req/10s |
| BYOK | 200 req/hour | 20 req/10s |

### Safety Guards
- **GUARD node**: STRICT/MODERATE/PERMISSIVE content filtering
- **Gandalf Veto**: AI safety review on Assembly outputs
- **Audit logging**: All blocked and sanitized requests logged

## Response Structure
```json
{
  "status": "success",
  "flow_name": "Chef",
  "result": {
    "outputs": {
      "recipe": {
        "response": "{ structured JSON }",
        "engine": "chef",
        "model": "gpt-4o"
      }
    },
    "duration_seconds": 58.9
  },
  "usage": { "tier": "free", "remaining": 8 }
}
```

## Error Responses

| Code | Meaning |
|------|---------|
| 400 | Invalid input or injection detected |
| 413 | Request too large |
| 429 | Rate limit exceeded |
| 500 | Server error |

## Languages

- **English** (default)
- **Greek** (Ελληνικά) — add `language="el"` to any node

## Technology

- **Backend**: FastAPI + Python 3.12
- **AI Models**: GPT-4o via OpenAI
- **Parser**: 39 node types with validation
- **Hosting**: Hetzner EU (GDPR compliant)
- **Security**: Multi-layer middleware with audit logging

## Links

- **Web**: [neurodoc.app/aether-nexus-omega-dsl](https://neurodoc.app/aether-nexus-omega-dsl)
- **GitHub**: [github.com/contrario/aetherlang](https://github.com/contrario/aetherlang)
- **Status**: Production ✅

---
*Built by NeuroAether — From Kitchen to Code* 🧠
