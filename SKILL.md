# AetherLang Ω — AI Workflow Orchestration Skill

> Production-grade DSL for building AI workflows with 39 node types and enterprise security.

**Source Code**: [github.com/contrario/aetherlang](https://github.com/contrario/aetherlang)
**Homepage**: [neurodoc.app/aether-nexus-omega-dsl](https://neurodoc.app/aether-nexus-omega-dsl)
**Author**: NeuroAether (info@neurodoc.app)
**License**: MIT

## Privacy & Data Handling

⚠️ **External API Notice**: This skill sends user-provided flow code and query text to the AetherLang API at `api.neurodoc.app` for processing. By using this skill, you consent to this data transmission.

- **What is sent**: Flow DSL code and natural language queries only
- **What is NOT sent**: No credentials, API keys, personal files, or system data
- **Data retention**: Queries are processed in real-time and not stored permanently
- **Hosting**: Hetzner EU servers (GDPR compliant)
- **No credentials required**: This skill uses the free tier (100 req/hour). No API keys needed.

Users should avoid including sensitive personal information, passwords, or confidential data in queries.

## Overview

AetherLang Ω is a domain-specific language for AI that orchestrates multi-model workflows with built-in safety, debugging, and real-time collaboration.

All user inputs are validated and sanitized server-side before processing. The security middleware source code is publicly available in the [GitHub repository](https://github.com/contrario/aetherlang/blob/main/aetherlang/middleware/security.py).

## Supported Engines

| Engine | Trigger Keywords | Description |
|--------|-----------------|-------------|
| `chef` | recipe, cook, food | Michelin-grade recipes with HACCP, costs, MacYuFBI |
| `molecular` | molecular, spherification | Molecular gastronomy techniques |
| `apex` | strategy, business, analysis | Nobel-level analysis (McKinsey/HBR quality) |
| `assembly` | debate, perspectives, council | 26 AI archetypes with Gandalf Veto |
| `consulting` | consulting, SWOT, roadmap | Strategic consulting with KPIs |
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
  "query": "<user_input>"
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

## Security Architecture

Security middleware source code: [middleware/security.py](https://github.com/contrario/aetherlang/blob/main/aetherlang/middleware/security.py)

### Input Validation (Server-Side)
- **Field whitelist**: Only `code`, `query`, `language` fields accepted
- **Length enforcement**: Query max 5000 chars, Code max 10000 chars, Body max 50KB
- **Type validation**: All fields type-checked before processing

### Injection Prevention
Blocks: code execution (`eval`, `exec`), SQL injection, XSS, template injection, OS commands, prompt manipulation.

### Rate Limiting
- **Free tier**: 100 req/hour, 10 req/10s burst (no credentials needed)

### Safety Guards
- **GUARD node**: STRICT/MODERATE/PERMISSIVE content filtering
- **Gandalf Veto**: AI safety review on Assembly outputs
- **Audit logging**: All blocked requests logged

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
  }
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

- **Backend**: FastAPI + Python 3.12 ([source](https://github.com/contrario/aetherlang))
- **AI Models**: GPT-4o via OpenAI
- **Parser**: 39 node types with validation
- **Hosting**: Hetzner EU (GDPR compliant)

---
*Built by NeuroAether — From Kitchen to Code* 🧠
