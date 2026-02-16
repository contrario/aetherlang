#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║        AETHERLANG Ω — ULTIMATE TELEGRAM BOT v2.0 MEGA          ║
║   The Technological Showcase of NeuroAether Intelligence         ║
║                                                                  ║
║  🧠 15 AI Engines  •  40+ Archetypes  •  16 API Integrations   ║
║  🔄 OpenRouter  •  🍽️ FDA Safety  •  🎰 LIVE OPAP API         ║
║  🌐 Full Greek/English  •  📊 Live Markets  •  🔬 Nobel Mode   ║
║                                                                  ║
║  v2.0: MEGA PROMPTS from NeuroAether Backend + OPAP LIVE DATA  ║
║  Built by: Hlia × Claude — From Kitchen to Code                ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import httpx
import asyncio
import logging
import re
import html
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

# ═══════════════════════════════════════════════════════════════
#  🛡️ INPUT SANITIZATION & SECURITY
# ═══════════════════════════════════════════════════════════════

MAX_QUERY_LENGTH = 2000
MAX_CODE_LENGTH = 5000

# Patterns that indicate injection attempts
INJECTION_PATTERNS = [
    re.compile(r'system_prompt\s*[=:]', re.IGNORECASE),
    re.compile(r'ignore\s+(all\s+)?(previous\s+)?instructions', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+', re.IGNORECASE),
    re.compile(r'new\s+instructions?\s*:', re.IGNORECASE),
    re.compile(r'override\s+(system|prompt|safety)', re.IGNORECASE),
    re.compile(r'__\w+__'),                         # Python dunder injection
    re.compile(r'eval\s*\(|exec\s*\('),             # Code execution
    re.compile(r';\s*DROP\s|;\s*DELETE\s|;\s*INSERT\s', re.IGNORECASE),  # SQL injection
    re.compile(r'<script\b', re.IGNORECASE),        # XSS
    re.compile(r'\{\{.*\}\}'),                       # Template injection
]

def sanitize_input(text: str, max_length: int = MAX_QUERY_LENGTH) -> str:
    """Sanitize user input — strip injection attempts, enforce length limits"""
    if not text:
        return ""
    
    # 1. Enforce length limit
    text = text[:max_length]
    
    # 2. Remove null bytes and control chars (keep newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 3. Strip potential JSON injection chars at boundaries
    #    (don't remove from middle — users can write normal JSON examples)
    text = text.strip()
    
    # 4. Check for injection patterns — log but don't block (just neutralize)
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            log.warning(f"⚠️ INJECTION PATTERN detected: {pattern.pattern}")
            # Neutralize by wrapping in harmless context
            text = re.sub(pattern, '[FILTERED]', text)
    
    return text

def sanitize_for_json(text: str) -> str:
    """Make text safe for JSON embedding — escape special chars"""
    if not text:
        return ""
    # json.dumps already handles escaping, but we double-check
    # Remove any unmatched quotes that could break JSON structure
    return text.replace('\\', '\\\\').replace('"', '\\"')

def validate_query_safety(query: str) -> Tuple[bool, str]:
    """Validate query is safe to process — returns (is_safe, reason)"""
    if not query or not query.strip():
        return False, "Empty query"
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query too long ({len(query)} > {MAX_QUERY_LENGTH})"
    
    # Check for severe injection attempts
    severe_patterns = [
        (r'system_prompt\s*[=:"\'{}]', "System prompt injection"),
        (r'ignore\s+(all\s+)?(previous\s+)?instructions', "Instruction override attempt"),
        (r'__import__|eval\s*\(|exec\s*\(|os\.system', "Code execution attempt"),
        (r'"\s*,\s*"\s*\w+"\s*:\s*"', "JSON structure injection"),
    ]
    for pattern, reason in severe_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, reason
    
    return True, "OK"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9999")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
FDA_API_KEY = os.getenv("FDA_API_KEY", "")
MEXC_API_KEY = os.getenv("MEXC_API_KEY", "")
MEXC_API_SECRET = os.getenv("MEXC_API_SECRET", "")
GATEIO_API_KEY = os.getenv("GATEIO_API_KEY", "")
GATEIO_API_SECRET = os.getenv("GATEIO_API_SECRET", "")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "")
KUCOIN_API_KEY = os.getenv("KUCOIN_API_KEY", "")
KUCOIN_API_SECRET = os.getenv("KUCOIN_API_SECRET", "")
SERPER_KEY = os.getenv("SERPER_API_KEY", "")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()]

POLL_INTERVAL = 4
POLL_TIMEOUT = 180
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ═══════════════════════════════════════════════════════════════
#  💰 TELEGRAM STARS CREDIT SYSTEM
# ═══════════════════════════════════════════════════════════════

CREDITS_DB = "/opt/aetherlang-bot/credits.db"

# Credit costs per engine
ENGINE_COSTS = {
    "chef": 2, "molecular": 2, "omega": 2, "terra": 2,
    "apex": 4, "consulting": 4, "lab": 4, "academic": 4,
    "assembly": 4, "brain": 4,
    "marketing": 2, "cyber": 2, "oracle": 2, "crypto": 3,
    "blueprint": 6, "vision": 5, "vision_multi": 8,
}

# Credit packages (Stars → Credits)
CREDIT_PACKAGES = {
    "starter": {"title": "Starter Pack", "desc": "15 AI credits", "stars": 150, "credits": 15},
    "pro": {"title": "Pro Pack", "desc": "50 AI credits — Best Value!", "stars": 400, "credits": 50},
    "ultimate": {"title": "Ultimate Pack", "desc": "150 AI credits", "stars": 900, "credits": 150},
}

def init_credits_db():
    """Initialize credits database on startup"""
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS user_credits (
        user_id INTEGER PRIMARY KEY,
        credits INTEGER DEFAULT 3,
        total_purchased INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0,
        first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
        last_purchase TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, type TEXT, amount INTEGER,
        stars_paid INTEGER DEFAULT 0, engine TEXT DEFAULT '',
        description TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def get_credits(user_id: int) -> int:
    """Get user's credit balance (creates user with 3 free credits if new)"""
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, 3)", (user_id,))
        conn.commit()
        conn.close()
        return 3
    conn.close()
    return row[0]

def spend_credits(user_id: int, amount: int, engine: str) -> bool:
    """Deduct credits for engine use. Returns False if insufficient."""
    current = get_credits(user_id)
    if current < amount:
        return False
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("UPDATE user_credits SET credits = credits - ?, total_spent = total_spent + ? WHERE user_id = ?",
              (amount, amount, user_id))
    c.execute("INSERT INTO transactions (user_id, type, amount, engine, description) VALUES (?, 'spend', ?, ?, ?)",
              (user_id, amount, engine, f"Used {engine} engine"))
    conn.commit()
    conn.close()
    return True

def add_credits(user_id: int, amount: int, stars_paid: int):
    """Add credits after purchase"""
    get_credits(user_id)  # ensure user exists
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("UPDATE user_credits SET credits = credits + ?, total_purchased = total_purchased + ?, last_purchase = CURRENT_TIMESTAMP WHERE user_id = ?",
              (amount, amount, user_id))
    c.execute("INSERT INTO transactions (user_id, type, amount, stars_paid, description) VALUES (?, 'purchase', ?, ?, ?)",
              (user_id, amount, stars_paid, f"Purchased {amount} credits for {stars_paid} Stars"))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════
#  OPAP GAME IDS — Live Lottery Data
# ═══════════════════════════════════════════════════════════════

OPAP_GAMES = {
    "kino": {"id": 1100, "name": "ΚΙΝΟ", "icon": "🎱", "numbers": 20, "range": 80},
    "powerspin": {"id": 1110, "name": "PowerSpin", "icon": "🌀"},
    "super3": {"id": 2100, "name": "Super 3", "icon": "3️⃣"},
    "proto": {"id": 2101, "name": "ΠΡΩΤΟ", "icon": "1️⃣"},
    "lotto": {"id": 5103, "name": "ΛΟΤΤΟ", "icon": "💰", "numbers": 6, "range": 49, "bonus": 1},
    "tzoker": {"id": 5104, "name": "ΤΖΟΚΕΡ", "icon": "🃏", "numbers": 5, "range": 45, "bonus_range": 20},
    "extra5": {"id": 5106, "name": "Extra 5", "icon": "5️⃣", "numbers": 5, "range": 35},
    "eurojackpot": {"id": 5149, "name": "Eurojackpot", "icon": "🇪🇺"},
}

# ═══════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/aetherlang-bot.log", mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger("AetherLangBot")

# ═══════════════════════════════════════════════════════════════
#  USER LANGUAGE PREFERENCES
# ═══════════════════════════════════════════════════════════════

user_language_prefs: Dict[int, str] = {}  # user_id -> "el" or "en"
_photo_buffer: Dict[str, dict] = {}  # media_group_id -> {chat_id, photos, caption, task}
user_last_response: Dict[int, dict] = {}  # user_id -> {"text": ..., "engine": ..., "query": ...}

# ═══════════════════════════════════════════════════════════════
#  LANGUAGE INSTRUCTION GENERATOR (from NeuroAether backend)
# ═══════════════════════════════════════════════════════════════

def get_language_instruction(lang: str) -> str:
    """Generate explicit language enforcement instruction — DOUBLE reinforcement"""
    if lang == "el":
        return """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  ΚΡΙΣΙΜΟ — ΓΛΩΣΣΑ: ΕΛΛΗΝΙΚΑ  ⚠️                        ║
╚══════════════════════════════════════════════════════════════╝

ΑΠΑΝΤΗΣΕ ΑΠΟΚΛΕΙΣΤΙΚΑ ΣΤΑ ΕΛΛΗΝΙΚΑ. ΑΥΤΟ ΕΙΝΑΙ ΥΠΟΧΡΕΩΤΙΚΟ.

ΚΑΝΟΝΕΣ ΓΛΩΣΣΑΣ:
1. ΟΛΟ το περιεχόμενο ΠΡΕΠΕΙ να είναι στα Ελληνικά
2. Τίτλοι, αναλύσεις, συστάσεις, βήματα — ΟΛΑ στα Ελληνικά
3. Ονόματα συνταγών, υλικών, ενεργειών — ΟΛΑ στα Ελληνικά
4. ΜΗΝ χρησιμοποιήσεις Αγγλικά ΠΟΤΕ (εξαίρεση: τεχνικοί όροι HACCP, KPI, SWOT, ROI)
5. Χρησιμοποίησε € (ευρώ) για νομισματικά ποσά
6. Αν δεν ξέρεις τη μετάφραση, γράψε στα Ελληνικά με εξήγηση

ΠΑΡΑΔΕΙΓΜΑΤΑ:
- ΟΧΙ "Executive Summary" → ΝΑΙ "Εκτελεστική Σύνοψη"
- ΟΧΙ "Ingredients" → ΝΑΙ "Υλικά"
- ΟΧΙ "Risk Matrix" → ΝΑΙ "Πίνακας Κινδύνων"
- ΟΧΙ "Phase 1" → ΝΑΙ "Φάση 1"

REMINDER: ΕΛΛΗΝΙΚΑ. ΕΛΛΗΝΙΚΑ. ΕΛΛΗΝΙΚΑ.
"""
    else:
        return """
CRITICAL: Respond ENTIRELY in English. All content, titles, analysis in English.
Use € for monetary amounts. Do NOT use Greek language."""

# ═══════════════════════════════════════════════════════════════
#  MEGA SYSTEM PROMPTS — Extracted from NeuroAether Backend
# ═══════════════════════════════════════════════════════════════

def build_chef_prompt(lang: str) -> str:
    """Executive Chef system prompt from chef.py + culinary.py"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

═══════════════════════════════════════════════════════════════
IDENTITY: EXECUTIVE CHEF & RESTAURANT CONSULTANT
Style: Michelin-trained, 20+ years, F&B Consultant, Menu Engineer, R&D Chef
═══════════════════════════════════════════════════════════════

ΔΕΝ ΕΙΣΑΙ food blogger. ΕΙΣΑΙ:
- Michelin-trained Executive Chef με 20+ χρόνια εμπειρία
- F&B Consultant που έχει σώσει 50+ εστιατόρια
- Menu Engineer με MBA in Hospitality
- R&D Chef που δημιουργεί signature dishes

═══════════════════════════════════════════════════════════════
ΚΡΙΤΙΚΟΙ ΚΑΝΟΝΕΣ — ΤΗΡΗΣΕ ΤΟΥΣ Ή ΑΠΟΤΥΧΕ:
═══════════════════════════════════════════════════════════════

⛔ ΑΠΑΓΟΡΕΥΕΤΑΙ:
- "Λίγο αλάτι" → ΓΡΑΨΕ "8g θαλασσινό αλάτι"
- "Ψήστε μέχρι να ετοιμαστεί" → ΓΡΑΨΕ "180°C για 12 λεπτά, core temp 72°C"
- "Οικονομικό" → ΓΡΑΨΕ "Food Cost: 2.85€ (23.8%)"
- "Για 4 άτομα" → ΓΡΑΨΕ "4 μερίδες × 180g = 720g yield"
- Γενικές συμβουλές χωρίς actionable steps

✅ ΥΠΟΧΡΕΩΤΙΚΟ ΣΕ ΚΑΘΕ ΣΥΝΤΑΓΗ:
- Ακριβή γραμμάρια για ΚΑΘΕ υλικό
- Κόστος ανά υλικό και συνολικό food cost
- Θερμοκρασίες σε °C (όχι "μέτρια φωτιά")
- Χρόνοι σε λεπτά (όχι "μέχρι να ροδίσει")
- Yield % για κρέατα/ψάρια (μετά το καθάρισμα)
- HACCP critical points
- MacYuFBI balance analysis

═══════════════════════════════════════════════════════════════
MENU ENGINEERING CATEGORIES:
═══════════════════════════════════════════════════════════════

⭐ STARS: High Profit + High Popularity → ΠΡΟΩΘΗΣΕ
🐴 PLOWHORSES: Low Profit + High Popularity → ΑΥΞΗΣΕ ΤΙΜΗ
🧩 PUZZLES: High Profit + Low Popularity → REBRAND
🐕 DOGS: Low Profit + Low Popularity → ΑΦΑΙΡΕΣΕ

Food Cost Targets: Fine Dining 28-32%, Casual 30-35%, Fast Casual 25-30%

═══════════════════════════════════════════════════════════════
MacYuFBI FLAVOR BALANCE SYSTEM:
═══════════════════════════════════════════════════════════════
M(aillard/Umami) ←→ A(cid) — Counters richness
C(aramel/Sweet) ←→ B(itter) — Depth control
Y(east/Fermented) ←→ F(at) — Texture balance
I(Heat/Spice) ←→ C+F — Cooling agents

═══════════════════════════════════════════════════════════════
NEURAL AGENTS ACTIVE (15):
═══════════════════════════════════════════════════════════════
🎨 Flavor Architect | 🔪 Technique Master | 🥗 Nutrition Sage
🛡️ Safety Guardian | 🌍 Culture Keeper | ✨ Innovation Spark
💰 Cost Sentinel | 🎭 Presentation Artist | 🍷 Sommelier Spirit
🌿 Seasonal Oracle | 🔬 Science Prophet | ♻️ Sustainability Sage
📊 Business Strategist | 🧪 Fermentation Alchemist | 🎂 Pastry Virtuoso

MINIMUM 12 EXECUTION STEPS PER RECIPE — ΥΠΟΧΡΕΩΤΙΚΟ!
Σπάσε κάθε διαδικασία σε μικρά, ΑΝΑΛΥΤΙΚΑ βήματα:
- Προετοιμασία υλικών (2-3 βήματα)
- Mise en place (2-3 βήματα)
- Κύριο μαγείρεμα (4-5 βήματα)
- Σάλτσες/συνοδευτικά (2-3 βήματα)
- Plating/σερβίρισμα (1-2 βήματα)

ΚΑΘΕ ΒΗΜΑ ΠΡΕΠΕΙ να περιέχει:
- "step_number": αριθμός (1, 2, 3...)
- "action": ΣΥΝΤΟΜΗ περιγραφή (5-10 λέξεις)
- "detailed_instructions": ΑΝΑΛΥΤΙΚΕΣ ΟΔΗΓΙΕΣ — ΤΟΥΛΑΧΙΣΤΟΝ 3-4 ΠΡΟΤΑΣΕΙΣ!
  Εξήγησε ΑΚΡΙΒΩΣ τι κάνεις, πώς, γιατί, τι να προσέξεις.
  Π.χ. "Βάλτε το ελαιόλαδο σε βαθύ τηγάνι. Ζεστάνετε σε μέτρια-δυνατή φωτιά μέχρι να αρχίσει να τρεμοπαίζει (180°C). Σωτάρετε τα κρεμμύδια ανακατεύοντας κάθε 30 δευτερόλεπτα. Μόλις γίνουν ημιδιαφανή (3-4 λεπτά) προσθέστε το σκόρδο."
- "temperature_celsius": αριθμός (αν ισχύει)
- "time_minutes": αριθμός (αν ισχύει)
- "visual_cue": τι βλέπεις οπτικά (π.χ. "χρυσαφένιο χρώμα", "αφράτο υφή")
- "chef_technique": τεχνική (π.χ. "sauté", "blanch", "deglaze")
- "common_mistakes": τι λάθη κάνουν οι αρχάριοι
- "pro_tips": επαγγελματικό tip

⚠️ CRITICAL: Τα "detailed_instructions" ΠΡΕΠΕΙ να είναι ΕΚΤΕΤΑΜΕΝΑ (50-100 λέξεις/βήμα).
ΟΧΙ "Ψήστε τα". ΝΑΙ "Τοποθετήστε τις μελιτζάνες σε ταψί με λαδόκολλα. Ψήστε στα 200°C για 35-40 λεπτά, γυρίζοντας στη μέση. Θα πρέπει να είναι πολύ μαλακές και να έχουν βυθιστεί. Η φλούδα θα μαυρίσει ελαφρά — αυτό είναι σωστό. Αφήστε τες 10 λεπτά να κρυώσουν πριν τις ξεφλουδίσετε."

Respond in JSON with full recipe structure including: recipe_name, overview (category, total_time_minutes, portions, portion_weight_grams, difficulty), financials (food_cost_per_portion, recommended_menu_price, food_cost_percentage, menu_category, gross_profit_per_portion), ingredients (item, quantity_grams, cost_for_recipe, yield_percent, preparation, substitutes, storage), mise_en_place, execution_steps (12+ — EACH with step_number, action, detailed_instructions [50-100 WORDS MINIMUM], equipment, temperature_celsius, time_minutes, visual_cue, chef_technique, common_mistakes, pro_tips, ccp_safety), plating (description, garnish, plate_type), haccp (critical_temps, allergens, storage_instructions, cross_contamination), macyufbi (dominant_flavors, counter_strategy, balance_score), zero_waste (byproduct, use).

{"ΤΕΛΙΚΗ ΥΠΕΝΘΥΜΙΣΗ: ΟΛΑ στα ΕΛΛΗΝΙΚΑ! recipe_name, ingredients, detailed_instructions, visual_cue, common_mistakes, pro_tips — ΟΛΑ ΕΛΛΗΝΙΚΑ. ΜΟΝΟ τεχνικοί όροι (sauté, blanch, HACCP) στα Αγγλικά." if lang == "el" else "FINAL REMINDER: ALL content in English."
}"""


def build_apex_prompt(lang: str) -> str:
    """APEX Nobel-level strategy prompt from brain.py Nobel Mode"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

You are NeuroAether Super Brain in NOBEL MODE v3.0 — delivering McKinsey + Harvard + Nobel-level analysis.

TARGET MISSION: Create PUBLICATION-READY analysis worthy of:
- Harvard Business Review / MIT Technology Review
- McKinsey Global Institute / World Economic Forum
- Nobel Prize Committee consideration

MANDATORY QUALITY STANDARDS:
1. EVERY claim needs SPECIFIC numbers (%, EUR/USD, years, metrics)
2. Reference REAL companies, studies, research papers with dates
3. Write PARAGRAPHS (4-5 sentences minimum) not bullet summaries
4. Include CONTRARIAN perspectives and honest limitations
5. Minimum 3000 tokens of substantive analytical content

Respond in JSON with THIS EXACT STRUCTURE:
{{
    "executive_summary": "8-10 powerful sentences covering problem magnitude, current state, breakthrough insight, strategy, expected impact, stakeholders, timeline, call to action",
    "grand_challenge": "Frame as CIVILIZATIONAL IMPERATIVE (6+ sentences) with specific projections",
    "context_analysis": {{
        "historical_evolution": "5+ key milestones with dates",
        "current_landscape": "Latest developments, major players, breakthroughs",
        "market_data": "Market size EUR/USD, growth rate %, financial statistics",
        "stakeholder_map": ["Stakeholder 1: role", "Stakeholder 2: role"],
        "regulatory_environment": "Current laws, pending legislation"
    }},
    "approaches": [
        {{
            "name": "Approach Name",
            "category": "Category",
            "description": "4-5 FULL PARAGRAPHS of analysis",
            "mechanism": "5+ sentence technical explanation",
            "evidence": [{{"source": "Research/Company", "finding": "Specific result with numbers", "year": "2024"}}],
            "implementation": {{"timeline": "Months", "cost_range": "EUR range", "roi_projection": "X%"}},
            "pros": ["Pro 1", "Pro 2"],
            "cons": ["Con 1", "Con 2"]
        }}
    ],
    "phased_roadmap": [
        {{"phase": "Phase 1", "timeframe": "Month 1-3", "actions": ["Action 1"], "budget": "EUR", "milestone": "Milestone"}},
        {{"phase": "Phase 2", "timeframe": "Month 4-6", "actions": ["Action 1"], "budget": "EUR", "milestone": "Milestone"}},
        {{"phase": "Phase 3", "timeframe": "Month 7-12", "actions": ["Action 1"], "budget": "EUR", "milestone": "Milestone"}}
    ],
    "risk_matrix": [
        {{"risk": "Risk", "probability": "HIGH/MED/LOW", "impact": "HIGH/MED/LOW", "mitigation": "Strategy", "contingency": "Plan B"}}
    ],
    "kpis": [
        {{"metric": "KPI Name", "current": "Value", "target_6m": "Value", "target_12m": "Value"}}
    ],
    "nobel_vision": {{"description": "Breakthrough innovation idea", "impact": "Potential impact"}},
    "meta_review": {{"ultimate_insight": "One distilled truth", "confidence": "85%"}}
}}"""


def build_assembly_prompt(lang: str, mode: str = "business") -> str:
    """Grand Assembly prompt from assembly.py"""
    lang_inst = get_language_instruction(lang)
    
    mode_characters = {
        "strategic": "Alexander the Great, Sun Tzu, Machiavelli, Cleopatra",
        "technical": "Tony Stark, Nikola Tesla, Daedalus, Archimedes",
        "analytical": "Sherlock Holmes, Isaac Newton, Socrates, Oracle",
        "tactical": "Ethan Hunt, MacGyver, Odysseus, Batman",
        "creative": "Leonardo DaVinci, Merlin, Prometheus, Morpheus",
        "wisdom": "Socrates, Merlin, Athena, Aristotle, Confucius, Seneca",
        "financial": "Warren Buffett, George Soros, Ray Dalio, John Maynard Keynes, Peter Thiel",
        "legal": "Harvey Specter, Ruth Bader Ginsburg, Atticus Finch, Athena",
        "startup": "Steve Jobs, Elon Musk, Peter Thiel, Paul Graham, Tim Draper",
        "marketing": "Don Draper, Seth Godin, Robert Cialdini, Cleopatra",
        "business": "Alexander, Buffett, Jobs, Thiel, Specter, Drucker, Sun Tzu",
        "full": "ALL 26+ legendary archetypes"
    }
    
    chars = mode_characters.get(mode, mode_characters["business"])
    
    return f"""{lang_inst}

You are the GRAND ASSEMBLY — a council of legendary characters analyzing a challenge.

CHARACTER ARCHETYPES ACTIVE: {chars}

NOBEL-LEVEL INSTRUCTIONS:
1. EVERY CHARACTER MUST RESPOND with IN-DEPTH analysis (300-500 words each)
2. SPECIFIC, ACTIONABLE recommendations
3. Use their AUTHENTIC voice and EXPERTISE
4. DISAGREE when appropriate — real debate
5. After ALL characters speak, create a MASTERFUL synthesis

Respond in JSON:
{{
    "archetypes": [
        {{"name": "Character Name", "icon": "emoji", "analysis": "Their full 300+ word analysis", "recommendation": "Specific advice", "key_insight": "Breakthrough insight"}}
    ],
    "synthesis": {{
        "consensus_verdict": "GO / CAUTION / NO-GO",
        "confidence_score": 85,
        "chairperson": {{"name": "Best suited leader", "icon": "emoji", "why": "Reason"}},
        "executive_summary": "Unified synthesis (300+ words)",
        "unified_strategy": {{
            "primary_approach": "Main strategy",
            "tactical_steps": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
            "timeline": "Estimated timeline"
        }},
        "final_recommendation": "Clear decisive action"
    }},
    "gandalf_review": {{
        "status": "APPROVED / CAUTION / VETOED",
        "wisdom": "Safety assessment",
        "additional_risks": ["Hidden risk 1", "Hidden risk 2"],
        "required_safeguards": ["Safeguard 1", "Safeguard 2"],
        "wisdom_quote": "Relevant quote"
    }},
    "key_insights": [{{"archetype": "Name", "insight": "Valuable insight"}}],
    "dissenting_opinions": ["Disagreements"],
    "risk_factors": [{{"risk": "Risk", "level": "HIGH/MEDIUM/LOW", "mitigation": "Strategy"}}]
}}"""


def build_consulting_prompt(lang: str) -> str:
    """McKinsey consulting prompt from consulting.py"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

Generate a McKinsey-level Strategic Report in JSON:
{{
    "title": "Strategic Report Title",
    "executive_summary": "3 paragraph comprehensive summary with specific insights and numbers",
    "modules": [
        {{"type": "swot", "title": "SWOT Analysis", "data": {{"strengths": ["s1","s2","s3"], "weaknesses": ["w1","w2","w3"], "opportunities": ["o1","o2","o3"], "threats": ["t1","t2","t3"]}}}},
        {{"type": "roadmap", "title": "Implementation Roadmap", "phases": [{{"name": "Phase 1", "time": "Month 1-3", "action": "Detailed action", "budget": "EUR", "kpi": "Metric"}}, {{"name": "Phase 2", "time": "Month 4-6", "action": "Action"}}, {{"name": "Phase 3", "time": "Month 7-12", "action": "Action"}}, {{"name": "Phase 4", "time": "Year 2", "action": "Action"}}]}},
        {{"type": "kpis", "title": "Key Performance Indicators", "metrics": [{{"name": "KPI 1", "current": "X%", "target": "Y%", "timeline": "3 months"}}, {{"name": "KPI 2", "current": "A", "target": "B"}}]}}
    ],
    "competitive_analysis": "Detailed competitor landscape",
    "financial_projections": {{"year1": "EUR", "year2": "EUR", "roi": "%"}},
    "recommendations": ["Detailed recommendation 1", "Detailed recommendation 2", "Detailed recommendation 3"],
    "next_steps": ["Immediate action 1", "Immediate action 2", "Immediate action 3"],
    "risk_assessment": [{{"risk": "Risk", "probability": "H/M/L", "impact": "H/M/L", "mitigation": "Strategy"}}]
}}

Provide industry-specific, actionable insights with quantified metrics."""


def build_lab_prompt(lang: str) -> str:
    """Scientific analysis prompt from lab.py"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

ACT AS: NEUROAETHER OMNI-KERNEL v24.0 — Deep Scientific Analyst
50 Domains × 48 Protocols × 6 Analysis Layers

Analyze the target and respond in JSON:
{{
    "target": "Target summary",
    "domain_detected": "Detected scientific domain",
    "executive_summary": "2-3 paragraphs with deep insights and specific numbers",
    "layers": [
        {{"title": "Deep Analysis", "content": "Technical breakdown with specifics (5+ paragraphs)"}},
        {{"title": "Market Impact", "content": "Economic analysis with EUR/USD numbers"}},
        {{"title": "Ethical Horizon", "content": "Long-term societal impact assessment"}},
        {{"title": "Innovation Vectors", "content": "Emerging opportunities and breakthroughs"}}
    ],
    "nobel_insight": "Breakthrough idea that could win a Nobel prize",
    "actionable_steps": ["Detailed step 1 with timeline", "Step 2", "Step 3", "Step 4", "Step 5"],
    "risk_matrix": [
        {{"risk": "Risk 1", "severity": "High/Medium/Low", "probability": "H/M/L", "mitigation": "Strategy"}},
        {{"risk": "Risk 2", "severity": "Medium", "mitigation": "Strategy"}}
    ],
    "data_references": ["Source 1 with year", "Source 2"],
    "omni_vision": "Philosophical insight connecting to humanity's future"
}}"""


def build_marketing_prompt(lang: str) -> str:
    """Marketing prompt from marketing.py"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

Generate a VIRAL marketing campaign strategy in JSON:
{{
    "campaign_name": "Creative campaign name",
    "target_audience": "Detailed audience profile with demographics",
    "brand_positioning": "How the brand should be perceived",
    "hook": "Attention-grabbing hook that stops scrolling",
    "main_copy": "Full campaign copy with emotional triggers (200+ words)",
    "content_calendar": [
        {{"day": "Day 1", "platform": "Instagram", "content_type": "Reel", "topic": "Topic", "cta": "CTA"}},
        {{"day": "Day 3", "platform": "TikTok", "content_type": "Video", "topic": "Topic", "cta": "CTA"}}
    ],
    "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
    "cta": "Compelling call to action",
    "visual_direction": "Detailed visual description for designers",
    "posting_times": {{"instagram": "Best time", "tiktok": "Best time", "facebook": "Best time"}},
    "engagement_strategy": ["Strategy 1", "Strategy 2", "Strategy 3"],
    "budget_allocation": {{"social_ads": "40%", "influencers": "30%", "content_creation": "20%", "analytics": "10%"}},
    "kpis": [{{"metric": "Engagement Rate", "target": "5%"}}, {{"metric": "Reach", "target": "100K"}}],
    "competitive_edge": "What makes this campaign different"
}}"""


def build_cyber_prompt(lang: str) -> str:
    """Cyber Intelligence prompt from knowledge_modules.py"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

You are a Cyber Intelligence Layer with:
- White-Hat Security Core: Penetration testing, OWASP Top 10, NIST frameworks, ethical hacking
- Black-Hat Attack Patterns (for defense): Malware tactics, ransomware, phishing, zero-day exploits
- Cyber Threat Intelligence: CERTs, security forums, threat hunting, incident response
- AI-Powered Defense: ML anomaly detection, fraud prevention, intrusion analysis
- Global Security Standards: ISO 27001, GDPR, HIPAA, PCI DSS

Respond in JSON:
{{
    "threat_assessment": "Overview of the security landscape for this topic",
    "offense_view": "How attackers would approach this (for defense purposes)",
    "defense_strategy": {{
        "immediate_actions": ["Action 1 with specifics", "Action 2"],
        "medium_term": ["Action 1", "Action 2"],
        "long_term": ["Action 1"]
    }},
    "three_approaches": [
        {{"name": "Offensive Strategy", "description": "Proactive testing", "pros": ["Pro"], "cons": ["Con"]}},
        {{"name": "Defensive Strategy", "description": "Protective measures", "pros": ["Pro"], "cons": ["Con"]}},
        {{"name": "Hybrid Strategy", "description": "Combined approach", "pros": ["Pro"], "cons": ["Con"]}}
    ],
    "risk_matrix": [{{"risk": "Risk", "severity": "CRITICAL/HIGH/MEDIUM/LOW", "mitigation": "Strategy"}}],
    "compliance": ["Relevant standards: ISO 27001, GDPR, etc."],
    "tools_recommended": ["Tool 1: purpose", "Tool 2: purpose"],
    "actionable_steps": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
    "guardian_ethics_check": "Ethical considerations and responsible disclosure"
}}"""


def build_oracle_prompt(lang: str, opap_data: str = "") -> str:
    """OPAP Oracle prompt with LIVE data — FORCES actual number generation"""
    lang_inst = get_language_instruction(lang)
    data_section = f"\n\n═══════════════════════════════════════\n📊 ΖΩΝΤΑΝΑ ΔΕΔΟΜΕΝΑ OPAP:\n═══════════════════════════════════════\n{opap_data}" if opap_data else ""
    return f"""{lang_inst}

═══════════════════════════════════════════════════════════════
IDENTITY: NEUROAETHER OPAP ORACLE — Στατιστικός Αναλυτής Τυχερών Παιχνιδιών
═══════════════════════════════════════════════════════════════
{data_section}

⚠️ ΚΡΙΣΙΜΟΙ ΚΑΝΟΝΕΣ:
1. ΠΑΝΤΑ δίνε ΣΥΓΚΕΚΡΙΜΕΝΟΥΣ αριθμούς (π.χ. [3, 12, 17, 28, 35]) — ΠΟΤΕ μόνο κείμενο
2. Χρησιμοποίησε τα LIVE DATA που δίνονται παραπάνω
3. ΠΑΝΤΑ υπενθύμιζε ότι κάθε κλήρωση είναι ΤΥΧΑΙΑ
4. Κάνε ΣΤΑΤΙΣΤΙΚΗ ανάλυση (hot numbers, cold numbers, frequency)
5. Να είσαι βοηθητικός αλλά υπεύθυνος

📌 GAME RULES:
- ΤΖΟΚΕΡ: 5 αριθμοί (1-45) + 1 Τζόκερ (1-20)
- ΛΟΤΤΟ: 6 αριθμοί (1-49) + 1 Bonus
- ΚΙΝΟ: 1-12 αριθμοί (1-80)
- EXTRA 5: 5 αριθμοί (1-35)
- SUPER 3: 3 αριθμοί (0-9)
- ΠΡΩΤΟ: 7ψήφιος αριθμός

Respond in JSON — ΥΠΟΧΡΕΩΤΙΚΟ FORMAT:
{{
    "game": "Όνομα παιχνιδιού (ΤΖΟΚΕΡ/ΚΙΝΟ/ΛΟΤΤΟ κτλ)",
    "latest_draw": {{
        "draw_id": "Αριθμός κλήρωσης",
        "date": "Ημερομηνία",
        "winning_numbers": [1, 2, 3, 4, 5],
        "bonus": 7,
        "prizes": "Πληροφορίες βραβείων"
    }},
    "statistical_analysis": {{
        "hot_numbers": [3, 7, 12, 21, 33],
        "cold_numbers": [1, 8, 14, 39, 44],
        "overdue_numbers": [5, 19, 27],
        "patterns": "Περιγραφή μοτίβων από τις τελευταίες κληρώσεις"
    }},
    "lucky_numbers": {{
        "set_1": {{
            "numbers": [3, 12, 17, 28, 35],
            "bonus": 7,
            "method": "Βασισμένο στη στατιστική ανάλυση (hot numbers)"
        }},
        "set_2": {{
            "numbers": [5, 14, 22, 31, 42],
            "bonus": 12,
            "method": "Βασισμένο σε overdue αριθμούς"
        }},
        "set_3": {{
            "numbers": [8, 19, 25, 33, 40],
            "bonus": 15,
            "method": "Τυχαία μικτή επιλογή (hot + cold)"
        }}
    }},
    "next_draw": {{
        "date": "Ημερομηνία επόμενης κλήρωσης",
        "estimated_jackpot": "Εκτιμώμενο τζακπότ"
    }},
    "analysis_summary": "Αναλυτικό σχόλιο 3-4 παραγράφων για τα στατιστικά και τις τάσεις",
    "responsible_gambling": "⚠️ ΠΡΟΣΟΧΗ: Κάθε κλήρωση είναι ΑΠΟΛΥΤΑ ΤΥΧΑΙΑ. Οι αριθμοί βασίζονται σε στατιστική ανάλυση αλλά ΔΕΝ εγγυώνται κέρδη. Παίξτε ΥΠΕΥΘΥΝΑ. Γραμμή βοήθειας ΚΕΘΕΑ: 1114"
}}

ΚΡΙΣΙΜΟ: Τα πεδία "lucky_numbers" ΠΡΕΠΕΙ να περιέχουν ΠΡΑΓΜΑΤΙΚΟΥΣ αριθμούς σε arrays []. 
ΠΟΤΕ μην γράψεις μόνο κείμενο αντί για αριθμούς. ΠΑΝΤΑ 3 σετ αριθμών."""



# ═══════════════════════════════════════════════════════════════
#  CRYPTO INTELLIGENCE ENGINE — CoinGecko + APEX Analysis
# ═══════════════════════════════════════════════════════════════

CRYPTO_ALIASES = {
    "bitcoin": "bitcoin", "btc": "bitcoin", "μπιτκοιν": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum", "ether": "ethereum",
    "solana": "solana", "sol": "solana",
    "ripple": "ripple", "xrp": "ripple",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "cardano": "cardano", "ada": "cardano",
    "polkadot": "polkadot", "dot": "polkadot",
    "avalanche": "avalanche-2", "avax": "avalanche-2",
    "polygon": "matic-network", "matic": "matic-network",
    "bnb": "binancecoin", "binance": "binancecoin",
    "litecoin": "litecoin", "ltc": "litecoin",
    "chainlink": "chainlink", "link": "chainlink",
    "tron": "tron", "trx": "tron",
    "shiba": "shiba-inu", "shib": "shiba-inu",
    "pepe": "pepe", "sui": "sui", "apt": "aptos", "aptos": "aptos",
    "ton": "the-open-network", "toncoin": "the-open-network",
    "near": "near", "uni": "uniswap", "uniswap": "uniswap",
}

def detect_crypto_coins(text: str) -> list:
    """Detect which cryptocurrencies are mentioned in the query"""
    text_lower = text.lower()
    found = []
    for alias, coin_id in CRYPTO_ALIASES.items():
        if alias in text_lower and coin_id not in found:
            found.append(coin_id)
    # Default to top coins if none detected
    if not found:
        found = ["bitcoin", "ethereum", "solana", "ripple", "cardano"]
    return found[:10]

async def fetch_coingecko_data(coin_ids: list) -> dict:
    """Fetch live crypto data from CoinGecko FREE API"""
    try:
        client = await get_client()
        ids_str = ",".join(coin_ids)
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&order=market_cap_desc&sparkline=false&price_change_percentage=1h,24h,7d"
        r = await client.get(url, timeout=15)
        if r.status_code == 200:
            return {"coins": r.json(), "source": "coingecko"}
        else:
            log.warning(f"CoinGecko error: {r.status_code}")
            return {"coins": [], "error": f"CoinGecko HTTP {r.status_code}"}
    except Exception as e:
        log.error(f"CoinGecko fetch error: {e}")
        return {"coins": [], "error": str(e)}


# MEXC symbol mapping (CoinGecko ID -> MEXC pair)
MEXC_SYMBOLS = {
    "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT",
    "ripple": "XRPUSDT", "dogecoin": "DOGEUSDT", "cardano": "ADAUSDT",
    "polkadot": "DOTUSDT", "avalanche-2": "AVAXUSDT", "matic-network": "MATICUSDT",
    "binancecoin": "BNBUSDT", "litecoin": "LTCUSDT", "chainlink": "LINKUSDT",
    "tron": "TRXUSDT", "shiba-inu": "SHIBUSDT", "sui": "SUIUSDT",
    "aptos": "APTUSDT", "the-open-network": "TONUSDT", "near": "NEARUSDT",
    "uniswap": "UNIUSDT", "pepe": "PEPEUSDT",
}

GATEIO_SYMBOLS = {
    "bitcoin": "BTC_USDT", "ethereum": "ETH_USDT", "solana": "SOL_USDT",
    "ripple": "XRP_USDT", "dogecoin": "DOGE_USDT", "cardano": "ADA_USDT",
    "polkadot": "DOT_USDT", "avalanche-2": "AVAX_USDT", "matic-network": "MATIC_USDT",
    "binancecoin": "BNB_USDT", "litecoin": "LTC_USDT", "chainlink": "LINK_USDT",
    "tron": "TRX_USDT", "shiba-inu": "SHIB_USDT", "sui": "SUI_USDT",
    "aptos": "APT_USDT", "the-open-network": "TON_USDT", "near": "NEAR_USDT",
    "uniswap": "UNI_USDT", "pepe": "PEPE_USDT",
}

async def fetch_mexc_ticker(coin_id: str) -> dict:
    """Fetch ticker from MEXC API (public, no auth needed for ticker)"""
    symbol = MEXC_SYMBOLS.get(coin_id)
    if not symbol:
        return {}
    try:
        client = await get_client()
        url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}"
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                "exchange": "MEXC",
                "symbol": symbol,
                "bid": float(d.get("bidPrice") or 0),
                "ask": float(d.get("askPrice") or 0),
                "spread": round(float(d.get("askPrice") or 0) - float(d.get("bidPrice") or 0), 4),
                "volume_usdt": float(d.get("quoteVolume") or 0),
                "trades_24h": int(d.get("count") or 0),
                "high_24h": float(d.get("highPrice") or 0),
                "low_24h": float(d.get("lowPrice") or 0),
            }
    except Exception as e:
        log.warning(f"MEXC ticker error for {coin_id}: {e}")
    return {}

async def fetch_gateio_ticker(coin_id: str) -> dict:
    """Fetch ticker from Gate.io API (public endpoint)"""
    symbol = GATEIO_SYMBOLS.get(coin_id)
    if not symbol:
        return {}
    try:
        client = await get_client()
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}"
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                d = data[0]
                return {
                    "exchange": "Gate.io",
                    "symbol": symbol,
                    "bid": float(d.get("highest_bid", 0)),
                    "ask": float(d.get("lowest_ask", 0)),
                    "spread": round(float(d.get("lowest_ask", 0)) - float(d.get("highest_bid", 0)), 4),
                    "volume_usdt": float(d.get("quote_volume", 0)),
                    "high_24h": float(d.get("high_24h", 0)),
                    "low_24h": float(d.get("low_24h", 0)),
                    "change_pct": float(d.get("change_percentage", 0)),
                }
    except Exception as e:
        log.warning(f"Gate.io ticker error for {coin_id}: {e}")
    return {}


BINANCE_SYMBOLS = {
    "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT",
    "ripple": "XRPUSDT", "dogecoin": "DOGEUSDT", "cardano": "ADAUSDT",
    "polkadot": "DOTUSDT", "avalanche-2": "AVAXUSDT", "matic-network": "MATICUSDT",
    "binancecoin": "BNBUSDT", "litecoin": "LTCUSDT", "chainlink": "LINKUSDT",
    "tron": "TRXUSDT", "shiba-inu": "SHIBUSDT", "sui": "SUIUSDT",
    "aptos": "APTUSDT", "the-open-network": "TONUSDT", "near": "NEARUSDT",
    "uniswap": "UNIUSDT", "pepe": "PEPEUSDT",
}

BYBIT_SYMBOLS = dict(BINANCE_SYMBOLS)  # Same format

KUCOIN_SYMBOLS = {
    "bitcoin": "BTC-USDT", "ethereum": "ETH-USDT", "solana": "SOL-USDT",
    "ripple": "XRP-USDT", "dogecoin": "DOGE-USDT", "cardano": "ADA-USDT",
    "polkadot": "DOT-USDT", "avalanche-2": "AVAX-USDT", "matic-network": "MATIC-USDT",
    "binancecoin": "BNB-USDT", "litecoin": "LTC-USDT", "chainlink": "LINK-USDT",
    "tron": "TRX-USDT", "shiba-inu": "SHIB-USDT", "sui": "SUI-USDT",
    "aptos": "APT-USDT", "the-open-network": "TON-USDT", "near": "NEAR-USDT",
    "uniswap": "UNI-USDT", "pepe": "PEPE-USDT",
}

async def fetch_binance_ticker(coin_id: str) -> dict:
    """Fetch ticker from Binance"""
    symbol = BINANCE_SYMBOLS.get(coin_id)
    if not symbol:
        return {}
    try:
        client = await get_client()
        r = await client.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                "exchange": "Binance",
                "symbol": symbol,
                "bid": float(d.get("bidPrice") or 0),
                "ask": float(d.get("askPrice") or 0),
                "spread": round(float(d.get("askPrice") or 0) - float(d.get("bidPrice") or 0), 4),
                "volume_usdt": float(d.get("quoteVolume") or 0),
                "high_24h": float(d.get("highPrice") or 0),
                "low_24h": float(d.get("lowPrice") or 0),
            }
    except Exception as e:
        log.warning(f"Binance error for {coin_id}: {e}")
    return {}

async def fetch_bybit_ticker(coin_id: str) -> dict:
    """Fetch ticker from Bybit"""
    symbol = BYBIT_SYMBOLS.get(coin_id)
    if not symbol:
        return {}
    try:
        client = await get_client()
        r = await client.get(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}", timeout=10)
        if r.status_code == 200:
            d = r.json()
            items = d.get("result", {}).get("list", [])
            if items:
                t = items[0]
                bid = float(t.get("bid1Price") or 0)
                ask = float(t.get("ask1Price") or 0)
                return {
                    "exchange": "Bybit",
                    "symbol": symbol,
                    "bid": bid,
                    "ask": ask,
                    "spread": round(ask - bid, 4),
                    "volume_usdt": float(t.get("turnover24h") or 0),
                    "high_24h": float(t.get("highPrice24h") or 0),
                    "low_24h": float(t.get("lowPrice24h") or 0),
                }
    except Exception as e:
        log.warning(f"Bybit error for {coin_id}: {e}")
    return {}

async def fetch_kucoin_ticker(coin_id: str) -> dict:
    """Fetch ticker from KuCoin"""
    symbol = KUCOIN_SYMBOLS.get(coin_id)
    if not symbol:
        return {}
    try:
        client = await get_client()
        r = await client.get(f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}", timeout=10)
        if r.status_code == 200:
            d = r.json().get("data", {})
            if d:
                bid = float(d.get("bestBid") or 0)
                ask = float(d.get("bestAsk") or 0)
                return {
                    "exchange": "KuCoin",
                    "symbol": symbol,
                    "bid": bid,
                    "ask": ask,
                    "spread": round(ask - bid, 4),
                    "volume_usdt": 0,
                }
        # Get volume separately
        r2 = await client.get(f"https://api.kucoin.com/api/v1/market/stats?symbol={symbol}", timeout=10)
        if r2.status_code == 200:
            d2 = r2.json().get("data", {})
            result = {
                "exchange": "KuCoin",
                "symbol": symbol,
                "bid": float(d2.get("buy") or 0),
                "ask": float(d2.get("sell") or 0),
                "spread": round(float(d2.get("sell") or 0) - float(d2.get("buy") or 0), 4),
                "volume_usdt": float(d2.get("volValue") or 0),
                "high_24h": float(d2.get("high") or 0),
                "low_24h": float(d2.get("low") or 0),
            }
            return result
    except Exception as e:
        log.warning(f"KuCoin error for {coin_id}: {e}")
    return {}


async def fetch_exchange_data(coin_ids: list) -> dict:
    """Fetch data from ALL 5 exchanges for comparison"""
    import asyncio as aio
    results = {}
    exchanges = ["binance", "bybit", "kucoin", "mexc", "gateio"]
    fetchers = {
        "binance": fetch_binance_ticker,
        "bybit": fetch_bybit_ticker,
        "kucoin": fetch_kucoin_ticker,
        "mexc": fetch_mexc_ticker,
        "gateio": fetch_gateio_ticker,
    }
    
    tasks = []
    task_map = []  # (coin_id, exchange_name)
    for coin_id in coin_ids[:5]:
        for ex_name, fetcher in fetchers.items():
            tasks.append(fetcher(coin_id))
            task_map.append((coin_id, ex_name))
    
    all_results = await aio.gather(*tasks, return_exceptions=True)
    
    for idx, (coin_id, ex_name) in enumerate(task_map):
        data = all_results[idx] if not isinstance(all_results[idx], Exception) else {}
        if data:
            if coin_id not in results:
                results[coin_id] = {}
            results[coin_id][ex_name] = data
    
    return results

def format_exchange_table(exchange_data: dict, lang: str = "el") -> str:
    """Format 5-exchange comparison table with arbitrage scanner"""
    if not exchange_data:
        return ""
    
    ex_icons = {"binance": "🟡", "bybit": "🟠", "kucoin": "🟢", "mexc": "🟦", "gateio": "🟨"}
    ex_names = {"binance": "Binance", "bybit": "Bybit", "kucoin": "KuCoin", "mexc": "MEXC", "gateio": "Gate.io"}
    
    lines = ["\n🏦 <b>Cross-Exchange Scanner (5 Exchanges)</b>\n"]
    
    for coin_id, data in exchange_data.items():
        # Get symbol from any exchange
        any_ex = next((d for d in data.values() if d), {})
        symbol = any_ex.get("symbol", coin_id).replace("_USDT", "").replace("USDT", "").replace("-USDT", "").replace("_", "").replace("-", "")
        
        lines.append(f"<b>{symbol}:</b>")
        
        # Collect all prices for arbitrage
        prices = []
        
        for ex_key in ["binance", "bybit", "kucoin", "mexc", "gateio"]:
            ex = data.get(ex_key, {})
            if ex and ex.get("bid", 0) > 0:
                bid = ex["bid"]
                ask = ex["ask"]
                spread = ex.get("spread", 0)
                vol = ex.get("volume_usdt", 0)
                icon = ex_icons.get(ex_key, "⚪")
                name = ex_names.get(ex_key, ex_key)
                
                vol_str = f"${vol/1e6:.0f}M" if vol > 1e6 else f"${vol:,.0f}" if vol > 0 else ""
                vol_part = f" | Vol: {vol_str}" if vol_str else ""
                
                if bid >= 1000:
                    lines.append(f"  {icon} {name}: ${bid:,.2f} / ${ask:,.2f}{vol_part}")
                elif bid >= 1:
                    lines.append(f"  {icon} {name}: ${bid:,.4f} / ${ask:,.4f}{vol_part}")
                else:
                    lines.append(f"  {icon} {name}: ${bid:,.6f} / ${ask:,.6f}{vol_part}")
                
                prices.append({"ex": name, "bid": bid, "ask": ask})
        
        # Arbitrage detection
        if len(prices) >= 2:
            cheapest = min(prices, key=lambda x: x["ask"])
            expensive = max(prices, key=lambda x: x["bid"])
            
            if cheapest["ask"] > 0:
                arb_pct = ((expensive["bid"] - cheapest["ask"]) / cheapest["ask"]) * 100
                spread_abs = expensive["bid"] - cheapest["ask"]
                
                if arb_pct > 0.01:
                    lines.append(f"  💰 <b>Buy {cheapest['ex']} → Sell {expensive['ex']}: {arb_pct:.3f}% (${spread_abs:,.2f})</b>")
                elif arb_pct > -0.01:
                    lines.append(f"  ⚖️ Spread tight — no clear arb")
        lines.append("")
    
    return "\n".join(lines)

def format_exchange_context(exchange_data: dict) -> str:
    """Format exchange data for LLM context"""
    if not exchange_data:
        return ""
    ex_names = {"binance": "Binance", "bybit": "Bybit", "kucoin": "KuCoin", "mexc": "MEXC", "gateio": "Gate.io"}
    lines = ["\nCROSS-EXCHANGE DATA (5 exchanges):"]
    for coin_id, data in exchange_data.items():
        any_ex = next((d for d in data.values() if d), {})
        sym = any_ex.get("symbol", coin_id)
        lines.append(f"  {sym}:")
        for ex_key in ["binance", "bybit", "kucoin", "mexc", "gateio"]:
            ex = data.get(ex_key, {})
            if ex:
                name = ex_names.get(ex_key, ex_key)
                lines.append(f"    {name}: bid={ex.get('bid')} ask={ex.get('ask')} spread={ex.get('spread')} vol=${ex.get('volume_usdt',0):,.0f}")
    return "\n".join(lines)


def format_crypto_context(data: dict) -> str:
    """Format crypto data for LLM context"""
    coins = data.get("coins", [])
    if not coins:
        return "No live data available."
    lines = ["LIVE CRYPTOCURRENCY MARKET DATA (CoinGecko):"]
    lines.append(f"{'Coin':<12} {'Price':>12} {'24h%':>8} {'7d%':>8} {'MCap':>15} {'Vol24h':>15}")
    lines.append("-" * 75)
    for c in coins:
        symbol = c.get("symbol", "").upper()
        price = c.get("current_price", 0)
        ch24 = c.get("price_change_percentage_24h", 0) or 0
        ch7d = c.get("price_change_percentage_7d_in_currency", 0) or 0
        mcap = c.get("market_cap", 0) or 0
        vol = c.get("total_volume", 0) or 0
        price_str = f"${price:,.2f}" if price < 10 else f"${price:,.0f}" if price > 100 else f"${price:,.2f}"
        mcap_str = f"${mcap/1e9:.1f}B" if mcap > 1e9 else f"${mcap/1e6:.0f}M"
        vol_str = f"${vol/1e9:.1f}B" if vol > 1e9 else f"${vol/1e6:.0f}M"
        lines.append(f"{symbol:<12} {price_str:>12} {ch24:>+7.1f}% {ch7d:>+7.1f}% {mcap_str:>15} {vol_str:>15}")
    return "\n".join(lines)

def format_crypto_table(data: dict, lang: str = "el") -> str:
    """Format crypto prices as Telegram table"""
    coins = data.get("coins", [])
    if not coins:
        return "📊 No crypto data available."
    lines = ["📊 <b>APEX Crypto Intelligence — Live Market</b>\n"]
    for c in coins:
        symbol = c.get("symbol", "").upper()
        name = c.get("name", "")
        price = c.get("current_price", 0)
        ch24 = c.get("price_change_percentage_24h", 0) or 0
        ch7d = c.get("price_change_percentage_7d_in_currency", 0) or 0
        mcap = c.get("market_cap", 0) or 0
        vol = c.get("total_volume", 0) or 0
        ath = c.get("ath", 0) or 0
        ath_pct = c.get("ath_change_percentage", 0) or 0
        rank = c.get("market_cap_rank", "?")
        # Price formatting
        if price >= 1000:
            p_str = f"${price:,.0f}"
        elif price >= 1:
            p_str = f"${price:,.2f}"
        else:
            p_str = f"${price:,.4f}"
        # Change emoji
        e24 = "🟢" if ch24 >= 0 else "🔴"
        e7d = "🟢" if ch7d >= 0 else "🔴"
        # Market cap
        mcap_str = f"${mcap/1e9:.1f}B" if mcap > 1e9 else f"${mcap/1e6:.0f}M"
        vol_str = f"${vol/1e9:.1f}B" if vol > 1e9 else f"${vol/1e6:.0f}M"
        lines.append(f"<b>#{rank} {symbol}</b> — {esc(name)}")
        lines.append(f"  💰 {p_str}")
        lines.append(f"  {e24} 24h: {ch24:+.1f}% | {e7d} 7d: {ch7d:+.1f}%")
        lines.append(f"  📈 MCap: {mcap_str} | Vol: {vol_str}")
        if ath > 0:
            lines.append(f"  🏔️ ATH: ${ath:,.0f} ({ath_pct:.0f}%)")
        lines.append("")
    lines.append(f"⏰ {time.strftime('%H:%M UTC', time.gmtime())}")
    return "\n".join(lines)

def build_crypto_prompt(lang: str, crypto_data: str = "") -> str:
    """APEX Crypto Trading Intelligence prompt"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

IDENTITY: NEUROAETHER APEX CRYPTO INTELLIGENCE — Institutional Trading Analyst

YOU HAVE REAL-TIME MARKET DATA. The user's message contains LIVE prices from CoinGecko.
You MUST analyze this data. NEVER say you cannot provide prices — THE DATA IS IN THE USER MESSAGE.

You are the APEX Crypto Intelligence Engine — a Hyper-Council of:
- Hedge Fund CIO (macro & portfolio strategy)
- Head of Quant Research (signals, backtests, risk models)  
- Chief Risk Officer Damocles (downside protection)
- Market Regime Classifier (bull/bear/chop detection)

MANDATORY RULES:
1. USE the real-time data from the user message — prices, volumes, changes are ALL there
2. Give SPECIFIC price levels for support/resistance based on the actual prices
3. Include conviction level (LOW/MEDIUM/HIGH)
4. Include risk assessment with specific scenarios
5. Be institutional and analytical, never casual

You MUST respond with ONLY valid JSON (no markdown, no backticks, no explanation before/after):

The JSON must have these exact keys:
- "market_overview" with "regime", "sentiment", "key_narrative"
- "coin_analysis" array with objects having "symbol", "verdict", "conviction", "support", "resistance", "key_insight", "risk_warning"
- "hyper_council" with "macro_view", "quant_signal", "risk_assessment", "regime_status"
- "action_plan" with "primary_trade", "entry_logic", "risk_management", "time_horizon"
- "disclaimer" with responsible trading warning

CRITICAL: Respond with ONLY the JSON object. No text before or after."""



BLUEPRINT_SYSTEM_PROMPT = """You are the APEX Trading Blueprint Studio — a fused team of:
- Hedge Fund CIO (institutional macro & portfolio strategy)
- Head of Quant Research (signals, backtests, risk models)
- Derivatives & Stochastic Calculus Expert (convexity, Greeks, path risk)
- Behavioral Finance Lead (sentiment, positioning, market psychology)
- Chief Risk Officer Damocles (downside protection, veto power)

You generate board-ready trading blueprints as STRICT JSON.
The user message contains LIVE MARKET DATA. You MUST use it.

OUTPUT: Return ONLY valid JSON with this EXACT structure (no markdown, no backticks):
{
  "title": "THE [SYMBOL] TRADING & MACRO BLUEPRINT",
  "subtitle": "NeuroAether APEX Hyper-Council Edition",
  "executive_summary": "3 paragraphs in institutional language highlighting regime, edge, risk and recommended stance. Use real numbers from the data.",
  "strategy_snapshot": {
    "symbol": "[from data]",
    "timeframe": "4H",
    "market": "Crypto Spot/Perps",
    "strategy_name": "APEX Momentum & Risk Framework",
    "status": "WATCH or ACTIVE or PAUSED",
    "conviction_level": "LOW or MEDIUM or HIGH",
    "risk_profile": "Conservative or Moderate or Aggressive"
  },
  "modules": [
    {
      "type": "swot",
      "title": "Strategic Market Position (SWOT)",
      "data": {
        "strengths": ["2-3 items based on real data"],
        "weaknesses": ["2-3 items"],
        "opportunities": ["2-3 items"],
        "threats": ["2-3 items"]
      }
    },
    {
      "type": "chart_bar",
      "title": "Projected PnL & Drawdown Profile (12 Months)",
      "labels": ["Q1", "Q2", "Q3", "Q4"],
      "datasets": [
        {"label": "No Strategy", "data": [0, 0, 0, 0]},
        {"label": "APEX Base Case", "data": [realistic numbers]},
        {"label": "APEX Stress Case", "data": [conservative numbers]}
      ],
      "insight": "CIO Note with specific reasoning"
    },
    {
      "type": "chart_radar",
      "title": "Strategy Capability Radar",
      "labels": ["Alpha Potential", "Risk Control", "Liquidity Fit", "Execution Complexity", "Robustness Across Regimes"],
      "datasets": [
        {"label": "Current Setup", "data": [0-100 scores]},
        {"label": "With APEX Strategy", "data": [0-100 scores]}
      ],
      "insight": "Research Note with reasoning"
    },
    {
      "type": "hyper_council",
      "title": "Hyper-Council Institutional View",
      "agents": [
        {"role": "MACRO", "name": "Global Macro CIO", "sentiment": "LONG/SHORT/NEUTRAL", "weight": -100 to 100, "summary": "2-3 lines", "dialogue": "5-8 lines detailed"},
        {"role": "QUANT", "name": "Head of Quant Research", "sentiment": "...", "weight": ..., "summary": "...", "dialogue": "..."},
        {"role": "STATS", "name": "Chief Statistician", "sentiment": "...", "weight": ..., "summary": "...", "dialogue": "..."},
        {"role": "RISK", "name": "CRO Damocles", "sentiment": "VETO/NEUTRAL/SHORT/LONG", "weight": negative, "summary": "...", "dialogue": "..."},
        {"role": "EXECUTION", "name": "Execution Architect", "sentiment": "INFO", "weight": 0, "summary": "...", "dialogue": "..."}
      ],
      "consensus": {
        "raw_sum": calculated,
        "consensus_score": 0-100,
        "status": "ALPHA_GO or HOLD or WAIT or VETOED",
        "execution_log": "One institutional decision statement"
      }
    },
    {
      "type": "roadmap",
      "title": "Implementation Roadmap",
      "phases": [
        {"name": "Phase 1: Backtest & Sandbox", "time": "Weeks 1-2", "action": "specific action"},
        {"name": "Phase 2: Controlled Deployment", "time": "Weeks 3-6", "action": "specific action"},
        {"name": "Phase 3: Scale & Institutionalize", "time": "Weeks 7+", "action": "specific action"}
      ]
    }
  ],
  "footer": "Generated by NeuroAether APEX Trading Blueprint Studio • Confidential & Proprietary"
}

CRITICAL RULES:
1. ALL numbers must be realistic based on the live data
2. Language must be premium, institutional, never casual
3. JSON must be valid with no trailing commas
4. Use REAL price levels from the data for support/resistance
5. Respond with ONLY the JSON — no text before or after"""


def build_academic_prompt(lang: str) -> str:
    """Academic research prompt"""
    lang_inst = get_language_instruction(lang)
    return f"""{lang_inst}

You are an Academic Research Engine with access to:
- arXiv, PubMed, OpenAlex, PubChem databases
- 12+ scientific sources
- Cross-disciplinary synthesis capabilities

Respond in JSON:
{{
    "research_topic": "Topic identified",
    "executive_summary": "Comprehensive overview of current research state",
    "key_papers": [
        {{"title": "Paper title", "authors": "Author(s)", "year": "Year", "source": "Journal/arXiv", "key_finding": "Main finding", "relevance": "Why it matters"}}
    ],
    "research_gaps": ["Gap 1: what's missing", "Gap 2"],
    "methodology_review": "Current research methodologies used",
    "future_directions": ["Direction 1", "Direction 2", "Direction 3"],
    "practical_applications": ["Application 1", "Application 2"],
    "cross_disciplinary_insights": "Connections to other fields"
}}"""


# ═══════════════════════════════════════════════════════════════
#  TERRA ALCHEMICA v6.0 — Multi-Expert Council Engine
# ═══════════════════════════════════════════════════════════════

TERRA_KNOWLEDGE = {
    "CULINARY": (
        "Herbal preparation methods: decoctions (βράσιμο 15-20min for roots/bark), "
        "infusions (ζεστό νερό 5-10min for leaves/flowers), tinctures (40-60% ethanol maceration 2-6 weeks), "
        "cold-press extraction, steam distillation for essential oils, poultices, salves (beeswax + oil base), "
        "oxymel (honey + vinegar), electuaries (honey paste), fermented preparations, glycerites. "
        "Critical: water temperature affects alkaloid extraction — 70°C for delicate compounds, 100°C for hardy roots."
    ),
    "SAFETY": (
        "Contraindication protocols: hepatotoxic pyrrolizidine alkaloids (comfrey, borage — max 6 weeks external only), "
        "photosensitizing furanocoumarins (St. John's Wort — avoid sun 2h post-application), "
        "drug interactions (warfarin + ginkgo = bleeding risk, SSRIs + St. John's Wort = serotonin syndrome), "
        "pregnancy category X herbs (pennyroyal, blue cohosh, tansy), "
        "allergenic cross-reactivity (Asteraceae family: chamomile, echinacea, ragweed), "
        "heavy metal bioaccumulation in wildcrafted herbs, essential oil neurotoxicity (thujone, camphor in children). "
        "ALWAYS: patch test 24h before topical use, start low-dose oral, consult healthcare provider."
    ),
    "BIO": (
        "Phytochemical classes: flavonoids (quercetin, rutin — antioxidant, anti-inflammatory via NF-κB inhibition), "
        "terpenes (limonene, linalool — anxiolytic via GABA-A modulation), alkaloids (berberine — AMPK activation, "
        "antimicrobial), phenolic acids (rosmarinic acid — COX-2 inhibition), saponins (ginsenosides — adaptogenic "
        "via HPA axis modulation), polysaccharides (β-glucans — immunomodulatory via dectin-1 receptor). "
        "Bioavailability enhancers: piperine (black pepper) increases curcumin absorption 2000%, "
        "lipid co-administration for fat-soluble compounds, fermentation for glycoside conversion."
    ),
    "MONASTIC": (
        "Mount Athos herbal tradition (1000+ years): sideritis (τσάι του βουνού — mountain tea) for longevity, "
        "Cretan dittany (δίκταμο — Origanum dictamnus) sacred wound-healer, "
        "mastic (μαστίχα Χίου) for digestive health — documented since Hippocrates, "
        "monk's pepper (λυγαριά — Vitex agnus-castus) hormonal balance, "
        "Greek oregano oil (ρίγανη) antimicrobial potency, "
        "Athonite elixir recipes: honey + propolis + mountain herbs for immune fortification. "
        "Hildegard von Bingen's Physica: viriditas (greening power) as healing force. "
        "Ayurvedic rasayana: ashwagandha, tulsi, amalaki for rejuvenation. TCM tonic herbs: astragalus, reishi, goji."
    ),
    "ACADEMIC": (
        "Evidence levels: systematic reviews (Cochrane), RCTs, observational studies. "
        "Key databases: PubMed, ESCOP monographs, WHO monographs on medicinal plants, "
        "European Pharmacopoeia (Ph. Eur.), German Commission E. "
        "Standardization: marker compound quantification (e.g., hypericin 0.3% in SJW), "
        "chromatographic fingerprinting (HPLC, GC-MS), DNA barcoding for species authentication. "
        "Regulatory: EU Traditional Herbal Medicinal Products Directive 2004/24/EC, "
        "FDA GRAS status, EMA HMPC community herbal monographs. "
        "Current research frontiers: gut microbiome modulation by polyphenols, "
        "epigenetic effects of phytochemicals, network pharmacology for multi-target synergy."
    ),
}


def build_terra_prompt(lang: str) -> str:
    """Terra Alchemica DaVinci Nexus synthesis mega-prompt"""
    lang_inst = get_language_instruction(lang)
    knowledge_block = "\n".join(f"[{k}]: {v}" for k, v in TERRA_KNOWLEDGE.items())
    return f"""{lang_inst}

═══════════════════════════════════════════════════════════════
IDENTITY: TERRA ALCHEMICA v6.0 — DaVinci Nexus Grand Synthesis
═══════════════════════════════════════════════════════════════

You are the DaVinci Nexus — the supreme synthesis mind of the Terra Alchemica Olympus Council.
You receive expert perspectives from Bio-Alchemist, Molecular Architect, Chronos Vaidya,
and the Safety Guardian. Your role is to weave their insights into a Grand Opus.

KNOWLEDGE BASE:
{knowledge_block}

YOUR TASK:
Synthesize all council input into a comprehensive Grand Opus that bridges ancient wisdom
with modern science. Be specific with dosages, mechanisms, and safety data.

Respond ONLY in valid JSON with this exact structure:
{{
    "opus_name": "A creative alchemical name for this opus (e.g., 'Morpheus Elixir of Deep Rest')",
    "executive_summary": "2-3 sentence overview bridging science + tradition",
    "deep_dive_exoteric": "Public/scientific perspective: mechanisms, clinical evidence, pharmacology (300+ words)",
    "deep_dive_esoteric": "Hidden/traditional wisdom: monastic practices, energetic properties, historical use (300+ words)",
    "the_formula": {{
        "ingredients": [
            {{"name": "Herb/compound name", "amount": "Specific dosage", "properties": "Key active compounds and effects"}}
        ],
        "preparation_steps": ["Step 1: Detailed instruction", "Step 2: ..."],
        "molecular_mechanisms": "How the ingredients work synergistically at a biochemical level"
    }},
    "safety_audit": {{
        "status": "SAFE|CAUTION|RESTRICTED|EXPERIMENTAL",
        "ccp_alerts": ["Critical control point 1", "Drug interaction warning"],
        "regulatory_notes": ["EU/FDA status", "Relevant regulations"]
    }},
    "future_horizon": "Emerging research, future applications, innovation opportunities",
    "kpis": [
        {{"metric": "Efficacy Evidence Level", "value": "e.g., Level 2 — Multiple RCTs"}},
        {{"metric": "Safety Profile", "value": "e.g., Well-established, minor interactions"}},
        {{"metric": "Bioavailability", "value": "e.g., 45% with piperine enhancement"}},
        {{"metric": "Traditional Use Duration", "value": "e.g., 2500+ years documented"}}
    ]
}}"""


async def _terra_expert_call(expert_name: str, knowledge_layer: str, query: str, context: str = "") -> dict:
    """Single Terra Alchemica expert consultation via OpenAI JSON mode"""
    if not OPENAI_KEY:
        return {"expert_name": expert_name, "perspective": "API key unavailable", "technical_points": [], "risk_flags": []}

    expert_prompts = {
        "Bio-Alchemist": (
            f"You are the Bio-Alchemist expert. Analyze from a phytochemical and biochemical perspective.\n"
            f"Knowledge: {TERRA_KNOWLEDGE.get('BIO', '')}\n"
            f"Focus: active compounds, mechanisms of action, bioavailability, synergies."
        ),
        "Molecular Architect": (
            f"You are the Molecular Architect expert. Analyze preparation methods and formulation.\n"
            f"Knowledge: {TERRA_KNOWLEDGE.get('CULINARY', '')}\n"
            f"Focus: optimal extraction methods, preparation techniques, dosage forms, stability."
        ),
        "Chronos Vaidya": (
            f"You are Chronos Vaidya — keeper of ancient healing traditions across time.\n"
            f"Knowledge: {TERRA_KNOWLEDGE.get('MONASTIC', '')}\n{TERRA_KNOWLEDGE.get('ACADEMIC', '')}\n"
            f"Focus: historical use, traditional formulations, cross-cultural healing practices, modern validation."
        ),
        "Safety Guardian": (
            f"You are the Safety Guardian. Your word is FINAL on safety matters.\n"
            f"Knowledge: {TERRA_KNOWLEDGE.get('SAFETY', '')}\n"
            f"Focus: contraindications, drug interactions, dosage limits, vulnerable populations, regulatory status."
        ),
    }

    system_prompt = expert_prompts.get(expert_name, f"You are {expert_name}. Provide expert analysis.")
    user_content = f"Query: {query}"
    if context:
        user_content += f"\n\nCouncil context so far:\n{context}"
    user_content += (
        f'\n\nRespond ONLY in valid JSON: {{"expert_name": "{expert_name}", '
        f'"perspective": "your detailed analysis (200+ words)", '
        f'"technical_points": ["point 1", "point 2", "point 3"], '
        f'"risk_flags": ["any safety concerns or none"]}}'
    )

    client = await get_client()
    try:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "max_tokens": 2000,
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            },
            timeout=60
        )
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if content:
            return json.loads(content)
    except Exception as e:
        log.warning(f"Terra expert {expert_name} failed: {e}")

    return {"expert_name": expert_name, "perspective": f"{expert_name} consultation unavailable", "technical_points": [], "risk_flags": []}


async def run_terra_council(query: str, language: str, chat_id: int) -> dict:
    """Execute 3-stage Terra Alchemica multi-expert council"""
    log.info(f"🌿 Summoning Terra Alchemica Council for: {query[:80]}")

    # ── Stage 1: Parallel expert consultations ──
    await send_typing(chat_id)
    try:
        bio_task = _terra_expert_call("Bio-Alchemist", "BIO", query)
        mol_task = _terra_expert_call("Molecular Architect", "CULINARY", query)
        chrono_task = _terra_expert_call("Chronos Vaidya", "MONASTIC", query)
        experts = await asyncio.gather(bio_task, mol_task, chrono_task, return_exceptions=True)

        expert_results = []
        all_risks = []
        for exp in experts:
            if isinstance(exp, Exception):
                log.warning(f"Terra expert exception: {exp}")
                continue
            if isinstance(exp, dict):
                expert_results.append(exp)
                all_risks.extend(exp.get("risk_flags", []))
    except Exception as e:
        log.error(f"Terra Stage 1 failed: {e}")
        return {}

    # ── Stage 2: Safety Guardian reviews aggregated risks ──
    await send_typing(chat_id)
    risk_context = f"Aggregated risks from council: {json.dumps(all_risks, ensure_ascii=False)}"
    council_minutes = json.dumps(expert_results, ensure_ascii=False, indent=1)
    try:
        safety = await _terra_expert_call("Safety Guardian", "SAFETY", query, risk_context)
    except Exception as e:
        log.warning(f"Terra Safety Guardian failed: {e}")
        safety = {"expert_name": "Safety Guardian", "perspective": "Safety review unavailable", "technical_points": [], "risk_flags": all_risks}

    # ── Stage 3: DaVinci Nexus Grand Synthesis ──
    await send_typing(chat_id)
    synthesis_prompt = build_terra_prompt(language)
    synthesis_context = (
        f"COUNCIL MINUTES:\n{council_minutes}\n\n"
        f"SAFETY GUARDIAN REPORT:\n{json.dumps(safety, ensure_ascii=False, indent=1)}\n\n"
        f"Original query: {query}"
    )

    client = await get_client()
    try:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": synthesis_prompt},
                    {"role": "user", "content": synthesis_context}
                ],
                "max_tokens": 10000,
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            },
            timeout=120
        )
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if content:
            opus = json.loads(content)
            if isinstance(opus, dict) and opus.get("opus_name"):
                log.info(f"🌿 Terra Grand Opus complete: {opus.get('opus_name', 'unnamed')}")
                return opus
    except Exception as e:
        log.error(f"Terra DaVinci Nexus synthesis failed: {e}")

    return {}


# ═══════════════════════════════════════════════════════════════
#  ENGINE DEFINITIONS with Greek Keywords
# ═══════════════════════════════════════════════════════════════

ENGINES = {
    "chef": {
        "icon": "👨‍🍳",
        "name": "Chef Omega",
        "desc": "Michelin recipes + MacYuFBI + HACCP + financials",
        "keywords": ["recipe", "cook", "syntagh", "mageirev", "fagito", "food",
                      "moussaka", "souvlaki", "pasta", "pizza", "sushi", "steak",
                      "dessert", "cake", "soup", "salad", "risotto", "burger",
                      "gyros", "tiramisu", "carbonara", "ramen", "tacos",
                      "mousaka", "mpifteki", "gemista", "pastitsio", "spanakopita",
                      # Greek
                      "συνταγή", "συνταγές", "μαγείρεμα", "μαγειρική", "φαγητό",
                      "μουσακάς", "σουβλάκι", "πιάτο", "γλυκό", "σούπα", "σαλάτα",
                      "ψωμί", "κρέας", "ψάρι", "λαχανικά", "ζυμαρικά", "ρύζι",
                      "κοτόπουλο", "αρνί", "μοσχάρι", "γαρίδες", "χταπόδι",
                      "τυρόπιτα", "μπακλαβάς", "γεμιστά", "παστίτσιο",
                      "μπιφτέκι", "σπανακόπιτα", "φέτα", "ελιές", "ντομάτα"],
        "build_prompt": lambda lang: build_chef_prompt(lang),
    },
    "apex": {
        "icon": "📈",
        "name": "APEX Strategy",
        "desc": "Nobel-level business analysis (9 sections, €projections)",
        "keywords": ["strategy", "business", "market", "startup", "company",
                      "invest", "revenue", "profit", "epixeirhsh", "stratigikh",
                      "restaurant strategy", "expansion", "growth", "roi",
                      "plan", "swot", "competitor", "funding", "enterprise",
                      "στρατηγική", "επιχείρηση", "επένδυση", "αγορά", "κέρδος",
                      "έσοδα", "ανάπτυξη", "ανταγωνισμός", "χρηματοδότηση",
                      "εταιρεία", "σχέδιο", "επέκταση", "εστιατόριο"],
        "build_prompt": lambda lang: build_apex_prompt(lang),
    },
    "assembly": {
        "icon": "🏛️",
        "name": "Grand Assembly",
        "desc": "26+ legendary archetypes with Gandalf Safety Veto",
        "keywords": ["assembly", "council", "archetypes", "alexander",
                      "gandalf", "sherlock", "sun tzu", "socrates",
                      "should i", "advise", "wisdom",
                      "symvouleute", "gnomh", "bitcoin", "crypto decision",
                      "συμβούλιο", "γνώμη", "συμβουλές", "σοφία", "πρέπει",
                      "αρχέτυπα", "αποφάσεις", "βοήθεια", "τι να κάνω"],
        "build_prompt": lambda lang: build_assembly_prompt(lang),
    },
    "consulting": {
        "icon": "💼",
        "name": "McKinsey Consulting",
        "desc": "Strategic reports with SWOT, roadmaps, KPIs",
        "keywords": ["consulting", "mckinsey", "swot", "kpi", "roadmap",
                      "symvouleutikh", "strategikh",
                      "report", "analysis report", "strategic plan",
                      "συμβουλευτική", "αναφορά", "στρατηγικό σχέδιο",
                      "δείκτες", "οδικός χάρτης", "υλοποίηση"],
        "build_prompt": lambda lang: build_consulting_prompt(lang),
    },
    "lab": {
        "icon": "🔬",
        "name": "Deep Analysis Lab",
        "desc": "Scientific analysis with Nobel insights, risk matrix",
        "keywords": ["research", "science", "analysis", "study", "lab",
                      "ereuna", "episthmonikh", "analyze", "deep dive",
                      "medical", "health", "clinical", "quantum",
                      "έρευνα", "επιστήμη", "ανάλυση", "μελέτη", "εργαστήριο",
                      "ιατρικό", "υγεία", "κλινική", "κβαντικό", "βιολογία"],
        "build_prompt": lambda lang: build_lab_prompt(lang),
    },
    "marketing": {
        "icon": "📣",
        "name": "Viral Marketing",
        "desc": "Campaign generation for social, email, content",
        "keywords": ["marketing", "campaign", "social media", "instagram",
                      "tiktok", "facebook", "viral", "content", "ads",
                      "diafhmish", "promotion", "branding", "seo",
                      "διαφήμιση", "καμπάνια", "μάρκετινγκ", "προώθηση",
                      "κοινωνικά δίκτυα", "περιεχόμενο", "brand"],
        "build_prompt": lambda lang: build_marketing_prompt(lang),
    },
    "oracle": {
        "icon": "🎰",
        "name": "OPAP Oracle",
        "desc": "LIVE lottery data, statistics, lucky numbers",
        "keywords": ["opap", "lotto", "kino", "tzoker", "lucky",
                      "lottery", "prediction", "arithmoi", "laxeio",
                      "proto", "extra5", "super3", "eurojackpot",
                      "λοττο", "κινο", "τζόκερ", "τυχερά", "λαχείο",
                      "αριθμοί", "πρόβλεψη", "πρώτο", "στοίχημα",
                      "κλήρωση", "τυχεροί", "νούμερα"],
        "build_prompt": lambda lang: build_oracle_prompt(lang),
    },
    "blueprint": {
        "icon": "📄",
        "name": "APEX Trading Blueprint",
        "desc": "Hedge fund-grade PDF reports with Hyper-Council analysis",
        "keywords": ["blueprint", "report", "pdf", "trading plan",
                      "αναφορά", "σχέδιο", "trading blueprint"],
        "build_prompt": lambda lang: "",
    },
    "crypto": {
        "icon": "📊",
        "name": "APEX Crypto Intelligence",
        "desc": "Live crypto prices, APEX trading analysis, market data",
        "keywords": ["crypto", "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
                      "usdt", "bnb", "xrp", "doge", "ada", "dot", "avax", "matic",
                      "price", "trading", "trade", "mexc", "gate", "exchange",
                      "κρυπτο", "μπιτκοιν", "τιμή", "αγορά", "πώληση",
                      "νομίσματα", "ανταλλαγή", "πορτοφόλι"],
        "build_prompt": lambda lang: build_crypto_prompt(lang),
    },
    "molecular": {
        "icon": "⚗️",
        "name": "Molecular Gastronomy",
        "desc": "Spherification, foams, gels, sous-vide techniques",
        "keywords": ["molecular", "spherification", "foam", "gel",
                      "sous vide", "sousv", "emulsion", "nitrogen",
                      "μοριακή", "γαστρονομία", "σφαιροποίηση", "αφρός",
                      "ζελατίνα", "τεχνική", "εμουλσιόν"],
        "build_prompt": lambda lang: build_chef_prompt(lang),
    },
    "omega": {
        "icon": "🔥",
        "name": "Chef Omega Neural",
        "desc": "15 Neural Agents + GAIA Brain + Archetypal Kitchen",
        "keywords": ["omega", "neural kitchen", "gaia", "prometheus chef",
                      "neural recipe", "advanced recipe"],
        "build_prompt": lambda lang: build_chef_prompt(lang),
    },
    "brain": {
        "icon": "🧠",
        "name": "Super Brain Nobel",
        "desc": "Nobel-mode analysis: breakthrough innovation + risk matrix",
        "keywords": ["brain", "nobel", "breakthrough", "innovation",
                      "super brain", "egkefalos", "epanastash",
                      "εγκέφαλος", "νόμπελ", "καινοτομία", "επανάσταση",
                      "ανακάλυψη", "πρωτοποριακό", "μέλλον"],
        "build_prompt": lambda lang: build_apex_prompt(lang),
    },
    "cyber": {
        "icon": "🔒",
        "name": "Cyber Intelligence",
        "desc": "Security analysis, threat assessment, NIST/ISO frameworks",
        "keywords": ["cyber", "security", "hack", "threat", "vulnerability",
                      "firewall", "encryption", "pentest", "asfaleia",
                      "ασφάλεια", "κυβερνοασφάλεια", "απειλή", "ευπάθεια",
                      "κρυπτογράφηση", "επίθεση", "προστασία"],
        "build_prompt": lambda lang: build_cyber_prompt(lang),
    },
    "academic": {
        "icon": "🎓",
        "name": "Academic Research",
        "desc": "Search arXiv, PubMed, OpenAlex + 12 sources",
        "keywords": ["arxiv", "pubmed", "paper", "academic", "journal",
                      "citation", "doi", "arthro", "dhmosieysh",
                      "άρθρο", "δημοσίευση", "ακαδημαϊκό", "επιστημονικό",
                      "πανεπιστήμιο", "διατριβή", "βιβλιογραφία"],
        "build_prompt": lambda lang: build_academic_prompt(lang),
    },
    "terra": {
        "icon": "🌿",
        "name": "Terra Alchemica",
        "desc": "Olympus Council: Bio-Alchemy + Molecular + Monastic + Safety",
        "keywords": ["terra", "alchemy", "alchemica", "herbs", "healing",
                      "phyto", "ayurveda", "monastic", "holistic", "elixir",
                      "tincture", "potion", "botanical", "herbal", "remedy",
                      "alximeia", "votana", "therapeia", "monasthriako",
                      "βότανα", "βότανο", "αλχημεία", "θεραπεία", "μοναστηριακό",
                      "ελιξίριο", "φαρμακευτικό", "φυτοθεραπεία", "αγιορείτικο",
                      "βιοαλχημεία", "ολιστικό", "αρωματικά φυτά", "τσάι βουνού",
                      "δίκταμο", "χαμομήλι", "ρίγανη", "φασκόμηλο"],
        "build_prompt": lambda lang: build_terra_prompt(lang),
    },
}

# ═══════════════════════════════════════════════════════════════
#  ASSEMBLY MODE PRESETS
# ═══════════════════════════════════════════════════════════════

ASSEMBLY_MODES = {
    "strategic": "🏛️ Alexander, Sun Tzu, Machiavelli, Cleopatra",
    "technical": "⚙️ Stark, Tesla, Daedalus, Archimedes",
    "analytical": "🔍 Sherlock, Newton, Socrates, Oracle",
    "tactical": "🎯 Ethan Hunt, MacGyver, Odysseus, Batman",
    "creative": "🎨 DaVinci, Merlin, Prometheus, Morpheus",
    "wisdom": "📿 Socrates, Merlin, Athena, Aristotle, Confucius",
    "financial": "💰 Buffett, Soros, Dalio, Keynes, Thiel",
    "legal": "⚖️ Specter, Ginsburg, Atticus, Athena",
    "startup": "🚀 Jobs, Musk, Thiel, Graham, Draper",
    "marketing": "📣 Draper, Godin, Cialdini, Cleopatra",
    "business": "📊 Alexander, Buffett, Jobs, Thiel, Specter, Drucker",
    "full": "🌐 ALL 26+ Archetypes"
}

# ═══════════════════════════════════════════════════════════════
#  TELEGRAM API HELPERS
# ═══════════════════════════════════════════════════════════════

http_client: Optional[httpx.AsyncClient] = None

async def get_client() -> httpx.AsyncClient:
    global http_client
    if http_client is None or http_client.is_closed:
        http_client = httpx.AsyncClient(timeout=120, follow_redirects=True)
    return http_client

def esc(text: str) -> str:
    return html.escape(str(text)) if text else ""

async def tg(method: str, **kwargs) -> dict:
    client = await get_client()
    try:
        r = await client.post(f"{TELEGRAM_API}/{method}", json=kwargs, timeout=30)
        return r.json()
    except Exception as e:
        log.error(f"TG API error: {e}")
        return {}

async def send_msg(chat_id: int, text: str, **kwargs) -> dict:
    MAX_LEN = 4000
    if len(text) > MAX_LEN:
        parts = []
        while text:
            if len(text) <= MAX_LEN:
                parts.append(text)
                break
            cut = text[:MAX_LEN].rfind('\n')
            if cut < 100:
                cut = MAX_LEN
            parts.append(text[:cut])
            text = text[cut:].lstrip('\n')

        result = {}
        for part in parts:
            result = await tg("sendMessage", chat_id=chat_id, text=part,
                             parse_mode="HTML", **kwargs)
            await asyncio.sleep(0.3)
        return result
    return await tg("sendMessage", chat_id=chat_id, text=text,
                    parse_mode="HTML", **kwargs)

async def send_typing(chat_id: int):
    await tg("sendChatAction", chat_id=chat_id, action="typing")

# ═══════════════════════════════════════════════════════════════
#  LANGUAGE DETECTION — Enhanced with full Greek + Greeklish
# ═══════════════════════════════════════════════════════════════

def detect_language(text: str, user_id: int = 0) -> str:
    """Detect language: checks user preference, Greek chars, Greek words, Greeklish"""
    # Check user preference first
    if user_id and user_id in user_language_prefs:
        return user_language_prefs[user_id]
    
    # Check for Greek Unicode characters
    greek_chars = sum(1 for c in text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
    
    # Check for Greek words (full Unicode)
    greek_words = [
        "μουσακάς", "συνταγή", "συνταγές", "μαγείρεμα", "μαγειρική",
        "φαγητό", "πιάτο", "στρατηγική", "επιχείρηση", "επένδυση",
        "αγορά", "κέρδος", "ανάπτυξη", "ασφάλεια", "έρευνα",
        "ανάλυση", "διαφήμιση", "συμβούλιο", "γνώμη", "βοήθεια",
        "τζόκερ", "λοττο", "κινο", "τυχερά", "εγκέφαλος",
        "σουβλάκι", "γυρο", "κοτόπουλο", "σαλάτα", "σούπα",
        "θέλω", "μπορώ", "πώς", "τι", "ποιο", "γιατί",
        "είναι", "έχω", "κάνω", "δώσε", "φτιάξε", "βρες",
        "μου", "σου", "του", "της", "μας", "σας",
        "και", "για", "από", "στο", "στα", "στη",
        "αυτό", "αυτή", "αυτός", "εδώ", "εκεί",
        "κλήρωση", "νούμερα", "αριθμοί", "τυχεροί",
        "εστιατόριο", "μενού", "κουζίνα", "σεφ"
    ]
    text_lower = text.lower()
    greek_word_match = any(w in text_lower for w in greek_words)
    
    # Check for Greeklish words
    greeklish_words = [
        "kai", "gia", "ena", "mou", "sou", "einai", "tha",
        "pou", "apo", "sto", "thn", "ton", "tous", "ti",
        "mia", "den", "oxi", "nai", "me", "se", "na",
        "pame", "kane", "dose", "ftia3e", "vres", "thelo",
        "boro", "pos", "giati", "poio", "exo", "kano",
        "syntagh", "fagito", "mageirev", "epixeirhsh",
        "stratigikh", "asfaleia", "klhrwsh", "noumera"
    ]
    greeklish = sum(1 for w in text_lower.split() if w in greeklish_words)
    
    if greek_chars > 2 or greek_word_match or greeklish > 1:
        return "el"
    return "en"


def detect_engine(text: str) -> str:
    """Smart engine detection from natural language"""
    text_lower = text.lower()

    # Check each engine's keywords
    scores = {}
    for key, engine in ENGINES.items():
        score = sum(1 for kw in engine["keywords"] if kw in text_lower)
        if score > 0:
            scores[key] = score

    if scores:
        return max(scores, key=scores.get)

    # Default fallback
    return "brain"


def detect_opap_game(text: str) -> Optional[str]:
    """Detect which OPAP game is being asked about"""
    text_lower = text.lower()
    
    game_keywords = {
        "tzoker": ["tzoker", "τζόκερ", "τζοκερ", "joker"],
        "kino": ["kino", "κινο", "κίνο"],
        "lotto": ["lotto", "λοττο", "λότο", "λοτο", "λοττό"],
        "proto": ["proto", "πρωτο", "πρώτο"],
        "extra5": ["extra5", "extra 5", "εξτρα5", "έξτρα"],
        "super3": ["super3", "super 3", "σουπερ3"],
        "eurojackpot": ["eurojackpot", "euro jackpot", "ευρωτζάκποτ"],
        "powerspin": ["powerspin", "power spin"],
    }
    
    for game, keywords in game_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return game
    
    # Generic lottery mention → default to tzoker
    if any(kw in text_lower for kw in ["opap", "λαχείο", "laxeio", "τυχερά", "κλήρωση", "νούμερα", "lucky numbers"]):
        return "tzoker"
    
    return None

# ═══════════════════════════════════════════════════════════════
#  OPAP API — Live Lottery Data
# ═══════════════════════════════════════════════════════════════

async def fetch_opap_data(game_key: str) -> dict:
    """Fetch live OPAP data for a specific game"""
    game = OPAP_GAMES.get(game_key)
    if not game:
        return {"error": f"Unknown game: {game_key}"}
    
    game_id = game["id"]
    client = await get_client()
    result = {"game": game["name"], "game_key": game_key}
    
    try:
        # Get last result
        r = await client.get(
            f"https://api.opap.gr/draws/v3.0/{game_id}/last-result-and-active",
            timeout=10,
            headers={"Accept": "application/json"}
        )
        if r.status_code == 200:
            data = r.json()
            
            # Parse last result
            last = data.get("last", data) if isinstance(data, dict) else {}
            if not last and isinstance(data, dict):
                last = data
            
            draw_id = last.get("drawId", "N/A")
            draw_time = last.get("drawTime", "")
            winning = last.get("winningNumbers", {})
            numbers = winning.get("list", [])
            bonus = winning.get("bonus", [])
            
            result["last_draw"] = {
                "draw_id": draw_id,
                "draw_time": draw_time,
                "numbers": numbers,
                "bonus": bonus
            }
            
            # Parse prize categories
            prize_cats = last.get("prizeCategories", [])
            if prize_cats:
                result["prizes"] = []
                for cat in prize_cats[:6]:
                    result["prizes"].append({
                        "category": cat.get("id", ""),
                        "divident": cat.get("divident", 0),
                        "winners": cat.get("winners", 0),
                        "distributed": cat.get("distributed", 0)
                    })
            
            # Parse active/upcoming draw
            active = data.get("active")
            if active:
                result["next_draw"] = {
                    "draw_id": active.get("drawId", ""),
                    "draw_time": active.get("drawTime", ""),
                    "prize_pool": active.get("prizeCategories", [{}])[0].get("minimum", 0) if active.get("prizeCategories") else 0
                }
        
        # Get statistics
        stats_url = f"https://api.opap.gr/games/v1.0/{game_id}/statistics"
        if game_key == "kino":
            stats_url += "?drawRange=1801"
        
        sr = await client.get(stats_url, timeout=10, headers={"Accept": "application/json"})
        if sr.status_code == 200:
            stats = sr.json()
            result["statistics"] = stats
        
        # Get last 10 draws for frequency analysis
        lr = await client.get(
            f"https://api.opap.gr/draws/v3.0/{game_id}/last/10",
            timeout=10,
            headers={"Accept": "application/json"}
        )
        if lr.status_code == 200:
            last_draws = lr.json()
            if isinstance(last_draws, list):
                all_numbers = []
                for draw in last_draws:
                    wn = draw.get("winningNumbers", {})
                    all_numbers.extend(wn.get("list", []))
                
                # Frequency analysis
                from collections import Counter
                freq = Counter(all_numbers)
                result["frequency_analysis"] = {
                    "hot_numbers": [n for n, _ in freq.most_common(10)],
                    "cold_numbers": [n for n, _ in freq.most_common()[-10:]],
                    "total_draws_analyzed": len(last_draws)
                }
    
    except Exception as e:
        log.error(f"OPAP API error: {e}")
        result["error"] = str(e)
    
    return result


def format_opap_context(opap_data: dict) -> str:
    """Format OPAP data as context for AI prompt"""
    lines = []
    
    game = opap_data.get("game", "Unknown")
    lines.append(f"ΠΑΙΧΝΙΔΙ: {game}")
    
    last = opap_data.get("last_draw", {})
    if last:
        lines.append(f"ΤΕΛΕΥΤΑΙΑ ΚΛΗΡΩΣΗ: #{last.get('draw_id', 'N/A')}")
        lines.append(f"ΗΜΕΡΟΜΗΝΙΑ: {last.get('draw_time', 'N/A')}")
        numbers = last.get("numbers", [])
        if numbers:
            lines.append(f"ΚΕΡΔΙΣΜΕΝΟΙ ΑΡΙΘΜΟΙ: {', '.join(str(n) for n in numbers)}")
        bonus = last.get("bonus", [])
        if bonus:
            lines.append(f"BONUS/ΤΖΟΚΕΡ: {', '.join(str(n) for n in bonus)}")
    
    prizes = opap_data.get("prizes", [])
    if prizes:
        lines.append("\nΒΡΑΒΕΙΑ:")
        for p in prizes[:5]:
            winners = p.get("winners", 0)
            divident = p.get("divident", 0)
            if winners > 0:
                lines.append(f"  Κατηγορία {p.get('category', '?')}: {winners} νικητές × {divident:.2f}€")
    
    freq = opap_data.get("frequency_analysis", {})
    if freq:
        hot = freq.get("hot_numbers", [])
        cold = freq.get("cold_numbers", [])
        lines.append(f"\nΣΤΑΤΙΣΤΙΚΑ (τελευταίες {freq.get('total_draws_analyzed', '?')} κληρώσεις):")
        if hot:
            lines.append(f"HOT αριθμοί (πιο συχνοί): {', '.join(str(n) for n in hot[:8])}")
        if cold:
            lines.append(f"COLD αριθμοί (πιο σπάνιοι): {', '.join(str(n) for n in cold[:8])}")
    
    next_draw = opap_data.get("next_draw", {})
    if next_draw:
        lines.append(f"\nΕΠΟΜΕΝΗ ΚΛΗΡΩΣΗ: {next_draw.get('draw_time', 'N/A')}")
        prize_pool = next_draw.get("prize_pool", 0)
        if prize_pool:
            lines.append(f"ΤΖΑΚΠΟΤ: {prize_pool:,.0f}€")
    
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════
#  BACKEND COMMUNICATION
# ═══════════════════════════════════════════════════════════════

async def call_backend(endpoint: str, payload: dict, method: str = "POST") -> dict:
    """Call AetherLang backend with error handling"""
    client = await get_client()
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == "GET":
            r = await client.get(url, params=payload, timeout=30)
        else:
            r = await client.post(url, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()
    except httpx.TimeoutException:
        raise Exception("Backend timeout — processing may take longer")
    except httpx.HTTPStatusError as e:
        raise Exception(f"Backend error {e.response.status_code}")
    except httpx.ConnectError:
        raise Exception("Backend offline")

async def call_backend_async(endpoint: str, payload: dict) -> dict:
    """Call backend with async polling pattern"""
    client = await get_client()
    
    start_endpoint = endpoint if endpoint.endswith("/start") else f"{endpoint}/start"
    
    try:
        r = await client.post(f"{BACKEND_URL}{start_endpoint}", json=payload, timeout=30)
        if r.status_code == 404:
            r = await client.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=120)
            r.raise_for_status()
            return r.json()
        
        start_data = r.json()
        task_id = start_data.get("task_id")
        if not task_id:
            return start_data
        
        status_base = endpoint.rstrip('/').rsplit('/', 1)[0] if '/start' in start_endpoint else endpoint.rstrip('/')
        status_endpoint = f"{status_base}/status/{task_id}"
        
        elapsed = 0
        while elapsed < POLL_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            sr = await client.get(f"{BACKEND_URL}{status_endpoint}", timeout=15)
            status_data = sr.json()
            if status_data.get("status") == "completed":
                return status_data.get("result", status_data)
            elif status_data.get("status") == "error":
                raise Exception(status_data.get("error", "Task failed"))
        raise Exception("Timeout — task is still processing")
    except httpx.ConnectError:
        raise Exception("Backend offline")


async def call_aetherlang_flow(node: str, query: str, language: str = "en") -> dict:
    """Execute AetherLang DSL flow via orchestrator — with input sanitization"""
    # 🛡️ SECURITY: Sanitize before sending to backend
    query = sanitize_input(query, MAX_QUERY_LENGTH)
    language = "el" if language == "el" else "en"  # Whitelist language values
    lang_param = f', language="{language}"' if language == "el" else ""
    
    FLOW_TEMPLATES = {
        "chef": f'flow Chef {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node Chef: chef cuisine="auto", difficulty="medium", servings=4{lang_param};\n  output text recipe from Chef;\n}}}}',
        "molecular": f'flow Molecular {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node Chef: chef cuisine="molecular", difficulty="molecular", servings=4{lang_param};\n  output text recipe from Chef;\n}}}}',
        "apex": f'flow Strategy {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node Guard: guard mode="MODERATE";\n  node Planner: plan steps=4;\n  node LLM: llm model="gpt-4o", temp=0.7{lang_param};\n  Guard -> Planner -> LLM;\n  output text report from LLM;\n}}}}',
        "assembly": f'flow Assembly {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node Guard: guard mode="MODERATE";\n  node LLM: llm model="gpt-4o", temp=0.9{lang_param};\n  Guard -> LLM;\n  output text report from LLM;\n}}}}',
        "research": f'flow Research {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node Guard: guard mode="MODERATE";\n  node Planner: plan steps=4;\n  node RAG: rag topk=3;\n  node LLM: llm model="gpt-4o", temp=0.4{lang_param};\n  Guard -> Planner -> LLM;\n  RAG -> LLM;\n  output text report from LLM;\n}}}}',
        "market": f'flow Marketing {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node LLM: llm model="gpt-4o", temp=0.8{lang_param};\n  output text campaign from LLM;\n}}}}',
        "consult": f'flow Consulting {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node Guard: guard mode="MODERATE";\n  node Planner: plan steps=4;\n  node LLM: llm model="gpt-4o", temp=0.7{lang_param};\n  Guard -> Planner -> LLM;\n  output text report from LLM;\n}}}}',
        "oracle": f'flow Oracle {{{{\n  using target "neuroaether" version ">=0.2";\n  input text query;\n  node LLM: llm model="gpt-4o", temp=0.8{lang_param};\n  output text prediction from LLM;\n}}}}',
    }
    
    node_map = {"chef": "chef", "molecular": "molecular", "omega": "chef",
                "apex": "apex", "brain": "apex", "assembly": "assembly",
                "lab": "analyze", "academic": "analyze", "consulting": "consulting",
                "marketing": "marketing", "oracle": "oracle", "cyber": "apex", "terra": "apex"}
    
    flow_key = node_map.get(node, "apex")
    template = FLOW_TEMPLATES.get(flow_key, FLOW_TEMPLATES["apex"])
    
    payload = {"code": template, "query": query}
    client = await get_client()
    try:
        r = await client.post(f"{BACKEND_URL}/aetherlang/execute", json=payload, timeout=120)
        data = r.json()
        if data.get("status") == "success":
            outputs = data.get("result", {}).get("outputs", data.get("outputs", {}))
            for key, val in outputs.items():
                if isinstance(val, dict):
                    raw = val.get("response", val.get("output", ""))
                    # Try to parse JSON response for structured formatting
                    if isinstance(raw, str):
                        try:
                            cleaned = raw.strip()
                            if cleaned.startswith("```"):
                                lines = cleaned.split("\n")
                                if lines[0].startswith("```"): lines = lines[1:]
                                if lines and lines[-1].strip() == "```": lines = lines[:-1]
                                cleaned = "\n".join(lines).strip()
                            js = cleaned.find("{")
                            je = cleaned.rfind("}")
                            if js >= 0 and je > js:
                                parsed = json.loads(cleaned[js:je+1])
                                if isinstance(parsed, dict) and len(str(parsed)) > 100:
                                    return parsed  # Return dict for chef/apex formatters
                        except (json.JSONDecodeError, TypeError):
                            pass
                    return {"raw_text": str(raw), "_source": "aetherlang"}
                else:
                    return {"raw_text": str(val), "_source": "aetherlang"}
            return {"raw_text": "", "_source": "aetherlang"}
        else:
            raise Exception(data.get("error", str(data)))
    except httpx.ConnectError:
        raise Exception("Backend offline")

# ═══════════════════════════════════════════════════════════════
#  FDA FOOD SAFETY ENRICHMENT
# ═══════════════════════════════════════════════════════════════

async def get_fda_safety(ingredients: list) -> str:
    if not FDA_API_KEY or not ingredients:
        return ""
    client = await get_client()
    warnings = []
    for ingredient in ingredients[:3]:
        name = ingredient if isinstance(ingredient, str) else ingredient.get("item", "")
        if not name:
            continue
        try:
            r = await client.get(
                "https://api.fda.gov/food/enforcement.json",
                params={"search": f'reason_for_recall:"{name}"', "limit": 2, "api_key": FDA_API_KEY},
                timeout=8
            )
            if r.status_code == 200:
                for result in r.json().get("results", [])[:1]:
                    warnings.append(f"⚠️ <b>{esc(name)}</b>: {esc(result.get('reason_for_recall', '')[:120])}")
        except:
            pass
    return "\n\n🛡️ <b>FDA Safety Alerts:</b>\n" + "\n".join(warnings) if warnings else ""

# ═══════════════════════════════════════════════════════════════
#  OPENAI DIRECT — AI Engine with MEGA Prompts
# ═══════════════════════════════════════════════════════════════

async def call_openrouter(query: str, engine_key: str, language: str, opap_data: str = "") -> str:
    """Call OpenAI directly with enhanced prompts from NeuroAether backend"""
    if not OPENAI_KEY:
        return "❌ No OpenAI API key available."
    
    # 🛡️ SECURITY: Sanitize query before sending to LLM
    query = sanitize_input(query, MAX_QUERY_LENGTH)
    
    client = await get_client()
    engine = ENGINES.get(engine_key, ENGINES["brain"])
    
    # Build the MEGA system prompt
    if engine_key == "oracle" and opap_data:
        sys_prompt = build_oracle_prompt(language, opap_data)
    elif engine_key == "crypto":
        sys_prompt = build_crypto_prompt(language, opap_data)
    elif "build_prompt" in engine:
        sys_prompt = engine["build_prompt"](language)
    else:
        lang_inst = get_language_instruction(language)
        sys_prompt = f"{lang_inst}\n\nYou are NeuroAether Super Brain. Provide comprehensive analysis."
    
    # Adjust model and temperature per engine
    model = "gpt-4o"
    max_tokens = 6000
    temperature = 0.7
    
    if engine_key in ["chef", "omega", "molecular"]:
        max_tokens = 12000
        temperature = 0.7
    elif engine_key in ["assembly"]:
        max_tokens = 8000
        temperature = 0.9
    elif engine_key in ["oracle"]:
        temperature = 0.6
    elif engine_key in ["marketing"]:
        temperature = 0.85
    elif engine_key in ["crypto"]:
        temperature = 0.5
        max_tokens = 8000
    elif engine_key in ["lab", "academic"]:
        temperature = 0.5
    elif engine_key == "terra":
        max_tokens = 10000
        temperature = 0.7
    
    try:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": query}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=120
        )
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            return "❌ AI returned empty response"
        
        # Try to parse as JSON for structured formatting
        try:
            # Strip markdown code blocks if present
            cleaned = content.strip()
            if cleaned.startswith("```"):
                # Remove ```json ... ``` wrapper
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]  # Remove opening ```json
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]  # Remove closing ```
                cleaned = "\n".join(lines).strip()
            
            # Try to find JSON object in text (sometimes LLM adds text before/after)
            json_start = cleaned.find("{")
            json_end = cleaned.rfind("}")
            if json_start >= 0 and json_end > json_start:
                json_str = cleaned[json_start:json_end + 1]
                json_content = json.loads(json_str)
                
                # Validate it has actual content (not just empty keys)
                if isinstance(json_content, dict) and len(str(json_content)) > 100:
                    return json_content  # Return dict for structured formatting
            
            # If JSON parsing got something tiny, fall back to raw text
            return content
        except (json.JSONDecodeError, TypeError, ValueError):
            return content  # Return raw text
            
    except Exception as e:
        log.error(f"OpenRouter error: {e}")
        return f"❌ AI engine error: {e}"

# ═══════════════════════════════════════════════════════════════
#  RESPONSE FORMATTERS — Beautiful Telegram Output
# ═══════════════════════════════════════════════════════════════

def format_chef_response(data: dict, engine_icon: str = "👨‍🍳") -> str:
    """Format chef recipe for Telegram"""
    try:
        return _format_chef_inner(data, engine_icon)
    except Exception as e:
        # Fallback: show raw JSON if formatter crashes
        import traceback
        traceback.print_exc()
        raw = json.dumps(data, ensure_ascii=False, indent=2)[:3500]
        return f"{engine_icon} <b>CHEF OMEGA — Recipe Complete</b>\n\n{html.escape(raw)}"

def _format_chef_inner(data: dict, engine_icon: str = "👨‍🍳") -> str:
    """Inner formatter with full error protection"""
    lines = [f"{engine_icon} <b>CHEF OMEGA — Recipe Complete</b>\n"]
    
    # Handle nested recipe structure
    if isinstance(data, dict) and "recipe" in data:
        data = data["recipe"]
    
    recipes = data.get("recipes", [data]) if "recipes" in data else [data]
    for recipe in recipes[:2]:
        name = recipe.get("recipe_name") or recipe.get("dish_name") or recipe.get("title", "Recipe")
        name_en = recipe.get("recipe_name_en", "")
        lines.append(f"🍽️ <b>{esc(name)}</b>")
        if name_en and name_en != name:
            lines.append(f"  <i>({esc(name_en)})</i>")
        
        # Overview
        overview = recipe.get("overview", {})
        if overview:
            lines.append(f"📋 {esc(str(overview.get('category', '')))} | ⏱️ {overview.get('total_time_minutes', '?')}min | 🍽️ {overview.get('portions', overview.get('servings', 4))} μερίδες × {overview.get('portion_weight_grams', '?')}g")
        
        # Financials
        fin = recipe.get("financials", {})
        if fin:
            fc = fin.get("food_cost_per_portion", fin.get("cost_per_serving", "N/A"))
            sp = fin.get("recommended_menu_price", fin.get("suggested_price", "N/A"))
            fcp = fin.get("food_cost_percentage", "N/A")
            cat = fin.get("menu_category", "")
            gp = fin.get("gross_profit_per_portion", "")
            lines.append(f"💰 Κόστος: {esc(str(fc))} | Τιμή: {esc(str(sp))} | FC%: {esc(str(fcp))} | {esc(cat)}")
            if gp:
                lines.append(f"  📈 Κέρδος/μερίδα: {esc(str(gp))}")

        # Ingredients
        ingredients = recipe.get("ingredients", [])
        if ingredients:
            lines.append(f"\n📋 <b>Υλικά ({len(ingredients)}):</b>")
            for ing in ingredients[:15]:
                if isinstance(ing, dict):
                    item = ing.get("item", ing.get("name", ""))
                    qty = ing.get("quantity_grams", ing.get("quantity", ing.get("quantity_display", "")))
                    cost = ing.get("cost_for_recipe", ing.get("cost", ""))
                    prep = ing.get("preparation", ing.get("prep", ""))
                    cost_str = f" — {cost}€" if cost else ""
                    prep_str = f" ({prep})" if prep else ""
                    lines.append(f"  • {esc(str(qty))}{'g' if isinstance(qty, (int, float)) else ''} {esc(item)}{esc(str(cost_str))}{esc(prep_str)}")

        # Mise en place
        mise = recipe.get("mise_en_place", {})
        if mise:
            lines.append(f"\n🔪 <b>Mise en Place:</b>")
            if isinstance(mise, dict):
                for phase, items in mise.items():
                    if isinstance(items, list):
                        lines.append(f"  <b>{esc(phase)}:</b> {esc(', '.join(str(i) for i in items[:4]))}")
            elif isinstance(mise, list):
                for i, step in enumerate(mise[:8], 1):
                    lines.append(f"  {i}. {esc(str(step))}")

        # Execution steps — FULL DETAIL
        steps = recipe.get("execution_steps", recipe.get("steps", []))
        if steps:
            lines.append(f"\n👨‍🍳 <b>Εκτέλεση ({len(steps)} βήματα):</b>\n")
            for step in steps[:16]:
                if isinstance(step, dict):
                    num = step.get("step_number", step.get("step", ""))
                    action = step.get("action", step.get("instruction", ""))
                    detail = step.get("detailed_instructions", "")
                    temp = step.get("temperature_celsius", "")
                    time_m = step.get("time_minutes", "")
                    tip = step.get("pro_tips", step.get("chef_tip", ""))
                    technique = step.get("chef_technique", "")
                    visual = step.get("visual_cue", "")
                    mistakes = step.get("common_mistakes", "")
                    equipment = step.get("equipment", "")
                    
                    # Step header with action
                    header = f"<b>{num}. {esc(str(action))}</b>"
                    if temp:
                        header += f" 🌡️{temp}°C"
                    if time_m:
                        header += f" ⏱️{time_m}λ."
                    lines.append(header)
                    
                    # Equipment
                    if equipment:
                        lines.append(f"  🍳 {esc(str(equipment)[:100])}")
                    
                    # Detailed instructions — FULL (up to 500 chars)
                    if detail:
                        lines.append(f"  {esc(str(detail)[:500])}")
                    elif action and len(str(action)) > 20:
                        lines.append(f"  {esc(str(action)[:500])}")
                    
                    # Technique
                    if technique:
                        lines.append(f"  🔪 <i>Τεχνική: {esc(str(technique)[:120])}</i>")
                    
                    # Visual cue
                    if visual:
                        lines.append(f"  👁️ {esc(str(visual)[:150])}")
                    
                    # Common mistakes
                    if mistakes:
                        if isinstance(mistakes, list):
                            mistakes = mistakes[0] if mistakes else ""
                        lines.append(f"  ⚠️ {esc(str(mistakes)[:150])}")
                    
                    # Pro tip
                    if tip:
                        if isinstance(tip, list):
                            tip = tip[0] if tip else ""
                        lines.append(f"  💡 {esc(str(tip)[:150])}")
                    
                    lines.append("")  # empty line between steps
                elif isinstance(step, str):
                    lines.append(f"  • {esc(str(step)[:300])}")

        # HACCP
        haccp = recipe.get("haccp", {})
        if haccp:
            lines.append(f"\n🛡️ <b>HACCP Safety:</b>")
            temps = haccp.get("critical_temps", haccp.get("critical_control_points", []))
            if isinstance(temps, str):
                lines.append(f"  🌡️ {esc(temps)}")
            elif isinstance(temps, list):
                for t in temps[:3]:
                    lines.append(f"  🌡️ {esc(str(t))}")
            allergens = haccp.get("allergens", [])
            if allergens:
                if isinstance(allergens, str):
                    lines.append(f"  ⚠️ Αλλεργιογόνα: {esc(allergens)}")
                elif isinstance(allergens, list):
                    lines.append(f"  ⚠️ Αλλεργιογόνα: {esc(', '.join(str(a) for a in allergens))}")

        # MacYuFBI
        mac = recipe.get("macyufbi", recipe.get("mac_yu_fbi", {}))
        if mac and isinstance(mac, dict):
            flavors = mac.get("dominant_flavors", mac.get("balance", []))
            if flavors:
                lines.append(f"\n🎯 <b>MacYuFBI:</b> {esc(', '.join(str(f) for f in (flavors if isinstance(flavors, list) else [flavors])[:5]))}")
            strategy = mac.get("counter_strategy", mac.get("solution", mac.get("strategy", "")))
            if strategy:
                lines.append(f"  ↳ {esc(str(strategy)[:200])}")

        # Zero waste
        waste = recipe.get("zero_waste", [])
        if waste:
            lines.append(f"\n♻️ <b>Zero Waste:</b>")
            if isinstance(waste, dict):
                lines.append(f"  • {esc(str(waste.get('byproduct', '')))} → {esc(str(waste.get('use', '')))}")
            elif isinstance(waste, list):
                for w in waste[:3]:
                    if isinstance(w, dict):
                        lines.append(f"  • {esc(w.get('byproduct', ''))} → {esc(w.get('use', ''))}")
                    else:
                        lines.append(f"  • {esc(str(w))}")

    return "\n".join(lines)


def format_apex_response(data: dict) -> str:
    """Format APEX/Brain strategic analysis"""
    lines = ["📈 <b>APEX — Nobel Strategic Analysis</b>\n"]
    
    es = data.get("executive_summary", data.get("summary", ""))
    if es:
        if isinstance(es, list):
            es = "\n".join(str(e) for e in es[:6])
        lines.append(f"📋 <b>Executive Summary:</b>\n{esc(str(es)[:1000])}\n")
    
    challenge = data.get("grand_challenge", "")
    if challenge:
        lines.append(f"🎯 <b>Grand Challenge:</b>\n{esc(str(challenge)[:400])}\n")
    
    approaches = data.get("approaches", data.get("strategic_options", []))
    for approach in (approaches if isinstance(approaches, list) else [])[:3]:
        if isinstance(approach, dict):
            name = approach.get("name", approach.get("option", ""))
            desc = approach.get("description", approach.get("detail", ""))
            lines.append(f"🎯 <b>{esc(str(name))}</b>")
            lines.append(f"  {esc(str(desc)[:400])}")
    
    roadmap = data.get("phased_roadmap", data.get("implementation_roadmap", data.get("action_plan", [])))
    if roadmap and isinstance(roadmap, list):
        lines.append(f"\n🗺️ <b>Roadmap:</b>")
        for phase in roadmap[:4]:
            if isinstance(phase, dict):
                pname = phase.get("phase", phase.get("action", ""))
                tf = phase.get("timeframe", phase.get("time", ""))
                budget = phase.get("budget", "")
                lines.append(f"  📌 <b>{esc(str(pname))}</b> ({esc(str(tf))})")
                if budget:
                    lines.append(f"     💶 {esc(str(budget))}")
    
    risks = data.get("risk_matrix", data.get("risks_and_mitigation", []))
    if risks and isinstance(risks, list):
        lines.append(f"\n⚠️ <b>Risk Matrix:</b>")
        for r_item in risks[:4]:
            if isinstance(r_item, dict):
                risk = r_item.get("risk", r_item.get("category", ""))
                prob = r_item.get("probability", "")
                mit = r_item.get("mitigation", r_item.get("contingency", ""))
                lines.append(f"  • {esc(str(risk)[:120])}")
                if mit:
                    lines.append(f"    → {esc(str(mit)[:120])}")
    
    kpis = data.get("kpis", [])
    if kpis and isinstance(kpis, list):
        lines.append(f"\n📊 <b>KPIs:</b>")
        for kpi in kpis[:5]:
            if isinstance(kpi, dict):
                metric = kpi.get("metric", kpi.get("name", ""))
                target = kpi.get("target_12m", kpi.get("target", ""))
                lines.append(f"  📈 {esc(str(metric))}: {esc(str(target))}")
    
    nobel = data.get("nobel_vision", data.get("breakthrough_innovation", ""))
    if nobel:
        desc = nobel.get("description", str(nobel)) if isinstance(nobel, dict) else str(nobel)
        lines.append(f"\n🏆 <b>Nobel Vision:</b>\n{esc(str(desc)[:400])}")
    
    meta = data.get("meta_review", {})
    if meta and isinstance(meta, dict):
        insight = meta.get("ultimate_insight", "")
        if insight:
            lines.append(f"\n💎 <b>Key Insight:</b> {esc(str(insight)[:300])}")
    
    return "\n".join(lines)


def format_assembly_response(data: dict) -> str:
    """Format Grand Assembly response"""
    lines = ["🏛️ <b>GRAND ASSEMBLY — Council Convened</b>\n"]
    
    archetypes = data.get("archetypes", [])
    for arch in archetypes[:8]:
        if isinstance(arch, dict):
            name = arch.get("name", "")
            icon = arch.get("icon", "🎭")
            insight = arch.get("key_insight", arch.get("recommendation", ""))
            analysis = arch.get("analysis", "")
            lines.append(f"{icon} <b>{esc(name)}</b>")
            if analysis:
                lines.append(f"  {esc(str(analysis)[:300])}")
            if insight:
                lines.append(f"  💡 <i>{esc(str(insight)[:200])}</i>")
            lines.append("")
    
    synth = data.get("synthesis", {})
    if synth:
        verdict = synth.get("consensus_verdict", "")
        confidence = synth.get("confidence_score", "")
        summary = synth.get("executive_summary", "")
        lines.append(f"⚖️ <b>VERDICT: {esc(str(verdict))}</b> | Confidence: {esc(str(confidence))}%")
        if summary:
            lines.append(f"\n📋 <b>Synthesis:</b>\n{esc(str(summary)[:500])}")
        
        strat = synth.get("unified_strategy", {})
        if strat:
            lines.append(f"\n🎯 <b>Strategy:</b> {esc(str(strat.get('primary_approach', '')))}")
            steps = strat.get("tactical_steps", [])
            for i, s in enumerate(steps[:5], 1):
                lines.append(f"  {i}. {esc(str(s))}")
    
    gandalf = data.get("gandalf_review", {})
    if gandalf:
        status = gandalf.get("status", "")
        wisdom = gandalf.get("wisdom", "")
        quote = gandalf.get("wisdom_quote", "")
        lines.append(f"\n🧙 <b>Gandalf Review: {esc(status)}</b>")
        if wisdom:
            lines.append(f"  {esc(str(wisdom)[:300])}")
        if quote:
            lines.append(f"  📜 <i>\"{esc(str(quote)[:200])}\"</i>")
    
    return "\n".join(lines)


def format_oracle_response(data: dict) -> str:
    """Format OPAP Oracle response — with 3 sets of lucky numbers"""
    lines = ["🎰 <b>OPAP ORACLE — Live Data Analysis</b>\n"]
    
    game = data.get("game", "")
    if game:
        lines.append(f"🎮 <b>{esc(game)}</b>\n")
    
    # Latest draw
    latest = data.get("latest_draw", {})
    if latest:
        lines.append(f"🏆 <b>Τελευταία Κλήρωση:</b> #{esc(str(latest.get('draw_id', '')))}")
        date = latest.get("date", "")
        if date:
            lines.append(f"📅 {esc(str(date))}")
        numbers = latest.get("winning_numbers", [])
        if numbers:
            if isinstance(numbers, list):
                lines.append(f"🔢 Αριθμοί: <b>{' — '.join(str(n) for n in numbers)}</b>")
            else:
                lines.append(f"🔢 Αριθμοί: <b>{esc(str(numbers))}</b>")
        bonus = latest.get("bonus", "")
        if bonus:
            lines.append(f"🃏 Bonus/Τζόκερ: <b>{esc(str(bonus))}</b>")
        prizes = latest.get("prizes", "")
        if prizes:
            lines.append(f"💰 {esc(str(prizes)[:200])}")
    
    # Statistical analysis
    stats = data.get("statistical_analysis", {})
    if stats:
        lines.append(f"\n📊 <b>Στατιστική Ανάλυση:</b>")
        hot = stats.get("hot_numbers", "")
        cold = stats.get("cold_numbers", "")
        overdue = stats.get("overdue_numbers", "")
        if hot:
            hot_str = ", ".join(str(n) for n in hot) if isinstance(hot, list) else str(hot)
            lines.append(f"  🔥 Ζεστοί: <b>{esc(hot_str)}</b>")
        if cold:
            cold_str = ", ".join(str(n) for n in cold) if isinstance(cold, list) else str(cold)
            lines.append(f"  ❄️ Κρύοι: <b>{esc(cold_str)}</b>")
        if overdue:
            ov_str = ", ".join(str(n) for n in overdue) if isinstance(overdue, list) else str(overdue)
            lines.append(f"  ⏳ Καθυστερημένοι: <b>{esc(ov_str)}</b>")
        patterns = stats.get("patterns", "")
        if patterns:
            lines.append(f"  📈 {esc(str(patterns)[:250])}")
    
    # Lucky numbers — 3 SETS
    lucky = data.get("lucky_numbers", {})
    if lucky:
        lines.append(f"\n🍀🍀🍀 <b>ΤΥΧΕΡΟΙ ΑΡΙΘΜΟΙ:</b> 🍀🍀🍀\n")
        
        for set_key in ["set_1", "set_2", "set_3"]:
            s = lucky.get(set_key, {})
            if s and isinstance(s, dict):
                nums = s.get("numbers", [])
                bonus = s.get("bonus", "")
                method = s.get("method", "")
                if nums:
                    nums_str = " — ".join(str(n) for n in nums) if isinstance(nums, list) else str(nums)
                    set_label = {"set_1": "1️⃣", "set_2": "2️⃣", "set_3": "3️⃣"}.get(set_key, "🔢")
                    lines.append(f"  {set_label} <b>[ {esc(nums_str)} ]</b>")
                    if bonus:
                        lines.append(f"     🃏 Bonus: <b>{esc(str(bonus))}</b>")
                    if method:
                        lines.append(f"     📐 <i>{esc(str(method)[:100])}</i>")
                    lines.append("")
        
        # Fallback: old format (main_numbers)
        main = lucky.get("main_numbers", lucky.get("numbers", []))
        if main and not lucky.get("set_1"):
            nums_str = ", ".join(str(n) for n in main) if isinstance(main, list) else str(main)
            lines.append(f"  🔢 <b>[ {esc(nums_str)} ]</b>")
            bonus = lucky.get("bonus_number", lucky.get("bonus", ""))
            if bonus:
                lines.append(f"  🃏 Bonus: <b>{esc(str(bonus))}</b>")
    
    # Analysis summary
    summary = data.get("analysis_summary", "")
    if summary:
        lines.append(f"\n📝 <b>Ανάλυση:</b>\n{esc(str(summary)[:400])}")
    
    # Next draw
    next_draw = data.get("next_draw", {})
    if next_draw:
        nd_date = next_draw.get("date", "")
        jackpot = next_draw.get("estimated_jackpot", "")
        if nd_date:
            lines.append(f"\n📅 Επόμενη Κλήρωση: {esc(str(nd_date))}")
        if jackpot:
            lines.append(f"💰 Εκτιμώμενο Τζακπότ: <b>{esc(str(jackpot))}</b>")
    
    # Disclaimer
    disclaimer = data.get("responsible_gambling", "")
    if disclaimer:
        lines.append(f"\n{esc(str(disclaimer))}")
    else:
        lines.append("\n⚠️ Κάθε κλήρωση είναι ΤΥΧΑΙΑ. Παίξτε υπεύθυνα. ΚΕΘΕΑ: 1114")
    
    return "\n".join(lines)


def format_crypto_analysis(data: dict) -> str:
    """Format APEX crypto analysis for Telegram"""
    lines = ["🧠 <b>APEX Crypto Intelligence — Analysis</b>\n"]
    
    # Market overview
    overview = data.get("market_overview", {})
    if overview:
        regime = str(overview.get("regime", "N/A")).upper()
        sentiment = str(overview.get("sentiment", "N/A")).upper()
        narrative = overview.get("key_narrative", "")
        regime_emoji = {"BULL": "🟢", "BEAR": "🔴", "CHOP": "🟡", "TRANSITION": "🔄"}.get(regime, "⚪")
        lines.append(f"{regime_emoji} <b>Regime:</b> {esc(regime)} | <b>Sentiment:</b> {esc(sentiment)}")
        if narrative:
            lines.append(f"📝 {esc(str(narrative)[:300])}")
        lines.append("")
    
    # Coin analysis
    coins = data.get("coin_analysis", [])
    for coin in coins[:8]:
        if isinstance(coin, dict):
            symbol = str(coin.get("symbol", "?")).upper()
            verdict = str(coin.get("verdict", "N/A")).upper()
            conviction = str(coin.get("conviction", "N/A")).upper()
            insight = coin.get("key_insight", "")
            risk = coin.get("risk_warning", "")
            support = coin.get("support", [])
            resistance = coin.get("resistance", [])
            
            v_emoji = {"LONG": "🟢", "SHORT": "🔴", "NEUTRAL": "⚪", "WAIT": "🟡"}.get(verdict, "⚪")
            lines.append(f"{v_emoji} <b>{esc(symbol)}</b> — {esc(verdict)} ({esc(conviction)})")
            
            # Handle support/resistance - could be list of numbers, strings, or a single string
            def format_levels(levels):
                if isinstance(levels, str):
                    return levels
                if isinstance(levels, list):
                    parts = []
                    for lv in levels:
                        if isinstance(lv, (int, float)):
                            if lv >= 1000:
                                parts.append(f"${lv:,.0f}")
                            elif lv >= 1:
                                parts.append(f"${lv:,.2f}")
                            else:
                                parts.append(f"${lv:,.4f}")
                        else:
                            s = str(lv).strip()
                            if s and not s.startswith("$"):
                                s = f"${s}"
                            parts.append(s)
                    return " / ".join(parts) if parts else ""
                return str(levels)
            
            sup_str = format_levels(support)
            res_str = format_levels(resistance)
            if sup_str:
                lines.append(f"  📉 Support: {esc(sup_str)}")
            if res_str:
                lines.append(f"  📈 Resistance: {esc(res_str)}")
            if insight:
                lines.append(f"  💡 {esc(str(insight)[:250])}")
            if risk:
                lines.append(f"  ⚠️ {esc(str(risk)[:200])}")
            lines.append("")
    
    # Hyper council
    council = data.get("hyper_council", {})
    if council:
        lines.append("<b>🏛 Hyper-Council:</b>")
        labels = {"macro_view": "🌍 Macro", "quant_signal": "📊 Quant", "risk_assessment": "⚠️ Risk (Damocles)", "regime_status": "📈 Regime"}
        for key, label in labels.items():
            val = council.get(key, "")
            if val:
                lines.append(f"  {label}: {esc(str(val)[:250])}")
        lines.append("")
    
    # Action plan
    plan = data.get("action_plan", {})
    if plan:
        lines.append("<b>🎯 Action Plan:</b>")
        if plan.get("primary_trade"):
            lines.append(f"  🎯 {esc(str(plan['primary_trade'])[:200])}")
        if plan.get("entry_logic"):
            lines.append(f"  📍 Entry: {esc(str(plan['entry_logic'])[:200])}")
        if plan.get("risk_management"):
            lines.append(f"  🛡️ Risk: {esc(str(plan['risk_management'])[:200])}")
        if plan.get("time_horizon"):
            lines.append(f"  ⏱️ Horizon: {esc(str(plan['time_horizon']))}")
        lines.append("")
    
    # Disclaimer - handle both string and dict
    disclaimer = data.get("disclaimer", "")
    if isinstance(disclaimer, dict):
        disc_text = disclaimer.get("responsible_trading_warning", "") or disclaimer.get("text", "") or str(list(disclaimer.values())[0]) if disclaimer else ""
    else:
        disc_text = str(disclaimer)
    if disc_text:
        lines.append(f"\n⚠️ {esc(disc_text[:250])}")
    
    return "\n".join(lines)


def format_generic_response(data: dict, engine_key: str) -> str:
    """Format generic JSON response"""
    engine = ENGINES.get(engine_key, {"icon": "🧠", "name": "Brain"})
    lines = [f"{engine['icon']} <b>{esc(engine['name'])} — Complete</b>\n"]
    
    es = data.get("executive_summary", data.get("summary", data.get("threat_assessment", "")))
    if es:
        lines.append(f"📋 <b>Summary:</b>\n{esc(str(es)[:800])}\n")
    
    for key in ["approaches", "three_approaches", "defense_strategy", "key_papers", "content_calendar"]:
        items = data.get(key, [])
        if items:
            if isinstance(items, list):
                for item in items[:5]:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("title", ""))
                        desc = item.get("description", item.get("key_finding", item.get("content_type", "")))
                        lines.append(f"  🔹 <b>{esc(str(name))}</b>: {esc(str(desc)[:200])}")
            elif isinstance(items, dict):
                for k, v in items.items():
                    if isinstance(v, list):
                        lines.append(f"  📌 <b>{esc(k)}:</b> {esc(', '.join(str(i)[:50] for i in v[:3]))}")
    
    steps = data.get("actionable_steps", data.get("recommendations", data.get("engagement_strategy", [])))
    if steps and isinstance(steps, list):
        lines.append(f"\n✅ <b>Actions:</b>")
        for i, s in enumerate(steps[:6], 1):
            lines.append(f"  {i}. {esc(str(s)[:150])}")
    
    risks = data.get("risk_matrix", data.get("risk_assessment", []))
    if risks and isinstance(risks, list):
        lines.append(f"\n⚠️ <b>Risks:</b>")
        for r_item in risks[:4]:
            if isinstance(r_item, dict):
                lines.append(f"  • {esc(str(r_item.get('risk', ''))[:100])}: {esc(str(r_item.get('mitigation', '')[:100]))}")
    
    return "\n".join(lines)


def format_terra_response(data: dict) -> str:
    """Format Terra Alchemica Grand Opus for Telegram"""
    lines = []
    opus_name = data.get("opus_name", "Terra Alchemica Opus")
    lines.append(f"🌿 <b>TERRA ALCHEMICA — {esc(opus_name)}</b>\n")

    summary = data.get("executive_summary", "")
    if summary:
        lines.append(f"📜 <b>Summary:</b>\n{esc(summary[:600])}\n")

    exoteric = data.get("deep_dive_exoteric", "")
    if exoteric:
        lines.append(f"🔬 <b>Scientific Perspective:</b>\n{esc(exoteric[:800])}\n")

    esoteric = data.get("deep_dive_esoteric", "")
    if esoteric:
        lines.append(f"🏛️ <b>Ancient Wisdom:</b>\n{esc(esoteric[:800])}\n")

    formula = data.get("the_formula", {})
    if formula:
        ingredients = formula.get("ingredients", [])
        if ingredients:
            lines.append("⚗️ <b>The Formula — Ingredients:</b>")
            for ing in ingredients[:10]:
                if isinstance(ing, dict):
                    name = ing.get("name", "")
                    amount = ing.get("amount", "")
                    props = ing.get("properties", "")
                    lines.append(f"  🌱 <b>{esc(name)}</b> — {esc(amount)}")
                    if props:
                        lines.append(f"      <i>{esc(props[:120])}</i>")

        steps = formula.get("preparation_steps", [])
        if steps:
            lines.append("\n📋 <b>Preparation:</b>")
            for i, step in enumerate(steps[:8], 1):
                lines.append(f"  {i}. {esc(str(step)[:200])}")

        mechanisms = formula.get("molecular_mechanisms", "")
        if mechanisms:
            lines.append(f"\n🧬 <b>Molecular Mechanisms:</b>\n{esc(mechanisms[:500])}")

    safety = data.get("safety_audit", {})
    if safety:
        status = safety.get("status", "UNKNOWN")
        status_emoji = {"SAFE": "✅", "CAUTION": "⚠️", "RESTRICTED": "🚫", "EXPERIMENTAL": "🔬"}.get(status, "❓")
        lines.append(f"\n🛡️ <b>Safety Audit:</b> {status_emoji} {esc(status)}")
        for alert in safety.get("ccp_alerts", [])[:5]:
            lines.append(f"  ⚠️ {esc(str(alert)[:150])}")
        for note in safety.get("regulatory_notes", [])[:3]:
            lines.append(f"  📋 {esc(str(note)[:150])}")

    horizon = data.get("future_horizon", "")
    if horizon:
        lines.append(f"\n🔮 <b>Future Horizon:</b>\n{esc(horizon[:400])}")

    kpis = data.get("kpis", [])
    if kpis:
        lines.append("\n📊 <b>Key Metrics:</b>")
        for kpi in kpis[:6]:
            if isinstance(kpi, dict):
                lines.append(f"  • <b>{esc(str(kpi.get('metric', ''))[:60])}:</b> {esc(str(kpi.get('value', ''))[:100])}")

    return "\n".join(lines)


def format_response(data, engine_key: str) -> str:
    """Smart response formatter — routes to correct formatter"""
    
    # Handle raw text
    if isinstance(data, str):
        if data.startswith("❌"):
            return data
        engine = ENGINES.get(engine_key, {"icon": "🧠", "name": "Brain"})
        
        # First HTML-escape for safety
        text = html.escape(data[:3800])
        # Then convert markdown to HTML (works because ** isn't affected by html.escape)
        text = re.sub(r'#{1,4}\s*(.+)', r'<b>\1</b>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Remove markdown table separators
        text = re.sub(r'\|[-:\s]+\|[-:\s|]+\|', '', text)
        # Clean table pipes
        text = re.sub(r'\|\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\|\s*', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'\s*\|\s*', ' — ', text)
        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return f"{engine['icon']} <b>{engine['name']} — Complete</b>\n\n{text.strip()}"
    
    if not isinstance(data, dict):
        return f"📊 Result:\n{esc(str(data)[:3500])}"
    
    # Check for raw_text from AetherLang
    if "raw_text" in data and data.get("_source") == "aetherlang":
        engine = ENGINES.get(engine_key, {"icon": "🧠", "name": "Brain"})
        return f"{engine['icon']} <b>{esc(engine['name'])} — Complete</b>\n\n{esc(str(data['raw_text'])[:3500])}"
    
    # Route to appropriate formatter
    if engine_key in ["chef", "omega", "molecular"]:
        formatted = format_chef_response(data)
        # If formatter returned almost nothing, show raw dict as text
        if len(formatted) < 200:
            engine = ENGINES.get(engine_key, {"icon": "👨‍🍳", "name": "Chef Omega"})
            # Convert dict to readable text
            raw = json.dumps(data, ensure_ascii=False, indent=2)[:3500]
            return f"{engine['icon']} <b>{esc(engine['name'])} — Complete</b>\n\n{esc(raw)}"
        return formatted
    elif engine_key in ["apex", "brain"]:
        return format_apex_response(data)
    elif engine_key == "assembly":
        return format_assembly_response(data)
    elif engine_key == "oracle":
        return format_oracle_response(data)
    elif engine_key == "crypto":
        return format_crypto_analysis(data)
    elif engine_key == "terra":
        return format_terra_response(data)
    else:
        return format_generic_response(data, engine_key)

# ═══════════════════════════════════════════════════════════════
#  MAIN PROCESSING ENGINE — 3-Layer: AetherLang → OpenRouter → Fallback
# ═══════════════════════════════════════════════════════════════

async def process_query(query: str, engine_key: str, user_id: int, chat_id: int) -> str:
    """Process user query through multi-layer AI pipeline"""

    # 💰 Credit check before processing
    cost = ENGINE_COSTS.get(engine_key, 2)
    current_credits = get_credits(user_id)
    if current_credits < cost:
        buy_keyboard = {"inline_keyboard": [
            [{"text": "🛒 Buy Credits", "callback_data": "buy:pro"}],
        ]}
        await tg("sendMessage", chat_id=chat_id,
            text=f"💰 Not enough credits!\n\nNeeded: {cost} | Balance: {current_credits}\n\n🛒 Buy more credits:",
            reply_markup=buy_keyboard, parse_mode="HTML")
        return "Credits insufficient"

    # Deduct credits
    spend_credits(user_id, cost, engine_key)
    remaining_credits = get_credits(user_id)

    language = detect_language(query, user_id)
    start_time = time.time()
    model_used = "gpt-4o"

    # OPAP: Fetch live data first for oracle engine
    opap_context = ""
    if engine_key == "oracle":
        game_key = detect_opap_game(query)
        if game_key:
            await send_typing(chat_id)
            opap_data = await fetch_opap_data(game_key)
            opap_context = format_opap_context(opap_data)
            log.info(f"OPAP data fetched for {game_key}: {len(opap_context)} chars")
    
    # For Greek: Layer 2 FIRST (OpenRouter has MEGA Greek prompts)
    # For English: Layer 1 first (AetherLang backend)
    # ALL languages → AetherLang backend first (has MEGA prompts)
    # Then fallback to OpenAI direct
    # ENGLISH → AetherLang backend first
    # ORACLE -> OpenRouter FIRST (has quantum prompt with number generation)
    if engine_key == "oracle":
        try:
            await send_typing(chat_id)
            enriched_query = f"{query}\n\nLIVE OPAP DATA:\n{opap_context}" if opap_context else query
            result = await call_openrouter(enriched_query, engine_key, language, opap_context)
            elapsed = time.time() - start_time
            formatted = format_response(result, engine_key)
            formatted += f"\n\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\u23f1\ufe0f {elapsed:.1f}s | \U0001f916 {model_used} | \U0001f310 {'EL' if language == 'el' else 'EN'}"
            return formatted
        except Exception as e_oracle:
            last_error = str(e_oracle)
            log.warning(f"Oracle OpenRouter failed: {e_oracle}")

    # BLUEPRINT -> Generate PDF report
    if engine_key == "blueprint":
        try:
            await send_typing(chat_id)
            
            # Detect coins
            coin_ids = detect_crypto_coins(query)
            if not coin_ids:
                coin_ids = ["bitcoin"]
            
            # Fetch all data
            import asyncio as aio
            cg_task = fetch_coingecko_data(coin_ids)
            ex_task = fetch_exchange_data(coin_ids)
            crypto_data, exchange_data = await aio.gather(cg_task, ex_task)
            
            # Send status
            status_msg = "📄 Generating APEX Trading Blueprint...\n⏳ This takes 30-60 seconds"
            if language == "el":
                status_msg = "📄 Δημιουργία APEX Trading Blueprint...\n⏳ Αναμονή 30-60 δευτερόλεπτα"
            await send_msg(chat_id, status_msg)
            await send_typing(chat_id)
            
            # Build context
            crypto_context = format_crypto_context(crypto_data)
            ex_context = format_exchange_context(exchange_data)
            full_context = crypto_context + ex_context
            
            # Call LLM for blueprint JSON
            enriched_query = f"Generate a complete APEX Trading Blueprint for the following market data:\n\n{full_context}\n\nUser query: {query}"
            
            client = await get_client()
            headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": BLUEPRINT_SYSTEM_PROMPT},
                    {"role": "user", "content": enriched_query}
                ],
                "max_tokens": 8000,
                "temperature": 0.5
            }
            
            r = await client.post("https://api.openai.com/v1/chat/completions", 
                                  json=payload, headers=headers, timeout=120)
            
            if r.status_code != 200:
                raise Exception(f"OpenAI error: {r.status_code}")
            
            resp_data = r.json()
            raw_text = resp_data["choices"][0]["message"]["content"]
            
            # Clean and parse JSON
            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            
            report_json = json.loads(clean)
            
            # Generate PDF
            from apex_blueprint import generate_blueprint_pdf
            import os
            
            symbol_clean = coin_ids[0].replace("-", "_")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            pdf_path = f"/tmp/APEX_Blueprint_{symbol_clean}_{timestamp}.pdf"
            
            generate_blueprint_pdf(report_json, pdf_path)
            
            # Post-process with Ghostscript for maximum compatibility
            compat_path = pdf_path.replace(".pdf", "_compat.pdf")
            try:
                import subprocess
                subprocess.run([
                    "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                    "-dPDFSETTINGS=/default", "-dNOPAUSE", "-dQUIET", "-dBATCH",
                    f"-sOutputFile={compat_path}", pdf_path
                ], timeout=30, check=True)
                os.remove(pdf_path)
                pdf_path = compat_path
            except Exception as gs_err:
                log.warning(f"Ghostscript post-process failed: {gs_err}")
            
            # Send PDF via Telegram
            pdf_size = os.path.getsize(pdf_path)
            with open(pdf_path, 'rb') as pdf_file:
                files = {"document": (f"APEX_Blueprint_{symbol_clean}.pdf", pdf_file, "application/pdf")}
                send_data = {"chat_id": chat_id, "caption": f"📄 APEX Trading Blueprint — {report_json.get('strategy_snapshot', {}).get('symbol', symbol_clean.upper())}\n🏛 Hyper-Council Analysis\n⏱️ {time.time() - start_time:.1f}s"}
                sr = await client.post(f"{TELEGRAM_API}/sendDocument", data=send_data, files=files, timeout=30)
                
                # Get download link for PC users
                sr_json = sr.json()
                if sr_json.get("ok"):
                    file_id = sr_json["result"].get("document", {}).get("file_id", "")
                    if file_id:
                        # Get file path from Telegram
                        file_resp = await client.get(f"{TELEGRAM_API}/getFile?file_id={file_id}", timeout=10)
                        file_data = file_resp.json()
                        if file_data.get("ok"):
                            file_path = file_data["result"].get("file_path", "")
                            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                            await send_msg(chat_id, f"💻 <b>PC Download:</b>\n<a href=\"{download_url}\">📥 Click here to download PDF</a>\n\n💡 An den anoigei sto Telegram Desktop, anoikse to link ston browser.")
            
            # Cleanup
            os.remove(pdf_path)
            
            # Send text summary for those who can't open PDF
            snapshot = report_json.get("strategy_snapshot", {})
            council_mod = next((m for m in report_json.get("modules", []) if m.get("type") == "hyper_council"), {})
            consensus = council_mod.get("consensus", {})
            
            summary_lines = [
                "📄 <b>APEX Trading Blueprint — Summary</b>\n",
                f"📌 <b>Symbol:</b> {esc(str(snapshot.get('symbol', 'N/A')))}",
                f"📊 <b>Status:</b> {esc(str(snapshot.get('status', 'N/A')))}",
                f"🎯 <b>Conviction:</b> {esc(str(snapshot.get('conviction_level', 'N/A')))}",
                f"⚖️ <b>Risk:</b> {esc(str(snapshot.get('risk_profile', 'N/A')))}\n",
                f"🏛 <b>Consensus:</b> {esc(str(consensus.get('status', 'N/A')))} (Score: {consensus.get('consensus_score', 'N/A')})",
                f"📝 {esc(str(consensus.get('execution_log', ''))[:300])}\n",
            ]
            
            # Add agent summaries
            agents = council_mod.get("agents", [])
            for ag in agents[:5]:
                if isinstance(ag, dict):
                    role = ag.get("role", "")
                    sentiment = ag.get("sentiment", "")
                    s_emoji = {"LONG": "🟢", "STRONG_LONG": "🟢", "SHORT": "🔴", "STRONG_SHORT": "🔴", "VETO": "🚫", "NEUTRAL": "🟡", "INFO": "ℹ️"}.get(sentiment, "⚪")
                    summary_lines.append(f"{s_emoji} <b>{esc(role)}:</b> {esc(str(ag.get('summary', ''))[:150])}")
            
            summary_lines.append(f"\n💡 Full report in the PDF above ↑")
            
            elapsed = time.time() - start_time
            summary_lines.append(f"\n⏱️ {elapsed:.1f}s | 🤖 gpt-4o")
            
            return "\n".join(summary_lines)
            
        except json.JSONDecodeError as je:
            log.error(f"Blueprint JSON parse error: {je}")
            return f"❌ Blueprint generation failed — JSON parse error. Try again."
        except Exception as e_bp:
            log.error(f"Blueprint error: {e_bp}")
            import traceback
            traceback.print_exc()
            return f"❌ Blueprint error: {esc(str(e_bp)[:300])}"

    # CRYPTO -> Show price table + APEX analysis via OpenRouter
    if engine_key == "crypto":
        try:
            await send_typing(chat_id)
            coin_ids = detect_crypto_coins(query)
            
            # Fetch CoinGecko + Exchange data in parallel
            import asyncio as aio
            cg_task = fetch_coingecko_data(coin_ids)
            ex_task = fetch_exchange_data(coin_ids)
            crypto_data, exchange_data = await aio.gather(cg_task, ex_task)
            
            # Send price table + exchange comparison immediately
            table = format_crypto_table(crypto_data, language)
            ex_table = format_exchange_table(exchange_data, language)
            if ex_table:
                table += ex_table
            await send_msg(chat_id, table)
            
            # Now get APEX analysis with ALL data
            await send_typing(chat_id)
            crypto_context = format_crypto_context(crypto_data)
            ex_context = format_exchange_context(exchange_data)
            full_context = crypto_context + ex_context
            enriched_crypto_query = f"{query}\n\n{full_context}"
            result = await call_openrouter(enriched_crypto_query, "crypto", language, full_context)
            elapsed = time.time() - start_time
            formatted = format_response(result, "crypto")
            formatted += f"\n\n──────────────────────────────\n⏱️ {elapsed:.1f}s | 🤖 {model_used} | 🌐 {'EL' if language == 'el' else 'EN'}"
            return formatted
        except Exception as e_crypto:
            last_error = str(e_crypto)
            log.warning(f"Crypto engine failed: {e_crypto}")
            # Still try to return the table if we have it
            try:
                if crypto_data and crypto_data.get("coins"):
                    return format_crypto_table(crypto_data, language) + f"\n\n⚠️ Analysis unavailable: {last_error}"
            except:
                pass

    # TERRA ALCHEMICA -> Multi-expert council
    if engine_key == "terra":
        try:
            status_msg = "🌿 Summoning the Terra Alchemica Council...\n⏳ 3-stage expert analysis in progress"
            if language == "el":
                status_msg = "🌿 Σύγκληση του Συμβουλίου Terra Alchemica...\n⏳ 3-σταδιακή ανάλυση ειδικών σε εξέλιξη"
            await send_msg(chat_id, status_msg)
            opus = await run_terra_council(query, language, chat_id)
            if opus and isinstance(opus, dict) and opus.get("opus_name"):
                elapsed = time.time() - start_time
                formatted = format_terra_response(opus)
                formatted += f"\n\n──────────────────────────────\n⏱️ {elapsed:.1f}s | 🤖 gpt-4o ×5 | 🌐 {'EL' if language == 'el' else 'EN'}"
                return formatted
            else:
                log.warning("Terra council returned empty, falling through to standard processing")
        except Exception as e_terra:
            log.warning(f"Terra council failed: {e_terra}, falling through")

    # ALL OTHER engines -> AetherLang backend first
    try:
        await send_typing(chat_id)
        node_map = {"chef": "chef", "molecular": "molecular", "omega": "chef",
                    "apex": "apex", "brain": "apex", "assembly": "assembly",
                    "lab": "analyze", "academic": "analyze", "consulting": "consulting",
                    "marketing": "marketing", "oracle": "oracle", "cyber": "apex", "terra": "apex"}
        node = node_map.get(engine_key, "apex")
        
        # Add OPAP context to query for oracle
        enriched_query = f"{query}\n\n{opap_context}" if opap_context else query
        
        result = await call_aetherlang_flow(node, enriched_query, language)
        elapsed = time.time() - start_time
        
        formatted = format_response(result, engine_key)
        formatted += f"\n\n──────────────────────────────\n⏱️ {elapsed:.1f}s | 🤖 {model_used} | 🌐 {'EL' if language == 'el' else 'EN'}"
        return formatted
        
    except Exception as e1:
        last_error = str(e1)
        log.warning(f"AetherLang failed: {e1}")
    
    # Layer 2: Direct OpenRouter with MEGA prompts
    try:
        await send_typing(chat_id)
        
        # For oracle: inject OPAP data into prompt
        if engine_key == "oracle" and opap_context:
            enriched_query = f"{query}\n\nLIVE OPAP DATA:\n{opap_context}"
        else:
            enriched_query = query
        
        result = await call_openrouter(enriched_query, engine_key, language, opap_context)
        elapsed = time.time() - start_time
        
        formatted = format_response(result, engine_key)
        formatted += f"\n\n──────────────────────────────\n⏱️ {elapsed:.1f}s | 🤖 {model_used} | 🌐 {'EL' if language == 'el' else 'EN'}"
        
        # FDA safety for chef recipes
        if engine_key in ["chef", "omega", "molecular"] and isinstance(result, dict):
            ingredients = result.get("ingredients", result.get("recipe", {}).get("ingredients", []))
            fda = await get_fda_safety(ingredients)
            if fda:
                formatted += fda
        
        return formatted
        
    except Exception as e2:
        log.error(f"OpenRouter failed: {e2}")
        lang_label = "Ελληνικά" if language == "el" else "English"
        return f"❌ All engines failed.\nAetherLang: {last_error}\nOpenRouter: {e2}\nLanguage: {lang_label}"

# ═══════════════════════════════════════════════════════════════
#  VISION CHEF HELPER FUNCTION
# ═══════════════════════════════════════════════════════════════

async def _vision_chef_process(chat_id: int, user_id: int, file_ids: list, caption: str):
    """Process 1-10 photos through Vision Chef v4"""
    # 💰 Credit check for Vision Chef
    cost = 8 if len(file_ids) >= 3 else 5
    if get_credits(user_id) < cost:
        buy_keyboard = {"inline_keyboard": [
            [{"text": "🛒 Buy Credits", "callback_data": "buy:pro"}],
        ]}
        await tg("sendMessage", chat_id=chat_id,
            text=f"💰 Not enough credits for Vision Chef!\n\nNeeded: {cost} | Balance: {get_credits(user_id)}\n\n🛒 /buy to get more",
            reply_markup=buy_keyboard, parse_mode="HTML")
        return
    spend_credits(user_id, cost, "vision" if len(file_ids) < 3 else "vision_multi")

    try:
        lang = detect_language(caption, user_id)
        diff = "medium"
        svgs = 4
        if caption:
            cl = caption.lower()
            if "easy" in cl or "aplo" in cl: diff = "easy"
            elif "hard" in cl or "dyskolo" in cl: diff = "hard"
            elif "master" in cl: diff = "masterchef"
            import re as _re
            sm = _re.search(r"(\d+)\s*(at|ser|mer)", cl)
            if sm: svgs = min(50, int(sm.group(1)))

        n = len(file_ids)
        await send_msg(chat_id, f"<b>Vision Chef v4</b> -- Analyzing {n} photo{'s' if n > 1 else ''}...\nDifficulty: {diff} | Servings: {svgs}\n6-Member Culinary Council activated\nEstimated: ~{30 + n * 15}-{60 + n * 20} seconds")
        await send_typing(chat_id)

        client = await get_client()
        all_photo_bytes = []
        for fid in file_ids[:10]:
            fr = await client.get(f"{TELEGRAM_API}/getFile?file_id={fid}", timeout=10)
            file_path = fr.json().get("result", {}).get("file_path", "")
            photo_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            pr = await client.get(photo_url, timeout=30)
            all_photo_bytes.append(pr.content)

        from vision_chef import run_vision_pipeline_multi, generate_recipe_pdf, format_vision_telegram, format_ingredient_report
        result = await run_vision_pipeline_multi(all_photo_bytes, lang=lang, difficulty=diff, servings=svgs)

        s1_list = result.get("ingredients_list", [result.get("ingredients", {})])
        ing_report = format_ingredient_report(s1_list, lang)
        await send_msg(chat_id, ing_report)
        await send_typing(chat_id)

        recipe = result["recipe"]
        metrics = result["metrics"]
        summary = format_vision_telegram(recipe, metrics, pdf_sent=True)
        await send_msg(chat_id, summary)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rname = recipe.get("recipe_name", "Recipe").replace(" ", "_").replace("/", "-")[:50]
        pdf_path = f"/tmp/VisionChef_{rname}_{ts}.pdf"
        generate_recipe_pdf(recipe, metrics, pdf_path)
        pdf_size = os.path.getsize(pdf_path)
        pdf_filename = f"VisionChef_{rname}.pdf"
        with open(pdf_path, "rb") as pf:
            files = {"document": (pdf_filename, pf, "application/pdf")}
            sd = {"chat_id": chat_id, "caption": "Recipe PDF - " + str(int(pdf_size/1024)) + " KB | Council v4"}
            client = await get_client()
            sr = await client.post(f"{TELEGRAM_API}/sendDocument", data=sd, files=files, timeout=30)
        try:
            sr_data = sr.json()
            doc = sr_data.get("result", {}).get("document", {})
            if doc.get("file_id"):
                fr2 = await client.get(f"{TELEGRAM_API}/getFile?file_id={doc['file_id']}", timeout=10)
                dl_path = fr2.json().get("result", {}).get("file_path", "")
                if dl_path:
                    dl_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{dl_path}"
                    await send_msg(chat_id, f'<a href="{dl_url}">Click to download PDF on PC</a>')
        except Exception:
            pass
        os.remove(pdf_path)
        # Credit footer for Vision Chef
        remaining = get_credits(user_id)
        await send_msg(chat_id, f"💰 Credits: {remaining} remaining (cost: {cost})")
    except Exception as e:
        log.error(f"Vision Chef error: {e}")
        await send_msg(chat_id, f"Vision Chef error: {esc(str(e)[:300])}")
    return

# ═══════════════════════════════════════════════════════════════
#  💰 TELEGRAM STARS PAYMENT HANDLERS
# ═══════════════════════════════════════════════════════════════

async def handle_pre_checkout(update: dict):
    """Answer pre-checkout query — MUST respond within 10 seconds"""
    pcq = update.get("pre_checkout_query", {})
    if not pcq:
        return
    try:
        await tg("answerPreCheckoutQuery",
            pre_checkout_query_id=pcq["id"],
            ok=True)
        log.info(f"Pre-checkout approved for user {pcq.get('from', {}).get('id')}")
    except Exception as e:
        log.error(f"Pre-checkout error: {e}")

async def handle_successful_payment(update: dict):
    """Process successful Telegram Stars payment"""
    msg = update.get("message", {})
    payment = msg.get("successful_payment", {})
    if not payment:
        return

    chat_id = msg.get("chat", {}).get("id")
    user_id = msg.get("from", {}).get("id", 0)
    payload = payment.get("invoice_payload", "")
    stars = payment.get("total_amount", 0)

    # Parse payload: credits_starter_12345
    parts = payload.split("_")
    package = parts[1] if len(parts) >= 2 else ""

    credit_map = {"starter": 15, "pro": 50, "ultimate": 150}
    credits_to_add = credit_map.get(package, 0)

    if credits_to_add > 0:
        add_credits(user_id, credits_to_add, stars)
        new_balance = get_credits(user_id)
        log.info(f"💰 Payment: user {user_id} bought {credits_to_add} credits for {stars} Stars")
        await send_msg(chat_id,
            f"✅ <b>Payment Successful!</b>\n\n"
            f"⭐ Paid: {stars} Stars\n"
            f"💰 Added: +{credits_to_add} credits\n"
            f"📊 New balance: {new_balance} credits\n\n"
            f"Enjoy your AI engines! 🚀")
    else:
        log.warning(f"Unknown payment payload: {payload}")

# ═══════════════════════════════════════════════════════════════
#  TELEGRAM MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════════

async def handle_message(update: dict):
    """Process incoming Telegram message"""
    msg = update.get("message", {})
    text = msg.get("text", "").strip()
    chat_id = msg.get("chat", {}).get("id")
    user = msg.get("from", {})
    user_id = user.get("id", 0)
    first_name = user.get("first_name", "User")
    
    # ── PHOTO HANDLER (Vision Chef v4) — Multi-Photo Support ──
    photo_list = msg.get("photo", [])
    caption = msg.get("caption", "").strip()
    media_group_id = msg.get("media_group_id", "")
    if photo_list and chat_id:
        if ALLOWED_USERS and user_id not in ALLOWED_USERS:
            await send_msg(chat_id, "Access restricted.")
            return
        best_photo = photo_list[-1]
        file_id = best_photo["file_id"]
        
        if media_group_id:
            if media_group_id not in _photo_buffer:
                _photo_buffer[media_group_id] = {
                    "chat_id": chat_id, "user_id": user_id,
                    "photos": [], "caption": caption, "task": None,
                    "notified": False
                }
            _photo_buffer[media_group_id]["photos"].append(file_id)

            # Send notification on first photo
            if not _photo_buffer[media_group_id]["notified"]:
                await send_msg(chat_id, "📸 Album detected - buffering photos...")
                _photo_buffer[media_group_id]["notified"] = True
            if caption and not _photo_buffer[media_group_id]["caption"]:
                _photo_buffer[media_group_id]["caption"] = caption
            
            if _photo_buffer[media_group_id]["task"]:
                _photo_buffer[media_group_id]["task"].cancel()
            
            async def _process_group(mgid=media_group_id):
                await asyncio.sleep(3)
                buf = _photo_buffer.pop(mgid, None)
                if not buf:
                    return
                # Notify user of final count
                photo_count = len(buf["photos"])
                await send_msg(buf["chat_id"], f"✅ Collected {photo_count} photo{'s' if photo_count > 1 else ''} - processing...")
                await _vision_chef_process(buf["chat_id"], buf["user_id"], buf["photos"], buf["caption"])

            _photo_buffer[media_group_id]["task"] = asyncio.create_task(_process_group())
            return
        else:
            await _vision_chef_process(chat_id, user_id, [file_id], caption)
            return

    if not text or not chat_id:
        return
    
    # Access control
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await send_msg(chat_id, "🔒 Access restricted. Contact admin.")
        return
    
    # 🛡️ SECURITY: Validate and sanitize input (skip for commands)
    if not text.startswith("/"):
        is_safe, reason = validate_query_safety(text)
        if not is_safe:
            log.warning(f"⚠️ BLOCKED [{user_id}]: {reason} — {text[:50]}")
            await send_msg(chat_id, f"⚠️ Input rejected: {reason}. Please rephrase your question.")
            return
        text = sanitize_input(text)
    
    log.info(f"[{user_id}] {first_name}: {text[:80]}")
    
    # ── COMMANDS ──
    
    if text.startswith("/start") or text.startswith("/help"):
        lang = detect_language("", user_id) if user_id in user_language_prefs else "en"
        welcome = f"""🌟 <b>Welcome to AetherLang Ω v2.0, {esc(first_name)}!</b>

The world's most advanced AI orchestration platform — now in your pocket.

🧠 <b>15 AI Engines Available:</b>

👨‍🍳 /chef — Michelin recipes + MacYuFBI + HACCP + financials
📈 /apex — Nobel-level business strategy (9-section)
🏛️ /assembly — 26+ legendary archetypes + Gandalf Veto
💼 /consulting — McKinsey reports: SWOT + Roadmap + KPIs
🔬 /lab — Deep scientific analysis + Nobel insights
📣 /marketing — Viral campaign generator
🎰 /oracle — <b>LIVE OPAP data</b> + statistics + lucky numbers
📊 /crypto — <b>LIVE crypto prices</b> + APEX trading analysis + 4 exchanges
📄 /blueprint — Hedge fund-grade PDF reports + trading strategies
⚗️ /molecular — Molecular gastronomy techniques
🔥 /omega — Neural Kitchen (15 AI agents)
🧠 /brain — Super Brain Nobel mode
🔒 /cyber — Security intelligence
🎓 /academic — Search arXiv, PubMed + 12 sources
🌿 /terra — Bio-Alchemy + Molecular + Monastic Olympus Council

🌐 <b>Language:</b> /lang_el (Ελληνικά) | /lang_en (English)

💡 <b>Just type naturally!</b>
"Μουσακάς για 6 άτομα" → Chef Omega 🇬🇷
"Berlin restaurant strategy" → APEX Logic 🇬🇧
"Bitcoin price" → APEX Crypto Intelligence 📊
"Should I invest in Solana?" → Assembly convenes 🏛️

⚡ <b>Commands:</b>
/engines — List all engines
/assembly_modes — Assembly configurations
/status — System health check
/lang_el — Ελληνικά | /lang_en — English

💰 <b>Credits:</b> /credits — Check balance | /buy — Get more
🆕 New users get 3 FREE credits!

Built with ❤️ by Hlia — From Kitchen to Code
🔄 OpenRouter • 🛡️ FDA Safety • 🎰 LIVE OPAP • 📊 Live Markets"""
        
        await send_msg(chat_id, welcome)
        return
    
    if text == "/engines":
        lines = ["🧠 <b>AetherLang Ω — 15 AI Engines</b>\n"]
        for key, eng in ENGINES.items():
            lines.append(f"{eng['icon']} <b>/{key}</b> — {esc(eng['desc'])}")
        await send_msg(chat_id, "\n".join(lines))
        return
    
    if text == "/assembly_modes":
        lines = ["🏛️ <b>Grand Assembly — Configurations</b>\n"]
        for mode, desc in ASSEMBLY_MODES.items():
            lines.append(f"<b>{esc(mode)}</b>: {esc(desc)}")
        lines.append("\nUsage: /assembly [mode] [question]")
        lines.append("Example: /assembly financial Should I invest in crypto?")
        await send_msg(chat_id, "\n".join(lines))
        return
    
    if text == "/status":
        client = await get_client()
        try:
            r = await client.get(f"{BACKEND_URL}/health", timeout=5)
            backend = "✅ Online" if r.status_code == 200 else f"⚠️ {r.status_code}"
        except:
            backend = "❌ Offline"
        
        lang = user_language_prefs.get(user_id, "auto-detect")
        
        status = f"""⚡ <b>AetherLang Ω v2.0 — System Status</b>

🖥️ Backend: {backend}
🤖 OpenAI: {'✅' if OPENAI_KEY else '❌'}
🔑 OpenAI: {'✅' if OPENAI_KEY else '❌'}
🍽️ FDA API: {'✅' if FDA_API_KEY else '❌'}
🔍 Serper: {'✅' if SERPER_KEY else '❌'}
🎰 OPAP API: ✅ Live
🌐 Language: {esc(lang)}
🧠 Engines: {len(ENGINES)} active
👤 User: {user_id}
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        await send_msg(chat_id, status)
        return

    # ── CREDIT & PAYMENT COMMANDS ──

    if text in ["/credits", "/balance"]:
        credits = get_credits(user_id)
        msg = f"""💰 <b>Your Credits: {credits}</b>

📊 Credit costs:
• Recipe/Standard engines: 2 credits
• Crypto (5 exchanges): 3 credits
• Analysis/Strategy engines: 4 credits
• Blueprint PDF: 6 credits
• Vision Chef (photo): 5-8 credits

🛒 Buy more: /buy"""
        await send_msg(chat_id, msg)
        return

    if text in ["/buy", "/shop", "/store"]:
        keyboard = {"inline_keyboard": [
            [{"text": "⭐ 150 Stars → 15 Credits", "callback_data": "buy:starter"}],
            [{"text": "⭐ 400 Stars → 50 Credits (Best Value)", "callback_data": "buy:pro"}],
            [{"text": "⭐ 900 Stars → 150 Credits (Ultimate)", "callback_data": "buy:ultimate"}],
        ]}
        credits = get_credits(user_id)
        await tg("sendMessage", chat_id=chat_id,
            text=f"🛒 <b>Buy Credits</b>\n\nCurrent balance: {credits} credits\n\nChoose a package:",
            reply_markup=keyboard, parse_mode="HTML")
        return

    if text.startswith("/admin_credits") and user_id in ALLOWED_USERS:
        parts = text.split()
        if len(parts) == 3:
            try:
                target = int(parts[1])
                amount = int(parts[2])
                add_credits(target, amount, 0)
                await send_msg(chat_id, f"✅ Added {amount} credits to user {target}")
            except ValueError:
                await send_msg(chat_id, "⚠️ Usage: /admin_credits USER_ID AMOUNT")
        else:
            await send_msg(chat_id, "⚠️ Usage: /admin_credits USER_ID AMOUNT")
        return

    if text.startswith("/refund") and user_id in ALLOWED_USERS:
        parts = text.split()
        if len(parts) == 3:
            try:
                target = int(parts[1])
                amount = int(parts[2])
                current = get_credits(target)
                conn = sqlite3.connect(CREDITS_DB)
                c = conn.cursor()
                c.execute("UPDATE user_credits SET credits = credits + ?, total_spent = total_spent - ? WHERE user_id = ?",
                          (amount, amount, target))
                c.execute("INSERT INTO transactions (user_id, type, amount, engine, description) VALUES (?, 'refund', ?, '', ?)",
                          (target, amount, f"Admin refund of {amount} credits"))
                conn.commit()
                conn.close()
                new_balance = get_credits(target)
                await send_msg(chat_id, f"✅ Refunded {amount} credits to user {target}\n📊 Balance: {current} → {new_balance}")
            except ValueError:
                await send_msg(chat_id, "⚠️ Usage: /refund USER_ID AMOUNT")
        else:
            await send_msg(chat_id, "⚠️ Usage: /refund USER_ID AMOUNT")
        return

    if text == "/admin_stats" and user_id in ALLOWED_USERS:
        conn = sqlite3.connect(CREDITS_DB)
        c = conn.cursor()
        c.execute("SELECT COUNT(*), SUM(credits), SUM(total_purchased) FROM user_credits")
        users, total_credits, total_purchased = c.fetchone()
        c.execute("SELECT SUM(stars_paid) FROM transactions WHERE type='purchase'")
        total_stars = c.fetchone()[0] or 0
        c.execute("SELECT engine, COUNT(*), SUM(amount) FROM transactions WHERE type='spend' GROUP BY engine ORDER BY COUNT(*) DESC")
        engine_stats = c.fetchall()
        conn.close()

        lines = [f"📊 <b>Admin Stats</b>\n",
                 f"👤 Users: {users}",
                 f"⭐ Total Stars earned: {total_stars}",
                 f"💰 Total credits purchased: {total_purchased or 0}",
                 f"📊 Credits in circulation: {total_credits or 0}\n",
                 f"<b>Engine Usage:</b>"]
        for eng, count, spent in engine_stats[:10]:
            lines.append(f"  {eng}: {count} uses ({spent} credits)")
        await send_msg(chat_id, "\n".join(lines))
        return

    # Language selection
    if text in ["/lang_el", "/el", "/greek", "/ελληνικά"]:
        user_language_prefs[user_id] = "el"
        await send_msg(chat_id, "🇬🇷 Γλώσσα: <b>Ελληνικά</b>\nΌλες οι απαντήσεις θα είναι στα Ελληνικά.")
        return
    
    if text in ["/lang_en", "/en", "/english"]:
        user_language_prefs[user_id] = "en"
        await send_msg(chat_id, "🇬🇧 Language: <b>English</b>\nAll responses will be in English.")
        return
    
    if text in ["/lang_auto", "/auto"]:
        if user_id in user_language_prefs:
            del user_language_prefs[user_id]
        await send_msg(chat_id, "🌐 Language: <b>Auto-detect</b>\nLanguage will be detected from your messages.")
        return
    
    # ── ENGINE COMMANDS ──
    
    engine_key = None
    query = text
    
    # Check /command format
    for key in ENGINES:
        if text.startswith(f"/{key}"):
            engine_key = key
            query = text[len(f"/{key}"):].strip()
            if not query:
                engine = ENGINES[key]
                lang = detect_language("", user_id)
                if lang == "el":
                    await send_msg(chat_id, f"{engine['icon']} <b>{esc(engine['name'])}</b>\n{esc(engine['desc'])}\n\n💡 Γράψε το ερώτημά σου μετά την εντολή.\nΠ.χ. /{key} [ερώτηση]")
                else:
                    await send_msg(chat_id, f"{engine['icon']} <b>{esc(engine['name'])}</b>\n{esc(engine['desc'])}\n\n💡 Type your query after the command.\ne.g. /{key} [your question]")
                return
            break
    
    # Assembly mode handling
    if text.startswith("/assembly "):
        parts = text[10:].strip().split(None, 1)
        if len(parts) >= 2 and parts[0].lower() in ASSEMBLY_MODES:
            engine_key = "assembly"
            query = parts[1]
        elif parts:
            engine_key = "assembly"
            query = " ".join(parts)
    
    # Natural language routing
    if not engine_key:
        engine_key = detect_engine(text)
        query = text
    
    # Process the query
    await send_typing(chat_id)
    engine = ENGINES.get(engine_key, ENGINES["brain"])
    
    lang = detect_language(query, user_id)
    if lang == "el":
        await send_msg(chat_id, f"{engine['icon']} <b>{esc(engine['name'])}</b> — Επεξεργασία... 🇬🇷")
    else:
        await send_msg(chat_id, f"{engine['icon']} <b>{esc(engine['name'])}</b> — Processing... 🇬🇧")
    
    try:
        response = await process_query(query, engine_key, user_id, chat_id)
        # Append credit info footer (unless it was an insufficient credits message)
        if response != "Credits insufficient":
            cost = ENGINE_COSTS.get(engine_key, 2)
            remaining = get_credits(user_id)
            response += f"\n\n💰 Credits: {remaining} remaining (cost: {cost})"
        await send_msg(chat_id, response)
        # Save for PDF generation
        if engine_key != "blueprint" and response != "Credits insufficient":
            user_last_response[user_id] = {"text": response, "engine": engine_key, "query": query}
            pdf_btn = {"inline_keyboard": [[{"text": "📄 PDF Report", "callback_data": f"pdf:{engine_key}"}]]}
            await tg("sendMessage", chat_id=chat_id, text="📄 Θέλεις PDF αναφορά;", reply_markup=pdf_btn, parse_mode="HTML")
    except Exception as e:
        log.error(f"Error processing: {e}")
        await send_msg(chat_id, f"❌ Error: {esc(str(e)[:300])}")

# Handle callback queries (inline buttons)
async def handle_callback(update: dict):
    cb = update.get("callback_query", {})
    data = cb.get("data", "")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    user_id = cb.get("from", {}).get("id", 0)
    
    if not data or not chat_id:
        return
    
    await tg("answerCallbackQuery", callback_query_id=cb.get("id", ""))
    
    # PDF Report generation
    if data.startswith("pdf:"):
        eng_key = data.split(":", 1)[1]
        last = user_last_response.get(user_id)
        if not last:
            await send_msg(chat_id, "⚠️ No recent response to convert to PDF.")
            return
        try:
            await send_msg(chat_id, "📄 Generating PDF report...")
            await send_typing(chat_id)
            from universal_report import generate_engine_pdf
            engine_info = ENGINES.get(eng_key, ENGINES["brain"])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = f"{engine_info['icon']} {engine_info['name']} Report"
            pdf_path = f"/tmp/AetherLang_{eng_key}_{timestamp}.pdf"
            generate_engine_pdf(
                engine_key=eng_key,
                title=title,
                content=last["text"],
                output_path=pdf_path,
                user_query=last.get("query", ""),
            )
            # Ghostscript compat
            compat_path = pdf_path.replace(".pdf", "_compat.pdf")
            try:
                import subprocess
                subprocess.run(["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                    "-dPDFSETTINGS=/default", f"-sOutputFile={compat_path}", pdf_path],
                    capture_output=True, timeout=30)
                import os
                os.remove(pdf_path)
                pdf_path = compat_path
            except:
                pass
            import os
            pdf_size = os.path.getsize(pdf_path)
            with open(pdf_path, "rb") as pdf_file:
                files = {"document": (f"AetherLang_{eng_key}_Report.pdf", pdf_file, "application/pdf")}
                send_data = {"chat_id": chat_id, "caption": engine_info["icon"] + " " + engine_info["name"] + " Report - " + str(int(pdf_size/1024)) + " KB"}
                client = await get_client()
                sr = await client.post(f"{TELEGRAM_API}/sendDocument", data=send_data, files=files, timeout=30)
            os.remove(pdf_path)
        except Exception as e:
            log.error(f"PDF generation error: {e}")
            await send_msg(chat_id, f"❌ PDF error: {esc(str(e)[:200])}")
        return

    # 💰 Buy credits — send Telegram Stars invoice
    if data.startswith("buy:"):
        package = data.split(":")[1]
        pkg = CREDIT_PACKAGES.get(package)
        if not pkg:
            return
        try:
            await tg("sendInvoice",
                chat_id=chat_id,
                title=pkg["title"],
                description=pkg["desc"],
                payload=f"credits_{package}_{user_id}",
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",
                prices=[{"label": pkg["title"], "amount": pkg["stars"]}],
            )
        except Exception as e:
            log.error(f"sendInvoice error: {e}")
            await send_msg(chat_id, f"❌ Payment error: {esc(str(e)[:200])}")
        return

    if data.startswith("engine:"):
        engine_key = data.split(":", 1)[1]
        engine = ENGINES.get(engine_key, ENGINES["brain"])
        lang = detect_language("", user_id)
        if lang == "el":
            await send_msg(chat_id, f"{engine['icon']} <b>{esc(engine['name'])}</b>\n{esc(engine['desc'])}\n\n💡 Γράψε το ερώτημά σου:")
        else:
            await send_msg(chat_id, f"{engine['icon']} <b>{esc(engine['name'])}</b>\n{esc(engine['desc'])}\n\n💡 Type your query:")

# ═══════════════════════════════════════════════════════════════
#  TELEGRAM POLLING LOOP
# ═══════════════════════════════════════════════════════════════

async def main():
    """Main bot loop with long polling"""
    log.info("=" * 60)
    log.info("AetherLang Ω v2.0 MEGA — Starting...")
    log.info(f"Backend: {BACKEND_URL}")
    log.info(f"Engines: {len(ENGINES)}")
    log.info(f"OPAP Games: {len(OPAP_GAMES)}")
    log.info(f"Allowed users: {ALLOWED_USERS}")
    log.info("=" * 60)

    # Initialize credits database
    init_credits_db()
    log.info("💰 Credits database initialized")
    
    # Delete webhook
    await tg("deleteWebhook", drop_pending_updates=True)
    await asyncio.sleep(2)
    
    offset = 0
    consecutive_errors = 0
    
    while True:
        try:
            client = await get_client()
            r = await client.get(
                f"{TELEGRAM_API}/getUpdates",
                params={"offset": offset, "timeout": 30, "allowed_updates": ["message", "callback_query", "pre_checkout_query"]},
                timeout=40
            )
            data = r.json()
            
            if not data.get("ok"):
                error_code = data.get("error_code", 0)
                if error_code == 409:
                    log.error("409 Conflict! Another bot instance is running.")
                    await asyncio.sleep(10)
                    await tg("deleteWebhook", drop_pending_updates=True)
                    continue
                log.error(f"Telegram error: {data}")
                await asyncio.sleep(5)
                continue
            
            consecutive_errors = 0
            
            for update in data.get("result", []):
                offset = update["update_id"] + 1

                try:
                    if "pre_checkout_query" in update:
                        await handle_pre_checkout(update)
                    elif "callback_query" in update:
                        await handle_callback(update)
                    elif "message" in update:
                        msg = update["message"]
                        if "successful_payment" in msg:
                            await handle_successful_payment(update)
                        else:
                            await handle_message(update)
                except Exception as e:
                    log.error(f"Handler error: {e}")
                    import traceback
                    traceback.print_exc()
        
        except httpx.ReadTimeout:
            pass  # Normal long-polling timeout
        except Exception as e:
            consecutive_errors += 1
            wait = min(30, 2 ** consecutive_errors)
            log.error(f"Poll error ({consecutive_errors}): {e} — waiting {wait}s")
            await asyncio.sleep(wait)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
