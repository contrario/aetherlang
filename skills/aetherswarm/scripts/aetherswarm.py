import os
#!/usr/bin/env python3
"""
AetherSwarm — Multi-Engine AI Orchestration
Routes queries to 32 specialized AI engines across distributed servers.
"""

import argparse
import asyncio
import json
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

GATEWAY = "https://neurodoc.app/gateway"
AUTH_HEADERS = {"Content-Type": "application/json"}
AETHER_KEY = os.environ.get("AETHERSWARM_API_KEY", "")
if not AETHER_KEY:
    print("ERROR: Set AETHERSWARM_API_KEY environment variable")
    print("  export AETHERSWARM_API_KEY=your_key_here")
    sys.exit(1)

# ── Async engines that need polling ──────────────────────────────────────────
ASYNC_ENGINES = [
    "terra-alchemica", "culinary-council", "photo-to-recipe",
    "grand-assembly", "vision", "master-control"
]

# ── Smart routing: keyword → engine sets ─────────────────────────────────────
ROUTING = {
    "business":    ["consulting", "marketing", "apex"],
    "strategy":    ["consulting", "apex", "marketing"],
    "restaurant":  ["consulting", "marketing", "chef-analyze"],
    "startup":     ["consulting", "marketing", "apex"],
    "investment":  ["apex", "consulting", "brain"],
    "crypto":      ["apex"],
    "bitcoin":     ["apex"],
    "trading":     ["apex"],
    "recipe":      ["chef-omega", "chef-recipe"],
    "cook":        ["chef-omega", "chef-analyze"],
    "menu":        ["chef-omega", "culinary-council"],
    "food":        ["chef-omega", "chef-analyze", "culinary-council"],
    "molecular":   ["terra-alchemica"],
    "gastronomy":  ["terra-alchemica", "culinary-council"],
    "health":      ["lab", "fda", "brain"],
    "medical":     ["lab", "fda", "brain"],
    "drug":        ["fda", "lab"],
    "science":     ["brain", "academic-research", "lab"],
    "research":    ["academic-research", "brain", "consulting"],
    "academic":    ["academic-research", "brain"],
    "sentiment":   ["noetica-sentiment", "noetica-council"],
    "opinion":     ["noetica-sentiment", "noetica-council"],
    "geopolitical": ["noetica-council", "brain", "consulting"],
    "cybersecurity": ["brain", "lab", "consulting"],
    "ai":          ["brain", "academic-research"],
    "technology":  ["brain", "consulting", "academic-research"],
    "marketing":   ["marketing", "consulting"],
    "branding":    ["marketing", "consulting"],
    "document":    ["smart-classifier", "enterprise-processor"],
    "ocr":         ["smart-classifier"],
    "study":       ["flashcards", "quiz"],
    "learn":       ["flashcards", "quiz", "brain"],
}

DEFAULT_ENGINES = ["omni", "brain", "consulting"]


def api_call(endpoint, method="GET", data=None, timeout=120):
    """Make HTTP request to Gateway API."""
    url = f"{GATEWAY}/{endpoint}"
    req = Request(url, headers=AUTH_HEADERS, method=method)
    if data:
        body = json.dumps(data).encode("utf-8")
        req.data = body
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_engines():
    """List all available engines."""
    result = api_call("engines")
    if isinstance(result, list):
        print(f"\n{'='*70}")
        print(f"  AETHERSWARM — {len(result)} AI Engines Available")
        print(f"{'='*70}\n")
        cats = {}
        for e in result:
            cat = e.get("category", "other")
            cats.setdefault(cat, []).append(e)
        for cat, engines in sorted(cats.items()):
            print(f"  [{cat.upper()}]")
            for e in engines:
                async_tag = " ⏳ASYNC" if e["id"] in ASYNC_ENGINES else ""
                srv = e.get("server", "?")
                print(f"    {e['id']:30s} SRV-{srv}  {e.get('description','')[:50]}{async_tag}")
            print()
        print(f"{'='*70}")
        print(f"  Total: {len(result)} engines | Server A: {sum(1 for e in result if e.get('server')=='A')} | Server B: {sum(1 for e in result if e.get('server')=='B')}")
        print(f"  Async: {len(ASYNC_ENGINES)} engines (require polling)")
        print(f"{'='*70}\n")
    else:
        print(f"Error: {result}")


def execute_engine(engine_id, query, lang="en", timeout=120):
    """Execute a single engine."""
    payload = {"query": query, "language": lang}
    if engine_id == "brain":
        payload = {"question": query, "language": lang}
    
    data = {
        "engine": engine_id,
        "payload": payload,
        "headers": {"X-Aether-Key": AETHER_KEY},
        "timeout": timeout
    }
    
    print(f"  ⚡ Executing [{engine_id}]...", end="", flush=True)
    t0 = time.time()
    result = api_call("execute", method="POST", data=data, timeout=timeout)
    elapsed = time.time() - t0
    
    # Check if async engine returned session_id
    resp_data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    sid = resp_data.get("session_id") or resp_data.get("task_id")
    
    if sid and engine_id in ASYNC_ENGINES:
        print(f" started (async), polling...", flush=True)
        result = poll_async(engine_id, sid, t0)
    else:
        status = result.get("status", "unknown")
        print(f" {status} ({elapsed:.1f}s)")
    
    return result


def poll_async(engine_id, session_id, t0, max_polls=60, interval=2.5):
    """Poll an async engine for results."""
    for i in range(max_polls):
        time.sleep(interval)
        poll_url = f"poll?engine={engine_id}&session_id={session_id}"
        resp = api_call(poll_url, method="POST")
        
        data = resp.get("data", {}) if isinstance(resp.get("data"), dict) else {}
        st = data.get("status", data.get("state", ""))
        
        print(f"    Poll #{i+1}: {st}", flush=True)
        
        if st in ("completed", "done", "ready") or data.get("result") or data.get("analysis") or data.get("recipe"):
            elapsed = time.time() - t0
            print(f"  ✅ [{engine_id}] completed ({elapsed:.1f}s)")
            return {"engine": engine_id, "status": "success", "data": data, "latency_ms": int(elapsed * 1000)}
        
        if st in ("error", "failed"):
            elapsed = time.time() - t0
            return {"engine": engine_id, "status": "error", "error": data.get("error", "Engine error"), "latency_ms": int(elapsed * 1000)}
    
    elapsed = time.time() - t0
    return {"engine": engine_id, "status": "error", "error": f"Timeout after {max_polls} polls", "latency_ms": int(elapsed * 1000)}


def auto_route(query):
    """Auto-select engines based on query keywords."""
    q = query.lower()
    selected = set()
    for keyword, engines in ROUTING.items():
        if keyword in q:
            selected.update(engines)
    
    if not selected:
        selected = set(DEFAULT_ENGINES)
    
    return list(selected)[:5]  # Max 5 engines


def swarm_execute(engines, query, lang="en"):
    """Execute multiple engines and merge results."""
    print(f"\n{'='*70}")
    print(f"  AETHERSWARM — Parallel Execution")
    print(f"  Query: {query[:80]}...")
    print(f"  Engines: {', '.join(engines)}")
    print(f"  Language: {lang.upper()}")
    print(f"{'='*70}\n")
    
    results = {}
    t0 = time.time()
    
    for engine_id in engines:
        result = execute_engine(engine_id, query, lang)
        results[engine_id] = result
    
    total = time.time() - t0
    
    # Summary
    print(f"\n{'='*70}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*70}\n")
    
    success = sum(1 for r in results.values() if r.get("status") == "success")
    errors = len(results) - success
    
    for eid, r in results.items():
        status = "✅" if r.get("status") == "success" else "❌"
        ms = r.get("latency_ms", 0)
        print(f"  {status} {eid:30s} {ms}ms")
    
    print(f"\n  Total: {success}/{len(results)} success | {total:.1f}s total")
    print(f"{'='*70}\n")
    
    return results


def format_output(results, fmt="json"):
    """Format results for output."""
    if fmt == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif fmt == "markdown":
        for eid, r in results.items() if isinstance(results, dict) else [(results.get("engine", "?"), results)]:
            print(f"\n## {eid}\n")
            if r.get("status") == "success":
                data = r.get("data", {})
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and len(v) > 20:
                            print(f"**{k}**: {v[:500]}\n")
                else:
                    print(str(data)[:2000])
            else:
                print(f"**Error**: {r.get('error', 'Unknown')}")


def health_check():
    """Check gateway health."""
    result = api_call("health")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="AetherSwarm — Multi-Engine AI Orchestration",
        epilog="Examples:\n"
               "  %(prog)s --list\n"
               "  %(prog)s --engine brain --query 'Explain quantum computing'\n"
               "  %(prog)s --swarm --query 'Analyze Greek market' --engines consulting,marketing,apex\n"
               "  %(prog)s --auto --query 'Best restaurant concept for Athens'\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--list", action="store_true", help="List all available engines")
    parser.add_argument("--health", action="store_true", help="Check gateway health")
    parser.add_argument("--engine", type=str, help="Single engine ID to execute")
    parser.add_argument("--engines", type=str, help="Comma-separated engine IDs for swarm mode")
    parser.add_argument("--swarm", action="store_true", help="Enable swarm (parallel) execution")
    parser.add_argument("--auto", action="store_true", help="Auto-route query to best engines")
    parser.add_argument("--query", "-q", type=str, help="Query to send to engine(s)")
    parser.add_argument("--lang", type=str, default="en", choices=["en", "el"], help="Response language")
    parser.add_argument("--format", "-f", type=str, default="json", choices=["json", "markdown"], help="Output format")
    parser.add_argument("--timeout", type=int, default=120, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    if args.list:
        list_engines()
        return
    
    if args.health:
        health_check()
        return
    
    if not args.query:
        parser.error("--query is required for execution")
    
    if args.auto:
        engines = auto_route(args.query)
        print(f"  🧠 Auto-selected engines: {', '.join(engines)}")
        results = swarm_execute(engines, args.query, args.lang)
        format_output(results, args.format)
    
    elif args.swarm:
        if not args.engines:
            parser.error("--engines is required for swarm mode (or use --auto)")
        engines = [e.strip() for e in args.engines.split(",")]
        results = swarm_execute(engines, args.query, args.lang)
        format_output(results, args.format)
    
    elif args.engine:
        result = execute_engine(args.engine, args.query, args.lang, args.timeout)
        format_output(result, args.format)
    
    else:
        # Default to auto mode
        engines = auto_route(args.query)
        print(f"  🧠 Auto-selected engines: {', '.join(engines)}")
        results = swarm_execute(engines, args.query, args.lang)
        format_output(results, args.format)


if __name__ == "__main__":
    main()
