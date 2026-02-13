# APEX Crypto Intelligence — Multi-Exchange Trading Analysis Skill

> Institutional-grade crypto market analysis across 5 exchanges with AI-powered Hyper-Council verdicts and hedge fund-quality PDF reports.

**Source Code**: [github.com/contrario/aetherlang](https://github.com/contrario/aetherlang)
**Homepage**: [neurodoc.app/aether-nexus-omega-dsl](https://neurodoc.app/aether-nexus-omega-dsl)
**Author**: NeuroAether (info@neurodoc.app)
**License**: MIT

---

## Privacy & Data Handling

⚠️ **BYOK (Bring Your Own Keys)**: This skill requires the user to provide their own exchange API keys. Keys are used exclusively for read-only market data retrieval and are never stored, logged, or transmitted to any third party.

⚠️ **External API Notice**: This skill sends analysis queries to the NeuroAether API at `api.neurodoc.app` for AI processing. Only market data and query text are transmitted — never API keys or credentials.

- **What is sent**: Market data queries and natural language analysis requests
- **What is NOT sent**: Exchange API keys, credentials, personal data, wallet addresses
- **Data retention**: Queries are processed in real-time and not stored
- **Hosting**: Hetzner EU servers (GDPR compliant)

**CRITICAL**: Users should configure exchange API keys with **READ-ONLY permissions**. Never enable withdrawal or trading permissions for keys used with this skill.

---

## Overview

APEX Crypto Intelligence provides real-time multi-exchange crypto market data, cross-exchange price comparison with arbitrage detection, and AI-powered institutional analysis through a Hyper-Council of 5 specialized AI agents.

### Key Features

1. **Cross-Exchange Scanner** — Live bid/ask from Binance, Bybit, KuCoin, MEXC, Gate.io
2. **Arbitrage Detection** — Automatic spread analysis across all 5 exchanges
3. **APEX Hyper-Council Analysis** — 5 AI agents (Macro CIO, Quant Research, Risk Officer Damocles, Execution Architect, Regime Classifier)
4. **Trading Blueprint PDF** — Hedge fund-grade reports with SWOT, Radar charts, PnL projections, Implementation Roadmap
5. **Multi-coin Support** — BTC, ETH, SOL, XRP, DOGE, ADA, DOT, AVAX, MATIC, BNB, LTC, LINK, TRX, SHIB, SUI, APT, TON, NEAR, UNI, PEPE

---

## Configuration (BYOK)

Users provide their own API keys via environment variables. All keys are optional — the skill works with CoinGecko free data by default, and each exchange is additive.

### Required Environment Variables

None required. The skill works without any keys using CoinGecko free tier.

### Optional Environment Variables

| Variable | Exchange | Purpose |
|----------|----------|---------|
| `BINANCE_API_KEY` | Binance | Market data, orderbook |
| `BINANCE_API_SECRET` | Binance | API authentication |
| `BYBIT_API_KEY` | Bybit | Market data, orderbook |
| `BYBIT_API_SECRET` | Bybit | API authentication |
| `KUCOIN_API_KEY` | KuCoin | Market data, orderbook |
| `KUCOIN_API_SECRET` | KuCoin | API authentication |
| `MEXC_API_KEY` | MEXC | Market data, orderbook |
| `MEXC_API_SECRET` | MEXC | API authentication |
| `GATEIO_API_KEY` | Gate.io | Market data, orderbook |
| `GATEIO_API_SECRET` | Gate.io | API authentication |

**Security Note**: Always create API keys with **read-only** permissions. This skill never executes trades, transfers, or withdrawals.

---

## API Endpoints

### 1. Live Market Data + Cross-Exchange Scanner
```
POST https://api.neurodoc.app/aetherlang/execute
Content-Type: application/json
```
```json
{
  "code": "flow CryptoScan {\n  using target \"neuroaether\" version \">=0.3\";\n  input text query;\n  node Scanner: crypto exchanges=\"all\", language=\"en\";\n  output text result from Scanner;\n}",
  "query": "BTC ETH SOL"
}
```

**Response includes:**
- CoinGecko market data (price, 24h/7d change, MCap, volume, ATH)
- Per-exchange bid/ask/spread/volume from configured exchanges
- Arbitrage opportunities with percentage and absolute spread

### 2. APEX Hyper-Council Analysis
```json
{
  "code": "flow ApexAnalysis {\n  using target \"neuroaether\" version \">=0.3\";\n  input text query;\n  node Apex: crypto mode=\"analysis\", language=\"en\";\n  output text result from Apex;\n}",
  "query": "Full APEX analysis for BTC ETH SOL"
}
```

**Response includes:**
- Market regime classification (BULL/BEAR/CHOP/TRANSITION)
- Per-coin verdict (LONG/SHORT/NEUTRAL/WAIT) with conviction level
- Support/Resistance levels
- Hyper-Council views (Macro, Quant, Risk Damocles, Regime)
- Actionable trading plan with entry/exit/risk management

### 3. Trading Blueprint PDF
```json
{
  "code": "flow Blueprint {\n  using target \"neuroaether\" version \">=0.3\";\n  input text query;\n  node Report: crypto mode=\"blueprint\", language=\"en\";\n  output text result from Report;\n}",
  "query": "Generate trading blueprint for BTC"
}
```

**Response includes downloadable PDF with:**
- Executive Summary
- SWOT Analysis (chart)
- Projected PnL Profile (bar chart)
- Strategy Capability Radar (radar chart)
- Hyper-Council Agent Reports (5 agents with sentiment/weight/reasoning)
- Consensus Engine Score
- Implementation Roadmap

---

## Supported Exchanges

| Exchange | Data Available | Auth Required |
|----------|---------------|---------------|
| CoinGecko | Price, MCap, Volume, ATH, 24h/7d change | No (free tier) |
| Binance | Bid/Ask, Spread, 24h Volume, High/Low | Optional |
| Bybit | Bid/Ask, Spread, 24h Volume, High/Low | Optional |
| KuCoin | Bid/Ask, Spread, Volume | Optional |
| MEXC | Bid/Ask, Spread, 24h Volume, Trades | Optional |
| Gate.io | Bid/Ask, Spread, 24h Volume, Change% | Optional |

---

## Hyper-Council Agents

| Agent | Role | Weight Range | Can Veto |
|-------|------|-------------|----------|
| MACRO | Global Macro CIO | -100 to +100 | No |
| QUANT | Head of Quant Research | -100 to +100 | No |
| STATS | Chief Statistician | -100 to +100 | No |
| RISK (Damocles) | Chief Risk Officer | -100 to +100 | **Yes** |
| EXECUTION | Execution Architect | 0 (INFO) | No |

### Consensus Engine

- Raw score = sum of all agent weights
- Status: `ALPHA_GO` (strong buy) | `HOLD` | `WAIT` | `VETOED` (Damocles veto)
- Veto: If RISK agent sentiment = "VETO", trade is blocked regardless of score

---

## Security Architecture

Source code: [github.com/contrario/aetherlang](https://github.com/contrario/aetherlang/blob/main/aetherlang/middleware/security.py)

### Key Security Principles
- **BYOK**: User keys stay on user's machine, never transmitted to NeuroAether
- **Read-only**: Skill only reads market data, never executes trades
- **No storage**: API keys are used per-request and never persisted server-side
- **Input validation**: All queries sanitized, max 5000 chars
- **Rate limiting**: 100 req/hour free tier

### What This Skill Does NOT Do
- ❌ Execute trades or place orders
- ❌ Transfer funds or make withdrawals
- ❌ Store or log API keys
- ❌ Access wallet balances (unless explicitly requested)
- ❌ Provide financial advice (analysis only, with disclaimers)

---

## Response Structure
```json
{
  "status": "success",
  "result": {
    "market_data": { "coins": [...] },
    "exchange_data": {
      "binance": { "bid": 66144.87, "ask": 66144.88, "volume_usdt": 1639000000 },
      "bybit": { "bid": 66142.50, "ask": 66142.60 },
      "kucoin": { "bid": 66144.80, "ask": 66144.90 },
      "mexc": { "bid": 66133.30, "ask": 66138.95 },
      "gateio": { "bid": 66151.70, "ask": 66151.80 }
    },
    "arbitrage": {
      "best_buy": "MEXC",
      "best_sell": "Gate.io",
      "spread_pct": 0.019,
      "spread_usd": 12.75
    },
    "analysis": { "regime": "BULLISH", "verdict": "HOLD", "consensus_score": 72 }
  }
}
```

## Error Responses

| Code | Meaning |
|------|---------|
| 400 | Invalid input |
| 429 | Rate limit exceeded |
| 500 | Server error |

---

## Languages

- **English** (default)
- **Greek** (Ελληνικά) — add `language="el"`

## Technology

- **Backend**: FastAPI + Python 3.12 ([source](https://github.com/contrario/aetherlang))
- **AI Models**: GPT-4o via OpenAI
- **Data Sources**: CoinGecko, Binance, Bybit, KuCoin, MEXC, Gate.io
- **PDF Engine**: WeasyPrint + Matplotlib
- **Hosting**: Hetzner EU (GDPR compliant)

---

## Disclaimer

⚠️ This skill provides AI-generated market analysis for educational and informational purposes only. It is NOT financial advice. Cryptocurrency trading involves significant risk. Always conduct your own research (DYOR) and consult with a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

---
*Built by NeuroAether — Institutional Intelligence for Everyone* 🧠📊
