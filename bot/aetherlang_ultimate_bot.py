#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║        AETHERLANG Ω — ULTIMATE TELEGRAM BOT v2.0 MEGA          ║
║   The Technological Showcase of NeuroAether Intelligence         ║
║                                                                  ║
║  🧠 12 AI Engines  •  40+ Archetypes  •  16 API Integrations   ║
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
SERPER_KEY = os.getenv("SERPER_API_KEY", "")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()]

POLL_INTERVAL = 4
POLL_TIMEOUT = 180
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

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
                "lab": "research", "academic": "research", "consulting": "consult",
                "marketing": "market", "oracle": "oracle", "cyber": "apex"}
    
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
    elif engine_key in ["lab", "academic"]:
        temperature = 0.5
    
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
    else:
        return format_generic_response(data, engine_key)

# ═══════════════════════════════════════════════════════════════
#  MAIN PROCESSING ENGINE — 3-Layer: AetherLang → OpenRouter → Fallback
# ═══════════════════════════════════════════════════════════════

async def process_query(query: str, engine_key: str, user_id: int, chat_id: int) -> str:
    """Process user query through multi-layer AI pipeline"""
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
    try:
        await send_typing(chat_id)
        node_map = {"chef": "chef", "molecular": "molecular", "omega": "chef",
                    "apex": "apex", "brain": "apex", "assembly": "assembly",
                    "lab": "research", "academic": "research", "consulting": "consult",
                    "marketing": "market", "oracle": "oracle", "cyber": "apex"}
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

🧠 <b>12 AI Engines Available:</b>

👨‍🍳 /chef — Michelin recipes + MacYuFBI + HACCP + financials
📈 /apex — Nobel-level business strategy (9-section)
🏛️ /assembly — 26+ legendary archetypes + Gandalf Veto
💼 /consulting — McKinsey reports: SWOT + Roadmap + KPIs
🔬 /lab — Deep scientific analysis + Nobel insights
📣 /marketing — Viral campaign generator
🎰 /oracle — <b>LIVE OPAP data</b> + statistics + lucky numbers
⚗️ /molecular — Molecular gastronomy techniques
🔥 /omega — Neural Kitchen (15 AI agents)
🧠 /brain — Super Brain Nobel mode
🔒 /cyber — Security intelligence
🎓 /academic — Search arXiv, PubMed + 12 sources

🌐 <b>Language:</b> /lang_el (Ελληνικά) | /lang_en (English)

💡 <b>Just type naturally!</b>
"Μουσακάς για 6 άτομα" → Chef Omega 🇬🇷
"Berlin restaurant strategy" → APEX Logic 🇬🇧
"Τζόκερ τυχεροί αριθμοί" → LIVE OPAP Oracle 🎰
"Should I invest in Bitcoin?" → Assembly convenes 🏛️

⚡ <b>Commands:</b>
/engines — List all engines
/assembly_modes — Assembly configurations  
/status — System health check
/lang_el — Ελληνικά | /lang_en — English

Built with ❤️ by Hlia — From Kitchen to Code
🔄 OpenRouter • 🛡️ FDA Safety • 🎰 LIVE OPAP • 📊 Live Markets"""
        
        await send_msg(chat_id, welcome)
        return
    
    if text == "/engines":
        lines = ["🧠 <b>AetherLang Ω — 12 AI Engines</b>\n"]
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
        await send_msg(chat_id, response)
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
                params={"offset": offset, "timeout": 30, "allowed_updates": ["message", "callback_query"]},
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
                    if "message" in update:
                        await handle_message(update)
                    elif "callback_query" in update:
                        await handle_callback(update)
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
