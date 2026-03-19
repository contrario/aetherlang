# 🌀 AetherSwarm — Multi-Engine AI Orchestration Skill

> Route queries to **32 specialized AI engines** across distributed servers. Get consulting-grade analysis, scientific research, culinary expertise, and more — all from a single skill.

[![Engines](https://img.shields.io/badge/engines-32-blue)]()
[![Servers](https://img.shields.io/badge/servers-2-green)]()
[![Categories](https://img.shields.io/badge/categories-10-purple)]()
[![Security](https://img.shields.io/badge/security-audited-brightgreen)]()

## What Makes This Different

While most skills give you **one AI perspective**, AetherSwarm gives you access to **32 purpose-built engines** spanning:

- 🏢 **Business Strategy** — Consulting, Marketing, APEX (ROI/Trading)
- 🔬 **Science & Research** — Brain, Lab, Academic Research, FDA
- 👨‍🍳 **Culinary Intelligence** — Chef Omega (23yr pro chef), Molecular Gastronomy, Culinary Council
- 🧠 **Deep Intelligence** — OMNI, Noetica (8 neural archetypes), Sentiment Analysis
- 📄 **Document Processing** — OCR, Classification, Enterprise Processing
- 🎓 **Education** — Auto-generated Flashcards & Quizzes
- 🎯 **Orchestration** — MasterSwarm parallel analysis, Grand Assembly (26 archetypes)

## Install

### Claude Code
```bash
# Copy to your skills directory
cp -r aetherswarm ~/.claude/skills/
```

### OpenClaw / ClawHub
```bash
claw install aetherswarm
```

## Usage

### Auto Mode (recommended)
```bash
python scripts/aetherswarm.py --auto --query "Should I open a tech startup in Greece?"
```
The system auto-selects the best engines based on your query.

### Single Engine
```bash
python scripts/aetherswarm.py --engine consulting --query "Market analysis for SaaS in Europe"
```

### Swarm Mode (parallel execution)
```bash
python scripts/aetherswarm.py --swarm --engines brain,consulting,marketing,apex --query "AI trends 2026"
```

### List All 32 Engines
```bash
python scripts/aetherswarm.py --list
```

## Architecture

```
Your Query
    │
    ▼
┌─────────────────┐
│  AetherSwarm     │  Smart routing based on keywords
│  Orchestrator    │  Auto-selects best engine(s)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Server A│ │Server B│
│ 9 eng. │ │23 eng. │
│neurodoc│ │omnimus │
└────────┘ └────────┘
```

## Engine Categories

| Category | Count | Highlight |
|----------|-------|-----------|
| Strategy & Business | 3 | McKinsey-level consulting + APEX trading |
| Science & Research | 4 | Academic papers, FDA drug data, lab analysis |
| Culinary | 6 | Pro chef AI, molecular gastronomy, council |
| Intelligence | 5 | Multi-archetype neural analysis |
| Document | 3 | OCR, classification, enterprise processing |
| Education | 2 | Flashcards & quiz generation |
| Orchestration | 3 | Parallel multi-engine coordination |
| Utility | 2 | PDF reports, Greek lottery data |

## Security

✅ No data stored beyond request lifecycle
✅ HTTPS via Cloudflare
✅ No user API keys collected
✅ Docker-isolated engine execution
✅ Manually audited — no exfiltration, no prompt injection
✅ No dependencies beyond Python stdlib

## Requirements

- Python 3.8+
- Internet connection (engines run on remote servers)
- No API keys needed — the skill connects to a public gateway

## License

MIT

## Author

Built by **Hlia** — From Kitchen to Code. 23 years professional chef, now building AI platforms.

- 🌐 [neurodoc.app](https://neurodoc.app)
- 🌐 [omnimusmind.com](https://omnimusmind.com)
- 🌐 [aetherlang.net](https://aetherlang.net)
