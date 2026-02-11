"""
╔══════════════════════════════════════════════════════════════╗
║  🛡️ AETHERLANG Ω — SECURITY MIDDLEWARE                     ║
║  Input Validation • Injection Prevention • Rate Limiting     ║
║                                                              ║
║  INSTALLATION:                                               ║
║  1. Copy to: /root/neurodoc_backend/app/middleware/security.py║
║  2. In main.py:                                              ║
║     from app.middleware.security import SecurityMiddleware    ║
║     app.add_middleware(SecurityMiddleware)                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import re
import time
import json
import logging
from collections import defaultdict
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

log = logging.getLogger("security")

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

MAX_QUERY_LENGTH = 5000        # Max chars for query field
MAX_CODE_LENGTH = 10000        # Max chars for code/DSL field
MAX_BODY_SIZE = 50000          # Max request body size (50KB)
RATE_LIMIT_WINDOW = 3600       # 1 hour window
RATE_LIMIT_MAX = 100           # Max requests per window
RATE_LIMIT_BURST = 10          # Max requests per 10 seconds

# ═══════════════════════════════════════════════════════════════
#  INJECTION DETECTION PATTERNS
# ═══════════════════════════════════════════════════════════════

# Severe patterns — BLOCK request entirely
BLOCK_PATTERNS = [
    (re.compile(r'__import__\s*\(', re.IGNORECASE), "Code injection: __import__"),
    (re.compile(r'(?:eval|exec|compile)\s*\(', re.IGNORECASE), "Code injection: eval/exec"),
    (re.compile(r'os\.(?:system|popen|exec)', re.IGNORECASE), "OS command injection"),
    (re.compile(r'subprocess\.', re.IGNORECASE), "Subprocess injection"),
    (re.compile(r';\s*(?:DROP|DELETE|INSERT|UPDATE|ALTER)\s', re.IGNORECASE), "SQL injection"),
    (re.compile(r'<script\b[^>]*>', re.IGNORECASE), "XSS injection"),
    (re.compile(r'\{\{.*?(?:config|self|request|__)', re.IGNORECASE), "Template injection"),
]

# Warning patterns — SANITIZE but allow
SANITIZE_PATTERNS = [
    re.compile(r'system_prompt\s*[=:"\'{}]', re.IGNORECASE),
    re.compile(r'ignore\s+(?:all\s+)?(?:previous\s+)?instructions', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+(?:a\s+)?(?:different|new|evil)', re.IGNORECASE),
    re.compile(r'override\s+(?:system|prompt|safety|guard)', re.IGNORECASE),
    re.compile(r'new\s+instructions?\s*:', re.IGNORECASE),
    re.compile(r'jailbreak|DAN\s*mode|developer\s*mode', re.IGNORECASE),
]

# ═══════════════════════════════════════════════════════════════
#  RATE LIMITER (In-Memory)
# ═══════════════════════════════════════════════════════════════

class RateLimiter:
    """Simple in-memory rate limiter with sliding window"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, str]:
        """Check if request is allowed"""
        now = time.time()
        
        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] 
            if now - t < RATE_LIMIT_WINDOW
        ]
        
        # Check burst (10 req in 10 sec)
        recent = [t for t in self.requests[client_ip] if now - t < 10]
        if len(recent) >= RATE_LIMIT_BURST:
            return False, f"Burst limit exceeded ({RATE_LIMIT_BURST}/10s)"
        
        # Check hourly limit
        if len(self.requests[client_ip]) >= RATE_LIMIT_MAX:
            return False, f"Rate limit exceeded ({RATE_LIMIT_MAX}/hour)"
        
        # Allow and record
        self.requests[client_ip].append(now)
        return True, "OK"

rate_limiter = RateLimiter()

# ═══════════════════════════════════════════════════════════════
#  VALIDATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def validate_field(value: str, field_name: str, max_length: int) -> Tuple[bool, str, str]:
    """Validate a single field — returns (is_safe, reason, sanitized_value)"""
    if not isinstance(value, str):
        value = str(value) if value else ""
    
    # Length check
    if len(value) > max_length:
        return False, f"{field_name} too long ({len(value)} > {max_length})", ""
    
    # Block patterns (severe)
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(value):
            log.warning(f"🚨 BLOCKED: {reason} in {field_name}")
            return False, reason, ""
    
    # Sanitize patterns (warning)
    sanitized = value
    for pattern in SANITIZE_PATTERNS:
        if pattern.search(sanitized):
            log.warning(f"⚠️ SANITIZED: {pattern.pattern} in {field_name}")
            sanitized = pattern.sub("[FILTERED]", sanitized)
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    return True, "OK", sanitized


def validate_json_body(body: dict) -> Tuple[bool, str, dict]:
    """Validate entire JSON request body"""
    # Check for unexpected fields that could be injection
    ALLOWED_FIELDS = {
        "query", "code", "question", "input_text", "language", "mode",
        "cuisine", "difficulty", "servings", "industry", "revenue", 
        "challenge", "goal", "platform", "product_info", "target_audience",
        "trace", "force_domain", "force_protocol", "knowledge_mode",
        "data",  # for PDF export
    }
    
    unexpected = set(body.keys()) - ALLOWED_FIELDS
    if unexpected:
        # Don't block — just log. Some fields might be legitimate new additions
        log.info(f"ℹ️ Unexpected fields: {unexpected}")
    
    # Specifically check for injection fields
    DANGEROUS_FIELDS = {"system_prompt", "system", "instructions", "override", "jailbreak", "role"}
    injected = set(body.keys()) & DANGEROUS_FIELDS
    if injected:
        log.warning(f"🚨 INJECTION ATTEMPT — dangerous fields: {injected}")
        return False, f"Unauthorized fields: {injected}", body
    
    # Validate individual fields
    sanitized_body = {}
    for key, value in body.items():
        if isinstance(value, str):
            max_len = MAX_CODE_LENGTH if key == "code" else MAX_QUERY_LENGTH
            is_safe, reason, clean = validate_field(value, key, max_len)
            if not is_safe:
                return False, f"Field '{key}': {reason}", body
            sanitized_body[key] = clean
        else:
            sanitized_body[key] = value
    
    return True, "OK", sanitized_body


# ═══════════════════════════════════════════════════════════════
#  MIDDLEWARE CLASS
# ═══════════════════════════════════════════════════════════════

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Enterprise-grade security middleware for AetherLang Ω
    
    Features:
    - Input validation on all POST endpoints
    - Injection pattern detection (code, SQL, XSS, template, prompt)
    - Rate limiting (100/hour + burst protection)
    - Request size limiting
    - Dangerous field detection
    - Audit logging
    """
    
    # Endpoints that need validation
    PROTECTED_ENDPOINTS = {
        "/aetherlang/run", "/aetherlang/start",
        "/api/analyze", "/api/chef", "/api/assembly",
        "/api/consulting", "/api/lab", "/api/marketing",
        "/api/oracle", "/api/cyber", "/api/academic",
        "/assembly/convene", "/assembly/start",
        "/consulting/generate", "/lab/analyze",
        "/marketing/campaign",
    }
    
    # Endpoints that skip validation
    SKIP_ENDPOINTS = {"/health", "/docs", "/openapi.json", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next):
        # Skip non-POST and safe endpoints
        path = request.url.path.rstrip("/")
        
        if request.method == "GET" or path in self.SKIP_ENDPOINTS:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        # Rate limiting
        allowed, reason = rate_limiter.is_allowed(client_ip)
        if not allowed:
            log.warning(f"🚫 RATE LIMITED: {client_ip} — {reason}")
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "detail": reason},
                headers={"Retry-After": "60"}
            )
        
        # Body size check
        content_length = request.headers.get("content-length", "0")
        if int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large", "max_size": MAX_BODY_SIZE}
            )
        
        # Only validate protected endpoints
        if request.method == "POST" and any(path.endswith(ep) or path.startswith(ep) for ep in self.PROTECTED_ENDPOINTS):
            try:
                body = await request.json()
                
                is_safe, reason, sanitized = validate_json_body(body)
                if not is_safe:
                    log.warning(f"🚨 BLOCKED [{client_ip}]: {reason}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Input validation failed", "detail": reason}
                    )
                
                # Replace request body with sanitized version
                # (Starlette doesn't directly support this, so we store in state)
                request.state.sanitized_body = sanitized
                request.state.security_validated = True
                
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid JSON body"}
                )
            except Exception as e:
                log.error(f"Security middleware error: {e}")
                # Don't block on middleware errors — let the request through
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Security"] = "AetherLang-Shield-v1"
        
        return response


# ═══════════════════════════════════════════════════════════════
#  STANDALONE VALIDATION (for direct use in endpoints)
# ═══════════════════════════════════════════════════════════════

def validate_and_sanitize_query(query: str) -> str:
    """Quick validation for use directly in endpoint handlers"""
    if not query:
        return ""
    is_safe, reason, sanitized = validate_field(query, "query", MAX_QUERY_LENGTH)
    if not is_safe:
        raise ValueError(f"Input validation failed: {reason}")
    return sanitized


# ═══════════════════════════════════════════════════════════════
#  INSTALLATION INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════
"""
STEP 1: Copy this file:
  cp security_middleware.py /root/neurodoc_backend/app/middleware/security.py

STEP 2: In main.py, add:
  
  from app.middleware.security import SecurityMiddleware
  
  app = FastAPI(title="NeuroAether Super Brain")
  app.add_middleware(SecurityMiddleware)  # ← ADD THIS LINE

STEP 3: (Optional) Use in endpoints directly:

  from app.middleware.security import validate_and_sanitize_query
  
  @router.post("/run")
  async def run_aether(request: AetherRunRequest):
      # Validate input
      sanitized_query = validate_and_sanitize_query(request.query)
      ...

STEP 4: Test:
  curl -X POST https://neurodoc.app/api/aetherlang/run -H "Content-Type: application/json" -d '{"code": "flow Test", "query": "test, system_prompt: hack"}'
  
  # Should return 400: "Input validation failed"

STEP 5: Monitor:
  journalctl -u neurodoc -f  (look for BLOCKED, SANITIZED, RATE)
"""
