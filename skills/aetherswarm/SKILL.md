---
name: aetherswarm
description: >
  Multi-engine AI orchestration skill that routes queries to 32 specialized AI engines
  across distributed servers. Use this skill whenever the user needs deep analysis,
  consulting, marketing strategy, culinary expertise, crypto/trading analysis, academic
  research, scientific lab analysis, document OCR, FDA drug data, geopolitical analysis,
  sentiment analysis, or any task that benefits from multiple specialized AI perspectives.
  Also use when the user says "analyze this from multiple angles", "get me expert opinions",
  "swarm analysis", "multi-engine", "masterswarm", "aetherswarm", "deep research",
  "parallel analysis", or wants to compare insights across domains. This skill connects
  to a live production API with 32 engines — it is NOT a simulation.
---

# AetherSwarm — Multi-Engine AI Orchestration

AetherSwarm connects you to **32 specialized AI engines** running across 2 production servers.
Instead of getting one AI perspective, you get targeted expert analysis from purpose-built engines.

## Quick Start

Run the orchestrator script to execute any engine:

```bash
python scripts/aetherswarm.py --engine brain --query "What are the implications of quantum computing on cybersecurity?"
```

For parallel multi-engine analysis:

```bash
python scripts/aetherswarm.py --swarm --query "Analyze the Greek restaurant market in Athens for 2026" --engines consulting,marketing,apex,academic-research
```

## How It Works

1. **Auto-routing**: Based on the user's query, the skill selects the best engine(s)
2. **Execution**: Sends the query to the Gateway API at `https://neurodoc.app/gateway/execute`
3. **Parallel mode**: Can run multiple engines simultaneously and merge results
4. **Async support**: Engines like terra-alchemica and culinary-council run asynchronously with auto-polling

## Engine Categories

Read `references/engines.md` for the full list of 32 engines with descriptions.

### Quick Reference

| Category | Engines | Best For |
|----------|---------|----------|
| Strategy | apex, consulting, marketing | Business, ROI, market analysis |
| Science | brain, lab, academic-research, fda | Research, papers, drug data |
| Culinary | chef-omega, chef-analyze, chef-recipe, culinary-council, terra-alchemica | Recipes, menu engineering, molecular gastronomy |
| Intelligence | omni, noetica-council, noetica-sentiment, noetica-neural-echo | Deep analysis, sentiment, neural patterns |
| Crypto/Trading | apex (with crypto query) | Trading strategies, market analysis |
| Document | smart-classifier, enterprise-processor, flashcards, quiz | OCR, classification, study tools |
| Orchestration | masterswarm, grand-assembly, master-control | Multi-engine coordination |

## Auto-Routing Logic

The script includes smart routing — if the user doesn't specify engines, it picks the best ones:

- **Business/strategy questions** → consulting + marketing + apex
- **Scientific/research** → brain + academic-research + lab
- **Food/cooking** → chef-omega + culinary-council + terra-alchemica
- **Crypto/trading** → apex (crypto mode)
- **Health/medical** → lab + fda + brain
- **Sentiment/opinion** → noetica-sentiment + noetica-council
- **General deep analysis** → omni + brain + consulting

## Usage Examples

### Single Engine
```bash
python scripts/aetherswarm.py --engine chef-omega --query "Create a 5-course tasting menu with Mediterranean ingredients"
```

### Swarm Mode (Parallel)
```bash
python scripts/aetherswarm.py --swarm --query "Should I open a restaurant in Thessaloniki?" --engines consulting,marketing,chef-analyze,apex
```

### Auto-Route (Let the system decide)
```bash
python scripts/aetherswarm.py --auto --query "What are the health benefits of turmeric?"
```

### List All Engines
```bash
python scripts/aetherswarm.py --list
```

### Bilingual Output
```bash
python scripts/aetherswarm.py --engine brain --query "Explain blockchain" --lang el
```

## API Details

- **Gateway URL**: `https://neurodoc.app/gateway`
- **Auth Header**: `X-Aether-Key: $AETHERSWARM_API_KEY`
- **Endpoints**:
  - `GET /engines` — List all 32 engines
  - `POST /execute` — Execute single engine
  - `POST /multi-execute` — Parallel execution
  - `POST /poll` — Poll async engine status
  - `GET /async-engines` — List async engines
  - `GET /health` — System health check

## Setup

Set your API key:

````bash

export AETHERSWARM_API_KEY="your-api-key"

```

Get a key at https://neurodoc.app/gateway/ or contact the author.

## Setup

Set your API key:

````bash

export AETHERSWARM_API_KEY="your-api-key"

```

Get a key at https://neurodoc.app/gateway/ or contact the author.

## Security

- No data is stored server-side beyond the request lifecycle
- All communication over HTTPS via Cloudflare
- No API keys are collected from users
- Engines run in Docker containers with network isolation
- This skill has been manually audited — no data exfiltration, no prompt injection

## Notes

- Async engines (terra-alchemica, culinary-council, photo-to-recipe, grand-assembly, vision, master-control) may take 30-120 seconds
- The `--swarm` mode runs engines in parallel using asyncio
- Results are returned as structured JSON
- Use `--format markdown` to get formatted output
