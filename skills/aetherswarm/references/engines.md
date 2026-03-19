# AetherSwarm Engine Registry

## 32 Specialized AI Engines across 2 Servers

### Server A — neurodoc-server (9 engines)

| ID | Category | Description |
|----|----------|-------------|
| masterswarm | orchestration | Parallel multi-engine document analysis with AetherLang DSL |
| smart-classifier | document | AI document classification and categorization |
| aetherlang-dsl | orchestration | Custom Domain-Specific Language for AI workflows |
| enterprise-processor | document | Enterprise-grade document processing pipeline |
| memory-summary | intelligence | Conversation memory and knowledge summarization |
| memory-evolution | intelligence | Adaptive memory evolution and learning system |
| flashcards | education | Auto-generate study flashcards from any text |
| quiz | education | Generate quiz questions with answers from content |
| lab-analysis | science | Scientific laboratory data analysis |

### Server B — omnimusmind (23 engines)

| ID | Category | Description |
|----|----------|-------------|
| apex | strategy | Nobel-level strategic analysis with ROI projections, crypto trading |
| omni | intelligence | Unified OMNI intelligence — general deep analysis |
| brain | science | NeuroAether Super Brain — research and knowledge synthesis |
| chef-omega | culinary | Professional culinary AI with 23 years chef expertise |
| chef-analyze | culinary | Dish analysis, nutritional breakdown, improvement suggestions |
| chef-recipe | culinary | Recipe generation with ingredient-first doctrine |
| culinary-council | culinary | ⏳ ASYNC — Multi-agent culinary council deliberation |
| terra-alchemica | culinary | ⏳ ASYNC — Molecular gastronomy and food science |
| vision | intelligence | ⏳ ASYNC — Computer vision and image analysis |
| photo-to-recipe | culinary | ⏳ ASYNC — Photo to recipe with AI vision |
| consulting | strategy | McKinsey-level business consulting analysis |
| marketing | strategy | Marketing strategy, branding, go-to-market planning |
| lab | science | Deep scientific analysis laboratory |
| fda | science | FDA drug database, adverse events, food recalls |
| academic-research | science | Academic paper-style research and citations |
| noetica-council | intelligence | Multi-archetype council with 8 neural perspectives |
| noetica-sentiment | intelligence | Sentiment analysis with emotional depth |
| noetica-neural-echo | intelligence | Neural echo pattern recognition |
| noetica-production | intelligence | Production-grade Noetica analysis |
| lucky | utility | Greek OPAP lottery data (KINO, TZOKER, LOTTO) |
| neuropress | utility | PDF report generation engine |
| grand-assembly | orchestration | ⏳ ASYNC — 26-archetype grand assembly deliberation |
| master-control | orchestration | ⏳ ASYNC — Master control orchestration |

### Async Engines (require polling)

These engines start a background task and return a `session_id`. The skill auto-polls every 2.5 seconds until completion:

- `terra-alchemica` — Molecular gastronomy synthesis (30-90s)
- `culinary-council` — Multi-agent deliberation (30-120s)
- `photo-to-recipe` — Vision + recipe generation (25-60s)
- `grand-assembly` — Full assembly with 26 archetypes (60-180s)
- `vision` — Image analysis pipeline (15-45s)
- `master-control` — Full orchestration (60-120s)

### Engine Selection Guide

**For business decisions:** `consulting` → structured analysis, `marketing` → go-to-market, `apex` → financial/ROI

**For science/research:** `brain` → broad knowledge, `academic-research` → paper-style, `lab` → data analysis, `fda` → health/drug data

**For food/culinary:** `chef-omega` → full recipes, `chef-analyze` → dish evaluation, `terra-alchemica` → molecular, `culinary-council` → multi-perspective

**For deep analysis:** `omni` → unified intelligence, `noetica-council` → multi-archetype, `noetica-sentiment` → emotional analysis

**For orchestration:** `masterswarm` → parallel engines, `grand-assembly` → full archetype council, `master-control` → meta-orchestration
