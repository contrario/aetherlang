# AetherLang Ω — AI Workflow Orchestration

> Production-grade DSL for building AI workflows with 28 node types and enterprise security.

## Overview

AetherLang Ω is a visual programming language for AI that orchestrates multi-model workflows with built-in safety, debugging, and real-time collaboration. It processes natural language queries through specialized AI engines.

## Domains

| Domain | Description | Output |
|--------|-------------|--------|
| Chef Omega | Michelin-grade recipes with HACCP, costs, MacYuFBI flavor system | Full recipe with financials |
| APEX Strategy | Nobel-level business analysis (McKinsey/HBR quality) | 9-section strategic report |
| Grand Assembly | 26 legendary AI archetypes with Gandalf Safety Veto | Multi-perspective analysis |
| Consulting | SWOT, roadmaps, KPIs with implementation phases | Strategic consulting report |
| Lab | Scientific analysis across 50 domains | Research report with risk matrix |
| Marketing | Viral campaign generation with content calendars | Campaign strategy |
| OPAP Oracle | Live Greek lottery statistics and analysis | Statistical analysis with numbers |
| Cyber | Threat assessment with defense strategies | Security intelligence report |
| Academic | Multi-source research (arXiv, PubMed, OpenAlex) | Research synthesis |

## Security Features

AetherLang includes enterprise-grade security:

- **Input Validation**: All inputs validated server-side (length limits, character filtering)
- **Injection Prevention**: Pattern detection blocks code injection, SQL injection, XSS, prompt manipulation
- **Rate Limiting**: 100 requests/hour per client with burst protection (10/10s)
- **Safety Guards**: Built-in GUARD node with STRICT/MODERATE/PERMISSIVE modes
- **Gandalf Veto**: AI safety review on Assembly outputs
- **Request Size Limits**: Max 5KB query, 10KB code, 50KB body
- **Audit Logging**: All blocked/sanitized requests logged
- **Security Headers**: X-Content-Type-Options, X-Frame-Options on all responses

## API Usage

All API interactions handled internally with proper validation:

1. **Field whitelist** — Only recognized fields accepted
2. **Length enforcement** — Query max 5000 chars, Code max 10000 chars
3. **Pattern detection** — Dangerous patterns blocked before processing
4. **Type validation** — All fields type-checked
5. **Sanitization** — Warning-level patterns neutralized

### Blocked Patterns

Automatically blocked:
- Code execution attempts (eval(), exec(), \_\_import\_\_)
- SQL injection (;DROP, ;DELETE)
- XSS (script tags)
- Template injection
- OS command injection (os.system)

## Response Structure
```json
{
  "status": "success",
  "flow": "FlowName",
  "result": "...",
  "safe": true,
  "nodes_executed": 3,
  "execution_time": "32.1s"
}
```

## Error Responses

| Code | Meaning |
|------|---------|
| 400 | Invalid input or injection detected |
| 413 | Request too large |
| 429 | Rate limit exceeded (Retry-After header included) |
| 500 | Server error |

## Rate Limits

| Tier | Limit | Burst |
|------|-------|-------|
| Free | 100 req/hour | 10 req/10s |
| BYOK | 200 req/hour | 20 req/10s |
| Enterprise | Custom | Custom |

## Languages

- **English** (default)
- **Greek** — full native support including Greeklish detection

## Technology

- **Backend**: FastAPI + Python 3.12
- **AI Models**: GPT-4o via OpenRouter
- **Hosting**: Hetzner EU (GDPR compliant)
- **Security**: Enterprise middleware with audit logging

## Links

- **Platform**: [aetherlang.neurodoc.app](https://aetherlang.neurodoc.app)
- **Status**: Production

---

*Built by NeuroAether — From Kitchen to Code*
