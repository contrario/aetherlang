"""
APEX Crypto Intelligence — Client Library
Auditable code showing exactly what data is sent to the API.

SECURITY GUARANTEE:
- Only market data and query text are sent to api.neurodoc.app
- Exchange API keys are used LOCALLY to fetch data from exchanges
- Keys are NEVER included in any outbound request to NeuroAether
"""

import os
import json
import httpx
from typing import Optional

NEURODOC_API = "https://api.neurodoc.app/aetherlang/execute"


# ═══════════════════════════════════════════════════════════════
#  LOCAL EXCHANGE DATA FETCHERS
#  These run on the USER'S machine. Keys never leave this code.
# ═══════════════════════════════════════════════════════════════

async def fetch_coingecko(coin_ids: list[str]) -> dict:
    """Free tier — no API key needed"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "24h,7d",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=15)
        return r.json() if r.status_code == 200 else {}


async def fetch_binance(symbol: str) -> dict:
    """Public endpoint — key optional for higher rate limits"""
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {"exchange": "Binance", "bid": d.get("bidPrice"), "ask": d.get("askPrice"), "volume": d.get("quoteVolume")}
    return {}


async def fetch_bybit(symbol: str) -> dict:
    """Public endpoint"""
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            items = r.json().get("result", {}).get("list", [])
            if items:
                t = items[0]
                return {"exchange": "Bybit", "bid": t.get("bid1Price"), "ask": t.get("ask1Price"), "volume": t.get("turnover24h")}
    return {}


async def fetch_kucoin(symbol: str) -> dict:
    """Public endpoint"""
    url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json().get("data", {})
            return {"exchange": "KuCoin", "bid": d.get("bestBid"), "ask": d.get("bestAsk")}
    return {}


async def fetch_mexc(symbol: str) -> dict:
    """Public endpoint"""
    url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {"exchange": "MEXC", "bid": d.get("bidPrice"), "ask": d.get("askPrice"), "volume": d.get("quoteVolume")}
    return {}


async def fetch_gateio(symbol: str) -> dict:
    """Public endpoint"""
    url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                d = data[0]
                return {"exchange": "Gate.io", "bid": d.get("highest_bid"), "ask": d.get("lowest_ask"), "volume": d.get("quote_volume")}
    return {}


# ═══════════════════════════════════════════════════════════════
#  API REQUEST BUILDER
#  This is the ONLY function that sends data to api.neurodoc.app
#  Inspect this to verify exactly what is transmitted.
# ═══════════════════════════════════════════════════════════════

def build_api_request(query: str, market_data: dict, exchange_data: list[dict], mode: str = "analysis") -> dict:
    """
    Build the exact payload sent to api.neurodoc.app.
    
    WHAT IS SENT:
    - code: AetherLang flow definition (static template)
    - query: User's natural language query + market data context
    
    WHAT IS NOT SENT:
    - No API keys
    - No credentials
    - No wallet addresses
    - No personal data
    """
    
    # Build context from locally-fetched data
    context_lines = [f"Market query: {query}", "", "LIVE MARKET DATA:"]
    for coin in market_data:
        context_lines.append(
            f"  {coin.get('symbol','?')}: ${coin.get('current_price',0):,.2f} "
            f"24h:{coin.get('price_change_percentage_24h',0):+.1f}% "
            f"MCap:${coin.get('market_cap',0)/1e9:.1f}B"
        )
    
    context_lines.append("\nEXCHANGE DATA:")
    for ex in exchange_data:
        if ex:
            context_lines.append(
                f"  {ex.get('exchange','?')}: bid={ex.get('bid')} ask={ex.get('ask')}"
            )
    
    flow_code = f'''flow CryptoAnalysis {{
  using target "neuroaether" version ">=0.3";
  input text query;
  node Apex: crypto mode="{mode}", language="en";
  output text result from Apex;
}}'''
    
    # THIS IS THE COMPLETE PAYLOAD — nothing else is sent
    payload = {
        "code": flow_code,
        "query": "\n".join(context_lines),
    }
    
    return payload


async def analyze(query: str, coin_ids: list[str], mode: str = "analysis") -> dict:
    """
    Full analysis pipeline:
    1. Fetch data LOCALLY from exchanges (keys stay local)
    2. Build payload with ONLY market data + query
    3. Send to api.neurodoc.app for AI analysis
    """
    
    # Step 1: Local data fetching (keys used here, never sent)
    market_data = await fetch_coingecko(coin_ids)
    
    symbol_map = {"bitcoin": ("BTCUSDT", "BTCUSDT", "BTC-USDT", "BTCUSDT", "BTC_USDT")}
    exchange_data = []
    for coin_id in coin_ids[:3]:
        if coin_id in symbol_map:
            syms = symbol_map[coin_id]
            exchange_data.extend([
                await fetch_binance(syms[0]),
                await fetch_bybit(syms[1]),
                await fetch_kucoin(syms[2]),
                await fetch_mexc(syms[3]),
                await fetch_gateio(syms[4]),
            ])
    
    # Step 2: Build payload (inspect this — no keys included)
    payload = build_api_request(query, market_data, exchange_data, mode)
    
    # Step 3: Send ONLY the payload to API
    async with httpx.AsyncClient() as client:
        r = await client.post(NEURODOC_API, json=payload, timeout=120)
        return r.json()


# ═══════════════════════════════════════════════════════════════
#  VERIFICATION: Run this to see exactly what would be sent
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    
    async def verify():
        """Run this to inspect the exact payload before sending"""
        market_data = await fetch_coingecko(["bitcoin"])
        exchange_data = [await fetch_binance("BTCUSDT")]
        
        payload = build_api_request("Analyze BTC", market_data, exchange_data)
        
        print("=" * 60)
        print("EXACT PAYLOAD THAT WOULD BE SENT TO api.neurodoc.app:")
        print("=" * 60)
        print(json.dumps(payload, indent=2))
        print("=" * 60)
        print("VERIFY: No API keys, credentials, or personal data above.")
        print("=" * 60)
    
    asyncio.run(verify())
