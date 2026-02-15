#!/usr/bin/env python3
"""
AetherLang Vision Chef Engine v4.0 — ELITE CULINARY INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6-Member Expert Council:
  🧑‍🍳 Executive Chef — Technique, timing, plating architecture
  🎨 Flavor Architect — MacYuFBI™ balance, compound pairing
  💰 F&B Director — Costing, menu pricing, scaling
  🛡️ HACCP Officer — Food safety, allergens, critical control points
  🏥 Clinical Nutritionist — Macros, micronutrients, dietary optimization
  🍷 Master Sommelier — Wine/beverage pairing, flavor bridge

Pipeline: OpenCV → GPT-4o Vision (Stage 1) → GPT-4o Council (Stage 2) → PDF

USAGE:
  from vision_chef import (
      run_vision_pipeline, run_text_recipe,
      generate_recipe_pdf, format_vision_telegram
  )
"""

import base64
import json
import math
import os
import re
import time
import logging
import subprocess
import numpy as np
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional, List

log = logging.getLogger("AetherLangBot")

# ── Optional deps ──
try:
    import cv2
    OPENCV_OK = True
except ImportError:
    OPENCV_OK = False

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    MPL_OK = True
except ImportError:
    MPL_OK = False

try:
    from weasyprint import HTML as WeasyHTML
    WEASY_OK = True
except ImportError:
    WEASY_OK = False

from openai import AsyncOpenAI
import httpx

_oai = None
def _get_oai():
    global _oai
    if _oai is None:
        key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY", "")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")
        _oai = AsyncOpenAI(api_key=key)
    return _oai


# ═══════════════════════════════════════════════════════════════
#  1. OPENCV PRE-ANALYSIS (Enhanced v4)
# ═══════════════════════════════════════════════════════════════

def opencv_analyze(image_bytes: bytes) -> Dict[str, Any]:
    """Enhanced texture analysis, meat/vegetable/seafood classification, color profiling"""
    if not OPENCV_OK:
        return {"available": False}
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {"available": False}
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        tex_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # Color ratios
        raw_r1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([20, 255, 200]))
        raw_r2 = cv2.inRange(hsv, np.array([160, 50, 50]), np.array([180, 255, 200]))
        raw_ratio = float(np.count_nonzero(cv2.bitwise_or(raw_r1, raw_r2))) / (h * w)

        brown_ratio = float(np.count_nonzero(
            cv2.inRange(hsv, np.array([10, 50, 30]), np.array([30, 200, 180])))) / (h * w)

        green_ratio = float(np.count_nonzero(
            cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255])))) / (h * w)

        white_ratio = float(np.count_nonzero(
            cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 40, 255])))) / (h * w)

        orange_ratio = float(np.count_nonzero(
            cv2.inRange(hsv, np.array([10, 100, 100]), np.array([25, 255, 255])))) / (h * w)

        yellow_ratio = float(np.count_nonzero(
            cv2.inRange(hsv, np.array([25, 80, 80]), np.array([35, 255, 255])))) / (h * w)

        # Classify primary content
        meat_type, conf = "UNKNOWN", 0.0
        food_category = "mixed"

        if raw_ratio > 0.10:
            food_category = "raw_meat"
            if tex_var > 400:
                meat_type, conf = "RAW_GROUND_MEAT_KEBAB", min(0.95, 0.5 + tex_var / 2000)
            elif tex_var > 200:
                meat_type, conf = "RAW_MEAT_CUT", min(0.85, 0.4 + tex_var / 1500)
            else:
                meat_type, conf = "RAW_SAUSAGE_SMOOTH", min(0.80, 0.5 + (200 - tex_var) / 500)
        elif brown_ratio > 0.20:
            food_category = "cooked"
            meat_type, conf = "COOKED_MEAT", min(0.80, 0.4 + brown_ratio)
        elif green_ratio > 0.25:
            food_category = "vegetables"
        elif white_ratio > 0.30:
            food_category = "dairy_or_seafood"
        elif orange_ratio > 0.15:
            food_category = "citrus_or_spiced"

        # Edge detection for shape complexity
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.count_nonzero(edges)) / (h * w)

        # Histogram for overall brightness
        brightness = float(np.mean(gray))

        return {
            "available": True,
            "dimensions": f"{w}x{h}",
            "texture_variance": round(tex_var, 1),
            "edge_density": round(edge_density, 3),
            "brightness": round(brightness, 1),
            "meat_type": meat_type,
            "meat_confidence": round(conf, 2),
            "food_category": food_category,
            "raw_ratio": round(raw_ratio, 3),
            "brown_ratio": round(brown_ratio, 3),
            "green_ratio": round(green_ratio, 3),
            "white_ratio": round(white_ratio, 3),
            "orange_ratio": round(orange_ratio, 3),
            "yellow_ratio": round(yellow_ratio, 3),
            "has_greens": green_ratio > 0.05,
            "likely_plated": edge_density > 0.08 and brightness > 100,
        }
    except Exception as e:
        log.error(f"OpenCV error: {e}")
        return {"available": False}


def opencv_hint(a: dict) -> str:
    """Build comprehensive LLM hint from OpenCV results"""
    if not a.get("available"):
        return ""
    parts = []
    mt = a.get("meat_type", "")
    fc = a.get("food_category", "")

    if mt == "RAW_GROUND_MEAT_KEBAB":
        parts.append(f"RAW GROUND MEAT (kimas) — texture:{a['texture_variance']} raw:{a['raw_ratio']} conf:{a['meat_confidence']:.0%} — NOT sausage/loukaniko!")
    elif mt == "RAW_MEAT_CUT":
        parts.append(f"Raw meat cut — texture:{a['texture_variance']} conf:{a['meat_confidence']:.0%}")
    elif mt == "COOKED_MEAT":
        parts.append(f"Cooked meat — brown:{a.get('brown_ratio', 0)}")

    if fc == "vegetables":
        parts.append(f"Predominantly vegetables (green:{a['green_ratio']:.1%})")
    elif fc == "dairy_or_seafood":
        parts.append(f"Likely dairy/seafood (white:{a['white_ratio']:.1%})")

    if a.get("has_greens"):
        parts.append(f"Greens present ({a['green_ratio']:.1%})")
    if a.get("likely_plated"):
        parts.append("Appears to be a plated/finished dish")
    if a.get("orange_ratio", 0) > 0.10:
        parts.append(f"Orange tones ({a['orange_ratio']:.1%}) — possible citrus/spice/tomato")

    return " | ".join(parts) if parts else ""


# ═══════════════════════════════════════════════════════════════
#  2. GPT-4o PROMPTS — 6-MEMBER CULINARY COUNCIL
# ═══════════════════════════════════════════════════════════════

STAGE1_SYSTEM = """You are the world's most advanced culinary computer vision system.
You work for a team of Michelin-starred chefs, F&B directors, and food scientists.
Your ONLY job: identify every ingredient visible in the photo with extreme precision.

CRITICAL RULES:
1. PACKAGING FIRST: If food is wrapped/packaged, READ ALL visible text, labels, logos, brand names BEFORE identifying. The packaging text tells you what's inside!
2. SHAPE-BASED MEAT IDENTIFICATION (use these exact guidelines):
   - Elongated cylinder (10-15cm, 3-4cm diameter, minced texture) = Kebab/Kempap
   - Flat rectangular cut (2-3cm thick, visible muscle grain) = Steak/fillet
   - Loose crumbly texture (no defined shape) = Ground/minced meat
   - Long thin cylindrical in casing = Sausage
   - Wrapped elongated shape + visible grill marks = Likely kebab, NOT biscuit
3. CONFIDENCE SCORING (be STRICT):
   - 0.9-1.0: Absolutely certain, clear visual confirmation, can read label
   - 0.7-0.9: Very confident, distinctive features visible
   - 0.5-0.7: Reasonably confident, some identifying features
   - 0.3-0.5: Unsure, vague visual match, similar to multiple items
   - 0.1-0.3: Complete guess, admit uncertainty
4. NEVER GUESS: If you can't identify something clearly, set confidence 0.3-0.5 and write in quality_notes: "Unclear - appears to be X but could be Y"
5. VISUAL CUE HIERARCHY (check in this order):
   a) Packaging text/labels (most reliable)
   b) Shape and dimensions (measure visually)
   c) Color and texture
   d) Context (other ingredients nearby)
   e) OpenCV analysis hints
6. COMMON MISTAKES TO AVOID:
   ❌ "Wrapped elongated item" → "biscuit" (CHECK: is it meat in plastic?)
   ❌ "Round white item" → "egg" (CHECK: could it be onion, garlic, mozzarella?)
   ❌ "Red liquid" → "tomato sauce" (CHECK: could it be blood from raw meat?)
   ❌ Ignoring visible text on packaging
7. Be SPECIFIC: "κεμπάπ μοσχαρίσιο" not just "κρέας". "φρέσκο βασιλικό" not just "χόρτο".
8. Trust OpenCV hints for meat type, color analysis, and texture detection
9. Each ingredient MUST have a confidence score that reflects your TRUE certainty

STATES: raw|cooked|fresh|dried|frozen|marinated|sliced|whole|diced|grated|packaged|wrapped|vacuum-sealed

Output PURE JSON:
{
  "ingredients": [
    {"name_gr": "Greek name", "name_en": "English name",
     "category": "protein|vegetable|dairy|spice|pantry|grain|seafood|fruit|herb|condiment",
     "quantity_estimate": "300g", "state": "raw|packaged|wrapped|etc",
     "quality_notes": "DETAILED visual: elongated 12cm x 4cm cylinder, minced texture visible, wrapped in clear plastic, grill marks present - definitely kebab NOT biscuit",
     "confidence": 0.85}
  ],
  "meat": {"type": "beef|pork|chicken|lamb", "cut": "kebab|steak|ground|fillet", "weight_estimate": "300g", "state": "raw|marinated", "fat_content": "low|medium|high"},
  "cuisine_hint": "Greek/Mediterranean/Asian/etc",
  "complexity": "simple|moderate|complex|masterchef",
  "detected_dishes": ["Only suggest if confident - empty array is OK"],
  "cooking_method_hints": ["grilling", "frying", "roasting"],
  "freshness_score": 8,
  "ingredient_count": 5,
  "photo_context": "supermarket|kitchen|restaurant|fridge|outdoor|market|other",
  "packaging_detected": true,
  "label_text_visible": "text on packaging if readable"
}

EXAMPLES OF GOOD quality_notes:
✅ "Elongated 15cm cylindrical shape, 4cm diameter, visible minced meat texture through clear plastic wrap, parallel grill marks - kebab 95% certain"
✅ "Can read 'FETA' on blue packaging label, white crumbly texture visible - definitely feta cheese"
✅ "Flat rectangular cut 3cm thick, red meat with white fat marbling, grain pattern visible - beef steak"
✅ "Unclear - wrapped item ~10cm long, could be kebab or sausage, confidence low due to opaque packaging"

EXAMPLES OF BAD quality_notes:
❌ "looks like meat" (too vague)
❌ "probably tomato" (be specific about WHY)
❌ "some vegetable" (identify or admit uncertainty)

Be exhaustive. Identify herbs, garnishes, sauces, background ingredients, visible labels.
PURE JSON only."""


def _build_council_prompt(lang: str, difficulty: str, servings: int, detected_dishes: list = None) -> str:
    """Build the elite 6-member council prompt for Stage 2"""
    if lang == "el":
        lang_block = """ΓΛΩΣΣΑ: ΟΛΑ στα ΕΛΛΗΝΙΚΑ.
- Ονόματα υλικών: Ελληνικά + (English σε παρένθεση)
- Βήματα εκτέλεσης: Αναλυτικά στα Ελληνικά, τεχνικοί όροι στα Αγγλικά σε παρένθεση
- Περιγραφή, tips, σημειώσεις: Ελληνικά
- Τεχνικές: Ελληνικά + (English)
- recipe_name: English, dish_name_greek: Ελληνικά
Παράδειγμα: 'Ζεσταίνουμε 30ml ελαιόλαδο σε βαθύ τηγάνι (heavy-bottom skillet) στους 180°C μέχρι να τρεμοπαίζει.'"""
    else:
        lang_block = """LANGUAGE: ALL in ENGLISH.
- Ingredient names: English + (Greek in parentheses)
- Steps: Detailed in English, Greek terms in parentheses
- Description, tips, notes: English
- Techniques: English + (Greek term)
- recipe_name: English, dish_name_greek: Greek
Example: 'Heat 30ml olive oil in a heavy-bottom skillet to 180°C until it begins to shimmer.'"""

    diff_map = {
        "easy": "Home cook level — simple techniques, common ingredients, forgiving timing.",
        "medium": "Experienced home cook — intermediate techniques, balanced flavors, some precision required.",
        "hard": "Professional level — advanced techniques, complex flavor layering, precise timing critical.",
        "masterchef": "Michelin level — molecular techniques, flavor compound pairing, architectural plating, zero margin for error."
    }

    dish_hint = ""
    if detected_dishes:
        dish_hint = f"\nDETECTED POSSIBLE DISHES: {', '.join(detected_dishes[:3])}\nUse these as inspiration but create the OPTIMAL recipe."

    return f"""You are the AETHERLANG CULINARY COUNCIL — six world-class experts collaborating on one perfect recipe.

YOUR COUNCIL:
🧑‍🍳 EXECUTIVE CHEF (technique, timing, thermal precision, plating architecture)
🎨 FLAVOR ARCHITECT (MacYuFBI™ 8-axis flavor balance, compound pairing, umami optimization)
💰 F&B DIRECTOR (food cost analysis, menu pricing, portion economics, scaling strategy)
🛡️ HACCP OFFICER (14 EU allergens, critical control points, safe temperatures, cross-contamination)
🏥 CLINICAL NUTRITIONIST (macro/micro optimization, glycemic impact, anti-inflammatory score, dietary flags)
🍷 MASTER SOMMELIER (wine pairing with flavor bridge analysis, alternative beverages, serving temperature)

{lang_block}
DIFFICULTY: {difficulty} — {diff_map.get(difficulty, diff_map['medium'])}
SERVINGS: {servings}
{dish_hint}

Each council member contributes their expertise. The result is ONE unified, extraordinary recipe.

OUTPUT PURE JSON with these sections:

{{
  "recipe_name": "English name",
  "dish_name_greek": "Ελληνικό όνομα",
  "description": "3-4 sentence poetic description that makes you hungry",
  "cuisine": "Greek/Mediterranean/etc",
  "difficulty": "{difficulty}",
  "servings": {servings},
  "prep_time_minutes": 20,
  "cook_time_minutes": 40,
  "total_time_minutes": 60,

  "ingredients": [
    {{
      "name": "Ελληνικό όνομα",
      "name_english": "English name",
      "amount": "300g",
      "amount_grams": 300,
      "category": "protein|vegetable|dairy|spice|pantry|grain|seafood",
      "preparation": "κομμένο σε κύβους (diced)",
      "substitutes": ["alternative 1", "alternative 2"],
      "quality_tip": "Choose bright red, firm tomatoes",
      "cost_eur": 2.50
    }}
  ],

  "steps": [
    {{
      "step_number": 1,
      "title": "Bilingual title GR (EN)",
      "action": "DETAILED 4-6 sentence instruction in GREEK first, then [ENGLISH translation]. Include EXACT grams, ml, temperatures, timing. Example: Προσθέτουμε 250g αλεύρι, 5g αλάτι και 200ml χλιαρό νερό (38°C) στο μπολ. Ζυμώνουμε για 8 λεπτά μέχρι η ζύμη να γίνει λεία και ελαστική. [Add 250g flour, 5g salt and 200ml lukewarm water (38°C) to the bowl. Knead for 8 minutes until dough is smooth and elastic.]",
      "timing": "8 minutes",
      "temperature": "180°C",
      "visual_cue": "Bilingual visual cue GR [EN]",
      "technique": "Ελληνικός όρος (English technique name)",
      "science": "Brief food science explanation",
      "pro_tip": "Bilingual pro tip GR [EN]",
      "equipment": ["exact equipment needed for this step"],
      "haccp_note": "Food safety note with temperatures",
      "chef_note": "Council member insight"
    }}
  ],

  CRITICAL FOR STEPS:
  - MINIMUM 10 steps, MAXIMUM 15 steps
  - Each step MUST have exact quantities in grams/ml
  - Each step MUST specify equipment needed
  - Each action MUST be 4-6 sentences with precise instructions
  - Include rest times, carry-over cooking, deglazing etc as separate steps
  - Mise en place is step 1
  - Final plating is the last step
  - BILINGUAL: Greek first, then [English in brackets]

  "mac_yu_fbi": {{
    "M": 8, "A": 6, "C": 3, "Y": 2, "U": 7, "F": 7, "B": 4, "I": 5,
    "dominant": "Maillard + Umami",
    "missing": "Slight acid deficiency",
    "balance_verdict": "Complex umami-forward profile with excellent Maillard development",
    "fix": "Add lemon zest at plating for acid brightness",
    "flavor_compounds": "glutamate + inosinate synergy, melanoidins from browning",
    "council_note": "Flavor Architect: The umami-Maillard bridge creates depth — acid fix elevates to 3-star level"
  }},

  "wine_pairing": {{
    "primary": {{"wine": "YOU MUST CHOOSE THE RIGHT WINE FOR THIS SPECIFIC DISH. DO NOT use Xinomavro unless the dish is grilled red meat or game. For seafood/fish → crisp white (Assyrtiko, Sauvignon Blanc, Albariño). For tomato-based dishes → medium red (Agiorgitiko, Sangiovese). For cream sauces → oaked white (Chardonnay, Viognier). For grilled meats → full-bodied red (Xinomavro, Cabernet, Syrah). MATCH THE WINE TO THE FOOD.",
                  "why": "Explain the specific flavor bridge between THIS wine and THIS dish's dominant flavors",
                  "flavor_bridge": "Exact compound connections: tannins + fat, acidity + salt, sweetness + spice, etc.",
                  "serving_temp": "correct temperature for the chosen wine type", "decant_minutes": 0}},
    "alternative_wine": {{"wine": "A COMPLETELY different wine style (if primary is red, choose white; if dry, choose off-dry)", "why": "Explain how this alternative approach works with the dish"}},
    "non_alcoholic": "Creative non-alcoholic pairing matched to the dish's flavor profile",
    "beer_pairing": "Specific beer style that complements this dish (IPA, lager, stout, wheat beer, etc.)",
    "council_note": "Master Sommelier: CRITICAL - Your wine choice must be justified by the dish's ingredients and cooking method. Red meat/game=full red (Xinomavro, Cabernet). White meat/fish=white (Assyrtiko, Sauvignon). Tomato sauce=medium red (Agiorgitiko). Cream=oaked white (Chardonnay). Spicy=off-dry (Gewürztraminer). DO NOT default to Xinomavro for every dish!"
  }},

  "allergen_matrix": {{
    "contains": ["gluten", "dairy", "eggs"],
    "may_contain": ["nuts"],
    "free_from": ["shellfish", "fish", "soy", "peanuts", "celery", "mustard", "sesame", "sulphites", "lupin", "molluscs"],
    "substitutions_for_free": {{
      "gluten_free": "Replace flour with rice flour + xanthan gum",
      "dairy_free": "Use coconut cream instead of heavy cream",
      "vegan": "Replace meat with king oyster mushrooms for umami"
    }},
    "council_note": "HACCP Officer: Cross-contamination risk with nuts if using shared cutting boards"
  }},

  "cost_analysis": {{
    "ingredient_cost_eur": 12.50,
    "cost_per_serving_eur": 3.12,
    "food_cost_pct": 28,
    "suggested_menu_price_eur": 14.90,
    "profit_margin_pct": 72,
    "scaling_notes": "Bulk herbs from Varvakios market reduce cost 40%",
    "council_note": "F&B Director: At 28% food cost, this is menu-ready. Premium positioning justified."
  }},

  "scaling_guide": {{
    "for_2": "Halve all ingredients. Reduce sauce by 40% (less evaporation in smaller pan)",
    "for_8": "Double recipe. Use larger pot — do NOT crowd the pan, work in batches",
    "for_20": "5x recipe. Pre-prep mise en place. Sauce can be made 24h ahead. Meat in 2 batches max",
    "banquet_50": "Commercial kitchen required. Par-cook proteins, finish à la minute"
  }},

  "nutritional_breakdown": {{
    "calories": 485,
    "protein_g": 32,
    "carbs_g": 28,
    "fat_g": 24,
    "fiber_g": 6,
    "sugar_g": 8,
    "sodium_mg": 680,
    "vitamins": "B12 (45% DV), Iron (30% DV), Zinc (25% DV)",
    "minerals": "Selenium (40% DV), Phosphorus (35% DV)",
    "anti_inflammatory_score": 7,
    "glycemic_load": "medium",
    "dietary_flags": ["high-protein", "Mediterranean"],
    "council_note": "Nutritionist: Excellent protein-to-calorie ratio. Add leafy greens side for fiber optimization."
  }},

  "common_mistakes": [
    "❌ ΛΑΘΟΣ: Overcrowding the pan → steaming instead of searing. ✅ ΣΩΣΤΟ: Work in batches, leave 2cm between pieces",
    "❌ ΛΑΘΟΣ: Adding cold ingredients to hot oil → temperature drop. ✅ ΣΩΣΤΟ: Room temperature ingredients always",
    "❌ ΛΑΘΟΣ: Cutting meat immediately after cooking. ✅ ΣΩΣΤΟ: Rest 5 min minimum — juices redistribute",
    "❌ ΛΑΘΟΣ: Seasoning only at the end. ✅ ΣΩΣΤΟ: Season at EVERY stage — layered flavor"
  ],

  "plating_guide": {{
    "plate_type": "Wide-rim matte charcoal ceramic, 28cm",
    "presentation_style": "Asymmetric modern — protein at 7 o'clock, sauce arc, height from garnish",
    "arrangement": "Base sauce first (spoon drag), protein angled, vegetables ascending, microgreens crown",
    "garnish": "Microgreens, flaky salt, olive oil drizzle, edible flowers if available",
    "color_theory": "Earth tones (brown protein) + green contrast + red sauce accent = visual triangle",
    "final_touch": "Warm the plate to 45°C before plating. Wipe rim with damp cloth.",
    "council_note": "Executive Chef: The plate is the canvas. Odd numbers, negative space, height variation."
  }},

  "technique_masterclass": {{
    "key_technique": "Reverse Sear (Αντίστροφο Σφράγισμα)",
    "explanation": "Low-slow cooking first (oven 120°C) to reach target internal temp, then high-heat sear for crust",
    "why_it_works": "Enzyme activity between 50-65°C tenderizes protein. Final sear creates Maillard without overcooking center",
    "common_in": "High-end steakhouses, Michelin kitchens",
    "practice_tip": "Use probe thermometer — remove from oven at 5°C below target (carryover cooking)"
  }},

  "cultural_context": {{
    "origin": "Brief history of the dish",
    "regional_variations": "How different regions prepare it",
    "seasonal_best": "Best months for peak ingredient quality",
    "pairing_traditions": "Traditional accompaniments"
  }},

  "zero_waste": {{
    "leftovers_ideas": ["Idea 1 for next day", "Idea 2 creative reuse"],
    "storage_tips": "Refrigerate in airtight container up to 3 days. Reheat gently at 160°C",
    "compost_items": ["Vegetable trimmings", "Herb stems"],
    "stock_from_scraps": "Bones + vegetable trimmings → 4-hour stock for future use"
  }},

  "equipment_needed": ["Heavy-bottom skillet", "Probe thermometer", "Sharp chef's knife"],

  "chef_wisdom": "A profound, memorable culinary quote or insight",
  "match_score": 95,

  "council_signatures": {{
    "executive_chef": "Technique and timing are flawless. Ready for service.",
    "flavor_architect": "MacYuFBI balanced. Compound synergy confirmed.",
    "fb_director": "Menu-viable at target food cost. Approved.",
    "haccp_officer": "All CCPs addressed. Allergen matrix complete. Safe.",
    "nutritionist": "Macro balance optimal. Anti-inflammatory profile strong.",
    "sommelier": "Pairing confirmed. Flavor bridge validated."
  }}
}}

CRITICAL RULES:
- Output PURE JSON only, no markdown
- Every section must be filled — no empty strings
- MINIMUM 10 steps, each with 4-6 sentences of detailed instructions
- ALL measurements in EXACT grams (g), milliliters (ml), and temperatures (°C)
- BILINGUAL: Greek FIRST, then [English in brackets] for actions, tips, visual cues
- Each ingredient MUST have amount_grams as integer
- Each step MUST list specific equipment needed
- Include preparation details: how to cut (size in cm), how to season (exact amounts)
- Each council member's voice must be present in their sections
- Costs in EUR, temperatures in °C
- All brackets must be properly closed
- The recipe must be so detailed that a complete beginner could execute it perfectly"""


# ═══════════════════════════════════════════════════════════════
#  3. PIPELINE
# ═══════════════════════════════════════════════════════════════

async def run_vision_pipeline(
    photo_bytes: bytes, lang: str = "el",
    difficulty: str = "medium", servings: int = 4
) -> Dict[str, Any]:
    """Photo → OpenCV → Stage1 (Vision) → Stage2 (Council) → Result"""
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")):
        raise RuntimeError("OPENAI_API_KEY / OPENAI_KEY not set")
    t0 = time.time()

    # Stage 0: OpenCV Pre-Analysis
    ocv = opencv_analyze(photo_bytes)
    hint = opencv_hint(ocv)
    t_ocv = round(time.time() - t0, 2)

    # Stage 1: GPT-4o Vision — Ingredient Identification
    t1 = time.time()
    b64 = base64.b64encode(photo_bytes).decode("utf-8")
    lang_hint = "Respond in GREEK." if lang == "el" else "Respond in ENGLISH."
    ocv_block = f"\nOPENCV ANALYSIS: {hint}\nTrust this data. If GROUND_MEAT → κιμάς, NOT λουκάνικο." if hint else ""

    r1 = await _get_oai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": STAGE1_SYSTEM},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}},
                {"type": "text", "text": f"{lang_hint}{ocv_block}\nIdentify ALL ingredients with precision. PURE JSON."}
            ]}
        ],
        max_tokens=2500, temperature=0.2,
        response_format={"type": "json_object"}, timeout=60.0
    )
    s1 = json.loads(r1.choices[0].message.content.strip())
    s1_tok = r1.usage.total_tokens if r1.usage else 0
    t_s1 = round(time.time() - t1, 1)

    # OpenCV meat corrections
    if "RAW_GROUND_MEAT" in ocv.get("meat_type", ""):
        bad_words = ["λουκάνικο", "loukaniko", "sausage"]
        for ing in s1.get("ingredients", []):
            if any(b in str(ing.get("name_gr", "")).lower() for b in bad_words):
                ing["name_gr"], ing["name_en"] = "κιμάς", "ground beef"
        meat_data = s1.get("meat", {})
        if isinstance(meat_data, dict) and any(b in str(meat_data.get("type", "")).lower() for b in bad_words):
            meat_data["type"], meat_data["cut"] = "κιμάς", "ground/minced"

    # Build ingredient text for Stage 2
    ing_lines = []
    for ing in s1.get("ingredients", []):
        if isinstance(ing, dict):
            line = f"- {ing.get('name_gr', ing.get('name_en', 'unknown'))}"
            if ing.get("name_en"):
                line += f" ({ing['name_en']})"
            if ing.get("quantity_estimate") or ing.get("quantity"):
                line += f" — {ing.get('quantity_estimate') or ing.get('quantity')}"
            if ing.get("state"):
                line += f" [{ing['state']}]"
            if ing.get("quality_notes"):
                line += f" | {ing['quality_notes']}"
            ing_lines.append(line)
    ing_text = "\n".join(ing_lines) or "No ingredients detected"

    detected_dishes = s1.get("detected_dishes", [])

    # Stage 2: GPT-4o Council — Full Recipe Creation
    t2 = time.time()
    council_prompt = _build_council_prompt(lang, difficulty, servings, detected_dishes)

    r2 = await _get_oai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": council_prompt},
            {"role": "user", "content": (
                f"DETECTED INGREDIENTS:\n{ing_text}\n\n"
                f"Cuisine hint: {s1.get('cuisine_hint', 'Mediterranean')}\n"
                f"Complexity: {s1.get('complexity', 'moderate')}\n"
                f"Freshness score: {s1.get('freshness_score', 'N/A')}/10\n\n"
                f"COUNCIL: Create the definitive recipe. Every member contributes. Difficulty: {difficulty} | Servings: {servings}"
            )}
        ],
        max_tokens=8000, temperature=0.6,
        response_format={"type": "json_object"}, timeout=120.0
    )
    recipe = json.loads(r2.choices[0].message.content.strip())
    s2_tok = r2.usage.total_tokens if r2.usage else 0
    t_s2 = round(time.time() - t2, 1)

    return {
        "ingredients": s1,
        "recipe": recipe,
        "opencv": ocv,
        "metrics": {
            "total_seconds": round(time.time() - t0, 1),
            "opencv_seconds": t_ocv,
            "stage1_seconds": t_s1,
            "stage2_seconds": t_s2,
            "stage1_tokens": s1_tok,
            "stage2_tokens": s2_tok,
            "total_tokens": s1_tok + s2_tok,
            "pipeline_version": "v4.0",
            "council_members": 6,
        }
    }


def format_ingredient_report(s1_results: list, lang: str = "el") -> str:
    """Format ingredient detection report for Telegram"""
    lines = []
    if lang == "el":
        lines.append("<b>\U0001f50d \u0391\u03bd\u03b1\u03b3\u03bd\u03ce\u03c1\u03b9\u03c3\u03b7 \u03a5\u03bb\u03b9\u03ba\u03ce\u03bd</b>")
    else:
        lines.append("<b>Ingredient Detection</b>")
    
    all_ingredients = []
    for pi, s1 in enumerate(s1_results):
        ings = s1.get("ingredients", [])
        if len(s1_results) > 1:
            lines.append(f"\nPhoto {pi+1}:")
        for ing in ings:
            if isinstance(ing, dict):
                name_gr = ing.get("name_gr", "")
                name_en = ing.get("name_en", "")
                conf = ing.get("confidence", 0)
                state = ing.get("state", "")
                qty = ing.get("quantity_estimate", "")
                if isinstance(conf, (int, float)) and conf >= 0.9:
                    cem = "+"
                elif isinstance(conf, (int, float)) and conf >= 0.7:
                    cem = "~"
                else:
                    cem = "?"
                cpct = f" {int(conf*100)}%" if isinstance(conf, (int, float)) and conf > 0 else ""
                line = f"  [{cem}] {_e(name_gr)}"
                if name_en:
                    line += f" ({_e(name_en)})"
                if qty:
                    line += f" - {_e(qty)}"
                if state:
                    line += f" [{_e(state)}]"
                line += cpct
                # FDA nutritional info
                fda = ing.get("fda_nutrients", {})
                if fda:
                    cals = fda.get("Energy", {}).get("value", "")
                    prot = fda.get("Protein", {}).get("value", "")
                    if cals:
                        line += f" | {cals}kcal"
                    if prot:
                        line += f" {prot}g prot"
                lines.append(line)
                all_ingredients.append(ing)
    
    cats = {}
    for ing in all_ingredients:
        c = ing.get("category", "other")
        cats[c] = cats.get(c, 0) + 1
    cat_text = ", ".join(f"{v}x {k}" for k, v in sorted(cats.items(), key=lambda x: -x[1]))
    lines.append(f"\nTotal: {len(all_ingredients)} ingredients | {cat_text}")
    
    for s1 in s1_results:
        dishes = s1.get("detected_dishes", [])
        if dishes:
            lines.append(f"Possible: {', '.join(dishes[:3])}")
    
    cooked = sum(1 for i in all_ingredients if i.get("state", "") in ("cooked", "grilled", "fried", "baked", "roasted"))
    raw = sum(1 for i in all_ingredients if i.get("state", "") in ("raw", "fresh", "whole"))
    if cooked > raw and cooked >= 2:
        lines.append("\nMode: Finished Dish - Recipe recreation")
    else:
        lines.append("\nMode: Raw Ingredients - Recipe creation")

    # Add total nutritional summary if FDA data is available
    total_cals = 0
    total_prot = 0
    total_fat = 0
    total_carbs = 0
    total_fiber = 0
    fda_count = 0

    for ing in all_ingredients:
        fda = ing.get("fda_nutrients", {})
        if fda:
            fda_count += 1
            # Estimate based on amount (rough calculation per 100g)
            amount_g = ing.get("amount_grams", 100)
            factor = amount_g / 100.0

            if "Energy" in fda:
                total_cals += fda["Energy"]["value"] * factor
            if "Protein" in fda:
                total_prot += fda["Protein"]["value"] * factor
            if "Fat" in fda:
                total_fat += fda["Fat"]["value"] * factor
            if "Carbohydrates" in fda:
                total_carbs += fda["Carbohydrates"]["value"] * factor
            if "Fiber" in fda:
                total_fiber += fda["Fiber"]["value"] * factor

    if fda_count > 0:
        nutr_label = "Συνολική Θρεπτική Αξία" if lang == "el" else "Total Nutritional Value"
        lines.append(f"\n📊 {nutr_label} ({fda_count}/{len(all_ingredients)} ingredients):")
        if total_cals > 0:
            lines.append(f"   Energy: {int(total_cals)} kcal")
        if total_prot > 0:
            lines.append(f"   Protein: {total_prot:.1f}g")
        if total_fat > 0:
            lines.append(f"   Fat: {total_fat:.1f}g")
        if total_carbs > 0:
            lines.append(f"   Carbs: {total_carbs:.1f}g")
        if total_fiber > 0:
            lines.append(f"   Fiber: {total_fiber:.1f}g")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# FDA API INTEGRATION - Nutritional Data Enrichment
# ══════════════════════════════════════════════════════════════════

async def fda_enrich_ingredients(ingredients: list) -> list:
    """
    Enrich ingredients with USDA FoodData Central nutritional data.
    Returns the same ingredient list with added 'fda_nutrients' field.
    """
    FDA_API_KEY = os.getenv("FDA_API_KEY", "")
    if not FDA_API_KEY:
        log.warning("FDA_API_KEY not set - skipping nutritional enrichment")
        return ingredients

    FDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    async with httpx.AsyncClient(timeout=10.0) as client:
        for ing in ingredients:
            try:
                # Get ingredient name (prefer English for better FDA matches)
                query = ing.get("name_english", ing.get("name", "")).lower()
                if not query or len(query) < 2:
                    continue

                # Clean query (remove parentheses, Greek text, amounts)
                query = re.sub(r'\([^)]*\)', '', query)  # Remove (Greek)
                query = re.sub(r'\d+.*?(g|ml|kg|l|oz|lb)', '', query)  # Remove amounts
                query = query.strip()

                if len(query) < 2:
                    continue

                # Call FDA API (get top 5 results to find best match)
                params = {
                    "api_key": FDA_API_KEY,
                    "query": query,
                    "pageSize": 5
                }

                response = await client.get(FDA_BASE_URL, params=params)
                if response.status_code != 200:
                    continue

                data = response.json()
                foods = data.get("foods", [])
                if not foods:
                    continue

                # Prefer Foundation, SR Legacy, or Survey data over Branded
                food = None
                for f in foods:
                    dtype = f.get("dataType", "")
                    if dtype in ["Foundation", "SR Legacy", "Survey (FNDDS)"]:
                        food = f
                        break

                # Fallback to first result if no preferred type found
                if not food:
                    food = foods[0]

                nutrients = food.get("foodNutrients", [])

                # Extract key nutrients (per 100g)
                fda_nutrients = {}
                nutrient_map = {
                    "Energy": "Energy",
                    "Protein": "Protein",
                    "Total lipid (fat)": "Fat",
                    "Carbohydrate, by difference": "Carbohydrates",
                    "Fiber, total dietary": "Fiber"
                }

                for nutrient in nutrients:
                    name = nutrient.get("nutrientName", "")
                    value = nutrient.get("value", 0)
                    unit = nutrient.get("unitName", "")

                    # Map to simplified names
                    if name in nutrient_map:
                        key = nutrient_map[name]
                        fda_nutrients[key] = {
                            "value": round(value, 1),
                            "unit": unit
                        }
                    # Also check for exact matches of simplified names
                    elif name in ["Energy", "Protein", "Fat", "Carbohydrates", "Fiber"]:
                        fda_nutrients[name] = {
                            "value": round(value, 1),
                            "unit": unit
                        }

                if fda_nutrients:
                    ing["fda_nutrients"] = fda_nutrients
                    log.info(f"FDA enriched: {query} → {len(fda_nutrients)} nutrients")

            except Exception as e:
                log.debug(f"FDA lookup failed for {ing.get('name', 'unknown')}: {e}")
                continue

    return ingredients


async def run_vision_pipeline_multi(
    photos: list, lang: str = "el",
    difficulty: str = "medium", servings: int = 4
) -> Dict[str, Any]:
    """Multiple photos -> OpenCV -> Stage1 each -> Merge -> Stage2 Council -> Result"""
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")):
        raise RuntimeError("OPENAI_API_KEY / OPENAI_KEY not set")
    t0 = time.time()
    all_s1 = []
    all_ing_lines = []
    all_detected_dishes = []
    total_s1_tok = 0
    
    for i, photo_bytes in enumerate(photos):
        ocv = opencv_analyze(photo_bytes)
        hint = opencv_hint(ocv)
        b64 = base64.b64encode(photo_bytes).decode("utf-8")
        lang_hint = "Respond in GREEK." if lang == "el" else "Respond in ENGLISH."
        ocv_block = f"\nOPENCV ANALYSIS: {hint}\nTrust this data." if hint else ""
        photo_label = f"Photo {i+1}/{len(photos)}. " if len(photos) > 1 else ""
        
        r1 = await _get_oai().chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": STAGE1_SYSTEM},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}},
                    {"type": "text", "text": f"{photo_label}{lang_hint}{ocv_block}\nIdentify ALL ingredients. PURE JSON."}
                ]}
            ],
            max_tokens=2500, temperature=0.2,
            response_format={"type": "json_object"}, timeout=60.0
        )
        s1 = json.loads(r1.choices[0].message.content.strip())
        total_s1_tok += r1.usage.total_tokens if r1.usage else 0
        all_s1.append(s1)
        
        for ing in s1.get("ingredients", []):
            if isinstance(ing, dict):
                line = f"- {ing.get('name_gr', ing.get('name_en', 'unknown'))}"
                if ing.get("name_en"):
                    line += f" ({ing['name_en']})"
                if ing.get("quantity_estimate") or ing.get("quantity"):
                    line += f" - {ing.get('quantity_estimate') or ing.get('quantity')}"
                if ing.get("state"):
                    line += f" [{ing['state']}]"
                all_ing_lines.append(line)
        all_detected_dishes.extend(s1.get("detected_dishes", []))
    
    t_s1 = round(time.time() - t0, 1)
    
    # FDA enrichment
    try:
        all_ings_flat = []
        for s1 in all_s1:
            all_ings_flat.extend(s1.get("ingredients", []))
        enriched = await fda_enrich_ingredients(all_ings_flat)
        # Put back
        idx = 0
        for s1 in all_s1:
            for j in range(len(s1.get("ingredients", []))):
                if idx < len(enriched):
                    s1["ingredients"][j] = enriched[idx]
                    idx += 1
    except Exception:
        pass
    
    seen = set()
    unique_lines = []
    for line in all_ing_lines:
        key = line.split("(")[0].strip().lower()
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)
    ing_text = "\n".join(unique_lines) or "No ingredients detected"
    
    all_ings = []
    for s1 in all_s1:
        all_ings.extend(s1.get("ingredients", []))
    cooked = sum(1 for i in all_ings if i.get("state", "") in ("cooked", "grilled", "fried", "baked", "roasted"))
    raw = sum(1 for i in all_ings if i.get("state", "") in ("raw", "fresh", "whole"))
    mode_hint = "\nMODE: FINISHED DISH - Reverse-engineer this dish." if cooked > raw and cooked >= 2 else "\nMODE: RAW INGREDIENTS - Create the best recipe from these ingredients."
    
    t2 = time.time()
    detected_dishes = list(set(all_detected_dishes))[:5]
    council_prompt = _build_council_prompt(lang, difficulty, servings, detected_dishes)
    photos_note = f"\n{len(photos)} photos analyzed. " if len(photos) > 1 else ""
    
    r2 = await _get_oai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": council_prompt},
            {"role": "user", "content": (
                f"DETECTED INGREDIENTS ({len(unique_lines)} unique):{photos_note}\n{ing_text}\n\n"
                f"Cuisine hint: {all_s1[0].get('cuisine_hint', 'Mediterranean')}\n"
                f"Complexity: {all_s1[0].get('complexity', 'moderate')}\n"
                f"{mode_hint}\n\n"
                f"COUNCIL: Create the definitive recipe. Every member contributes. Difficulty: {difficulty} | Servings: {servings}"
            )}
        ],
        max_tokens=8000, temperature=0.6,
        response_format={"type": "json_object"}, timeout=120.0
    )
    recipe = json.loads(r2.choices[0].message.content.strip())
    s2_tok = r2.usage.total_tokens if r2.usage else 0
    t_s2 = round(time.time() - t2, 1)
    
    return {
        "ingredients_list": all_s1,
        "ingredients": all_s1[0] if all_s1 else {},
        "recipe": recipe,
        "opencv": opencv_analyze(photos[0]),
        "metrics": {
            "total_seconds": round(time.time() - t0, 1),
            "stage1_seconds": t_s1,
            "stage2_seconds": t_s2,
            "stage1_tokens": total_s1_tok,
            "stage2_tokens": s2_tok,
            "total_tokens": total_s1_tok + s2_tok,
            "pipeline_version": "v4.1",
            "council_members": 6,
            "photos_analyzed": len(photos),
        }
    }


async def run_text_recipe(
    text: str, lang: str = "el",
    difficulty: str = "medium", servings: int = 4
) -> Dict[str, Any]:
    """Text → Council Recipe (Stage 2 only)"""
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")):
        raise RuntimeError("OPENAI_API_KEY / OPENAI_KEY not set")
    t0 = time.time()
    council_prompt = _build_council_prompt(lang, difficulty, servings)

    r = await _get_oai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": council_prompt},
            {"role": "user", "content": (
                f"INGREDIENTS / REQUEST:\n{text}\n\n"
                f"COUNCIL: Create the definitive recipe. Difficulty: {difficulty} | Servings: {servings}"
            )}
        ],
        max_tokens=8000, temperature=0.6,
        response_format={"type": "json_object"}, timeout=120.0
    )
    return {
        "recipe": json.loads(r.choices[0].message.content.strip()),
        "metrics": {
            "total_seconds": round(time.time() - t0, 1),
            "total_tokens": r.usage.total_tokens if r.usage else 0,
            "pipeline_version": "v4.0",
            "council_members": 6,
        }
    }


# ═══════════════════════════════════════════════════════════════
#  4. CHART GENERATION
# ═══════════════════════════════════════════════════════════════

def _radar_b64(mac: dict) -> str:
    """MacYuFBI™ radar chart → base64 PNG"""
    if not MPL_OK or not mac:
        return ""
    try:
        keys = ['M', 'A', 'C', 'Y', 'U', 'F', 'B', 'I']
        labels = ['Maillard', 'Acid', 'Capsaicin', 'Yeast', 'Umami', 'Fat', 'Bitter', 'Ionic']
        vals = [float(mac.get(k, 0)) for k in keys] + [float(mac.get('M', 0))]
        angles = [n / 8 * 2 * math.pi for n in range(8)] + [0]

        fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#0c0a09')
        ax.set_facecolor('#0c0a09')
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'], color='#78716c', size=7)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, color='#fbbf24', size=8, fontweight='bold')
        ax.spines['polar'].set_color('#44403c')
        ax.grid(color='#44403c', linewidth=0.5, alpha=0.5)

        # Filled area with gradient effect
        ax.fill(angles, vals, color='#f59e0b', alpha=0.15)
        ax.plot(angles, vals, color='#f59e0b', linewidth=2.5)
        for a, v in zip(angles[:-1], vals[:-1]):
            ax.plot(a, v, 'o', color='#f59e0b', markersize=6, markeredgecolor='#0c0a09', markeredgewidth=1)
            ax.annotate(f'{v:.0f}', (a, v), textcoords="offset points",
                       xytext=(0, 10), ha='center', color='#fafaf9', fontsize=7, fontweight='bold')

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0c0a09')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception:
        return ""


def _nutr_b64(n: dict) -> str:
    """Nutrition chart → base64 PNG"""
    if not MPL_OK or not n:
        return ""
    try:
        items = [(l, float(v), c) for l, v, c in [
            ('Protein', n.get('protein_g'), '#22c55e'),
            ('Carbs', n.get('carbs_g'), '#3b82f6'),
            ('Fat', n.get('fat_g'), '#f59e0b'),
            ('Fiber', n.get('fiber_g'), '#a855f7'),
            ('Sugar', n.get('sugar_g'), '#ef4444'),
        ] if v]
        if not items:
            return ""
        labels, values, colors = zip(*items)

        fig, ax = plt.subplots(figsize=(4, 2.2))
        fig.patch.set_facecolor('#0c0a09')
        ax.set_facecolor('#0c0a09')
        bars = ax.barh(labels, values, color=colors, height=0.5, edgecolor='#1c1917', linewidth=0.5)
        ax.set_xlim(0, max(values) * 1.35)
        for b, v in zip(bars, values):
            ax.text(b.get_width() + 0.8, b.get_y() + b.get_height() / 2,
                    f'{v:.0f}g', va='center', color='#fafaf9', fontsize=9, fontweight='bold')
        ax.tick_params(colors='#a8a29e', labelsize=9)
        for s in ['top', 'right']:
            ax.spines[s].set_visible(False)
        for s in ['bottom', 'left']:
            ax.spines[s].set_color('#44403c')
        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0c0a09')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception:
        return ""


def _cost_b64(cost: dict) -> str:
    """Cost breakdown pie chart → base64 PNG"""
    if not MPL_OK or not cost:
        return ""
    try:
        fc = float(cost.get("food_cost_pct", 30))
        profit = 100 - fc
        fig, ax = plt.subplots(figsize=(2.5, 2.5))
        fig.patch.set_facecolor('#0c0a09')
        ax.set_facecolor('#0c0a09')
        wedges, texts, autotexts = ax.pie(
            [fc, profit], labels=['Food Cost', 'Margin'],
            colors=['#ef4444', '#22c55e'], autopct='%1.0f%%',
            startangle=90, textprops={'color': '#fafaf9', 'fontsize': 9}
        )
        for t in autotexts:
            t.set_fontweight('bold')
        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor='#0c0a09')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════
#  5. PDF GENERATION — ELITE DARK THEME
# ═══════════════════════════════════════════════════════════════

def _strip_emojis(html: str) -> str:
    """Remove emoji characters that crash WeasyPrint font subsetting"""
    import re
    emoji_pattern = re.compile(
        "[🌀-🧿"  # symbols & pictographs
        "🨀-🩯"  # chess symbols
        "🩰-🫿"  # symbols extended
        "✂-➰"  # dingbats
        "︀-️"  # variation selectors
        "‍"             # zero width joiner
        "Ⓜ-🉑"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', html)


def _e(t):
    """HTML-escape"""
    if t is None:
        return ""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_recipe_pdf(recipe: dict, metrics: dict, output_path: str) -> str:
    """Generate elite dark-theme A4 recipe PDF"""
    if not WEASY_OK:
        raise RuntimeError("WeasyPrint not installed")

    name = _e(recipe.get("dish_name_greek") or recipe.get("recipe_name") or "Recipe")
    name_en = _e(recipe.get("recipe_name", ""))
    desc = _e(recipe.get("description", ""))
    diff = _e(recipe.get("difficulty", "medium"))
    svgs = recipe.get("servings", 4)
    prep = recipe.get("prep_time_minutes", "")
    cook = recipe.get("cook_time_minutes", "")
    total_t = recipe.get("total_time_minutes", "")
    cost_data = recipe.get("cost_analysis", {})
    cuisine = _e(recipe.get("cuisine", ""))

    radar = _radar_b64(recipe.get("mac_yu_fbi", {}))
    nchart = _nutr_b64(recipe.get("nutritional_breakdown", {}))
    cost_chart = _cost_b64(cost_data)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Ingredients Table ──
    ing_rows = ""
    total_cost = 0
    for i, ing in enumerate(recipe.get("ingredients", [])):
        if isinstance(ing, dict):
            bg = "#1c1917" if i % 2 == 0 else "#292524"
            n = _e(ing.get("name", ""))
            ne = _e(ing.get("name_english", ""))
            amt = _e(ing.get("amount", ""))
            prp = _e(ing.get("preparation", ""))
            qt = _e(ing.get("quality_tip", ""))
            c = ing.get("cost_eur", 0)
            if c:
                total_cost += float(c)
            ing_rows += f'<tr style="background:{bg}">'
            ing_rows += f'<td class="ic">{i+1}</td>'
            ing_rows += f'<td class="in"><b>{n}</b>'
            if ne:
                ing_rows += f' <span class="dim">({ne})</span>'
            if prp:
                ing_rows += f'<br><span class="dim">{prp}</span>'
            if qt:
                ing_rows += f'<br><span class="tip">💡 {qt}</span>'
            ing_rows += '</td>'
            ing_rows += f'<td class="ia">{amt}</td>'
            if c:
                ing_rows += f'<td class="ip">€{c:.2f}</td>'
            else:
                ing_rows += '<td class="ip">—</td>'
            ing_rows += '</tr>'

    # ── Steps ──
    steps_html = ""
    for s in recipe.get("steps", []):
        eq = s.get("equipment", "")
        if isinstance(eq, list):
            eq = ", ".join(eq)
        steps_html += f'<div class="step">'
        steps_html += f'<div class="step-head">'
        steps_html += f'<span class="step-num">{s.get("step_number", "")}</span>'
        steps_html += f'<span class="step-title">{_e(s.get("title") or s.get("technique", ""))}</span>'
        if s.get("timing"):
            steps_html += f'<span class="step-time">⏱ {_e(s["timing"])}</span>'
        if s.get("temperature"):
            steps_html += f'<span class="step-temp">🌡 {_e(s["temperature"])}</span>'
        steps_html += '</div>'
        steps_html += f'<p class="step-action">{_e(s.get("action", ""))}</p>'
        if s.get("visual_cue"):
            steps_html += f'<div class="step-box visual">👁 VISUAL: {_e(s["visual_cue"])}</div>'
        if s.get("science"):
            steps_html += f'<div class="step-box science">🔬 SCIENCE: {_e(s["science"])}</div>'
        if s.get("pro_tip"):
            steps_html += f'<div class="step-box protip">💡 PRO TIP: {_e(s["pro_tip"])}</div>'
        if s.get("haccp_note"):
            steps_html += f'<div class="step-box haccp">🛡️ HACCP: {_e(s["haccp_note"])}</div>'
        if s.get("chef_note"):
            steps_html += f'<div class="step-box chef">🧑‍🍳 {_e(s["chef_note"])}</div>'
        if eq:
            steps_html += f'<p class="step-equip">🍳 {_e(str(eq))}</p>'
        steps_html += '</div>'

    # ── Allergen Matrix ──
    allergen_html = ""
    allergens = recipe.get("allergen_matrix", {})
    if allergens:
        contains = allergens.get("contains", [])
        may = allergens.get("may_contain", [])
        free = allergens.get("free_from", [])
        allergen_html = '<div class="section"><h2>🛡️ Allergen Matrix</h2><div class="allergen-grid">'
        for a in contains:
            allergen_html += f'<span class="allergen red">⚠️ {_e(a)}</span>'
        for a in may:
            allergen_html += f'<span class="allergen yellow">⚡ {_e(a)}</span>'
        for a in free[:6]:
            allergen_html += f'<span class="allergen green">✅ {_e(a)}</span>'
        allergen_html += '</div>'
        subs = allergens.get("substitutions_for_free", {})
        if subs:
            for k, v in subs.items():
                allergen_html += f'<p class="sub-note"><b>{_e(k)}:</b> {_e(v)}</p>'
        if allergens.get("council_note"):
            allergen_html += f'<p class="council-note">{_e(allergens["council_note"])}</p>'
        allergen_html += '</div>'

    # ── Cost Analysis ──
    cost_html = ""
    if cost_data:
        cost_img = f'<img src="data:image/png;base64,{cost_chart}" class="chart-sm">' if cost_chart else ''
        cost_html = f'<div class="section"><h2>💰 Cost Analysis</h2><div class="cost-grid">'
        cost_html += f'<div class="cost-item"><span class="cost-label">Ingredients</span><span class="cost-val">€{cost_data.get("ingredient_cost_eur", "?")}</span></div>'
        cost_html += f'<div class="cost-item"><span class="cost-label">Per Serving</span><span class="cost-val">€{cost_data.get("cost_per_serving_eur", "?")}</span></div>'
        cost_html += f'<div class="cost-item"><span class="cost-label">Food Cost</span><span class="cost-val">{cost_data.get("food_cost_pct", "?")}%</span></div>'
        cost_html += f'<div class="cost-item"><span class="cost-label">Menu Price</span><span class="cost-val gold">€{cost_data.get("suggested_menu_price_eur", "?")}</span></div>'
        cost_html += f'</div>{cost_img}'
        if cost_data.get("council_note"):
            cost_html += f'<p class="council-note">{_e(cost_data["council_note"])}</p>'
        cost_html += '</div>'

    # ── Wine Pairing ──
    wine_html = ""
    w = recipe.get("wine_pairing", {})
    if w:
        primary = w.get("primary", w) if isinstance(w.get("primary"), dict) else w
        wine_html = '<div class="section wine"><h2>🍷 Wine & Beverage Pairing</h2>'
        wine_name = primary.get("wine", w.get("recommended", ""))
        if wine_name:
            wine_html += f'<p class="wine-name">{_e(wine_name)}</p>'
            if primary.get("why") or w.get("why"):
                wine_html += f'<p class="wine-why">{_e(primary.get("why") or w.get("why"))}</p>'
            if primary.get("flavor_bridge"):
                wine_html += f'<p class="wine-bridge">🌉 Flavor Bridge: {_e(primary["flavor_bridge"])}</p>'
        if w.get("non_alcoholic"):
            wine_html += f'<p class="wine-alt">🥤 Non-alcoholic: {_e(w["non_alcoholic"])}</p>'
        if w.get("beer_pairing"):
            wine_html += f'<p class="wine-alt">🍺 Beer: {_e(w["beer_pairing"])}</p>'
        if w.get("council_note"):
            wine_html += f'<p class="council-note">{_e(w["council_note"])}</p>'
        wine_html += '</div>'

    # ── MacYuFBI ──
    mac = recipe.get("mac_yu_fbi", {})
    mac_html = ""
    if mac:
        radar_img = f'<img src="data:image/png;base64,{radar}" class="chart-md">' if radar else ''
        mac_html = f'<div class="section"><h2>🎯 MacYuFBI™ Flavor Profile</h2>{radar_img}'
        if mac.get("balance_verdict"):
            mac_html += f'<p class="verdict">{_e(mac["balance_verdict"])}</p>'
        if mac.get("fix"):
            mac_html += f'<p class="fix">💡 {_e(mac["fix"])}</p>'
        if mac.get("flavor_compounds"):
            mac_html += f'<p class="compounds">🧬 {_e(mac["flavor_compounds"])}</p>'
        if mac.get("council_note"):
            mac_html += f'<p class="council-note">{_e(mac["council_note"])}</p>'
        mac_html += '</div>'

    # ── Nutrition ──
    nutr = recipe.get("nutritional_breakdown", {})
    nutr_html = ""
    if nutr:
        nutr_img = f'<img src="data:image/png;base64,{nchart}" class="chart-md">' if nchart else ''
        nutr_html = f'<div class="section"><h2>📊 Nutritional Breakdown</h2>'
        if nutr.get("calories"):
            nutr_html += f'<p class="calories">{nutr["calories"]} kcal</p>'
        nutr_html += nutr_img
        if nutr.get("dietary_flags"):
            flags = nutr["dietary_flags"] if isinstance(nutr["dietary_flags"], list) else [nutr["dietary_flags"]]
            nutr_html += '<div class="flags">' + ''.join(f'<span class="flag">{_e(f)}</span>' for f in flags) + '</div>'
        if nutr.get("council_note"):
            nutr_html += f'<p class="council-note">{_e(nutr["council_note"])}</p>'
        nutr_html += '</div>'

    # ── Mistakes ──
    mistakes = recipe.get("common_mistakes", [])
    mist_html = ""
    if mistakes:
        mist_html = '<div class="section"><h2>⚠️ Common Mistakes</h2>'
        for m in mistakes:
            mist_html += f'<div class="mistake">{_e(str(m))}</div>'
        mist_html += '</div>'

    # ── Plating ──
    pl = recipe.get("plating_guide", {})
    pl_html = ""
    if pl:
        pl_html = '<div class="section"><h2>🎨 Plating Guide</h2>'
        for lab, key in [("Style", "presentation_style"), ("Plate", "plate_type"),
                         ("Arrangement", "arrangement"), ("Garnish", "garnish"),
                         ("Color Theory", "color_theory"), ("Final Touch", "final_touch")]:
            if pl.get(key):
                pl_html += f'<p class="pl-item"><span class="pl-label">{lab}:</span> {_e(pl[key])}</p>'
        if pl.get("council_note"):
            pl_html += f'<p class="council-note">{_e(pl["council_note"])}</p>'
        pl_html += '</div>'

    # ── Technique Masterclass ──
    tech = recipe.get("technique_masterclass", {})
    tech_html = ""
    if tech and tech.get("key_technique"):
        tech_html = f'<div class="section masterclass"><h2>🎓 Technique Masterclass</h2>'
        tech_html += f'<p class="tech-name">{_e(tech["key_technique"])}</p>'
        if tech.get("explanation"):
            tech_html += f'<p class="tech-exp">{_e(tech["explanation"])}</p>'
        if tech.get("why_it_works"):
            tech_html += f'<p class="tech-why">🔬 {_e(tech["why_it_works"])}</p>'
        if tech.get("practice_tip"):
            tech_html += f'<p class="tech-tip">💡 {_e(tech["practice_tip"])}</p>'
        tech_html += '</div>'

    # ── Scaling ──
    scale = recipe.get("scaling_guide", {})
    scale_html = ""
    if scale:
        scale_html = '<div class="section"><h2>📐 Scaling Guide</h2>'
        for k, label in [("for_2", "2 servings"), ("for_8", "8 servings"),
                         ("for_20", "20 servings"), ("banquet_50", "50+ banquet")]:
            if scale.get(k):
                scale_html += f'<p class="scale-item"><b>{label}:</b> {_e(scale[k])}</p>'
        scale_html += '</div>'

    # ── Zero Waste ──
    zw = recipe.get("zero_waste", {})
    zw_html = ""
    if zw:
        zw_html = '<div class="section"><h2>♻️ Zero Waste</h2>'
        for idea in zw.get("leftovers_ideas", []):
            zw_html += f'<p class="zw-idea">♻️ {_e(idea)}</p>'
        if zw.get("storage_tips"):
            zw_html += f'<p class="zw-store">📦 {_e(zw["storage_tips"])}</p>'
        if zw.get("stock_from_scraps"):
            zw_html += f'<p class="zw-stock">🍲 {_e(zw["stock_from_scraps"])}</p>'
        zw_html += '</div>'

    # ── Cultural Context ──
    culture = recipe.get("cultural_context", {})
    culture_html = ""
    if culture and culture.get("origin"):
        culture_html = '<div class="section"><h2>📜 Cultural Context</h2>'
        culture_html += f'<p>{_e(culture["origin"])}</p>'
        if culture.get("regional_variations"):
            culture_html += f'<p class="dim">{_e(culture["regional_variations"])}</p>'
        if culture.get("seasonal_best"):
            culture_html += f'<p>🌿 Best season: {_e(culture["seasonal_best"])}</p>'
        culture_html += '</div>'

    # ── Council Signatures ──
    sigs = recipe.get("council_signatures", {})
    sig_html = ""
    if sigs:
        sig_html = '<div class="section signatures"><h2>✍️ Council Signatures</h2><div class="sig-grid">'
        icons = {"executive_chef": "🧑‍🍳", "flavor_architect": "🎨", "fb_director": "💰",
                 "haccp_officer": "🛡️", "nutritionist": "🏥", "sommelier": "🍷"}
        for key, icon in icons.items():
            if sigs.get(key):
                sig_html += f'<div class="sig-card"><span class="sig-icon">{icon}</span><p class="sig-text">{_e(sigs[key])}</p></div>'
        sig_html += '</div></div>'

    # ── Chef Wisdom ──
    wisdom = recipe.get("chef_wisdom", "")
    wis_html = ""
    if wisdom:
        wis_html = f'<div class="wisdom"><p class="wis-icon">👨‍🍳</p><p class="wis-text">"{_e(wisdom)}"</p></div>'

    # ── Metrics ──
    m = metrics or {}
    met_html = f'<div class="metrics">Pipeline v{m.get("pipeline_version", "4.0")} | {m.get("total_seconds", "?")}s | S1: {m.get("stage1_seconds", "?")}s | S2: {m.get("stage2_seconds", "?")}s | {m.get("total_tokens", "?")} tokens | Council: {m.get("council_members", 6)} members</div>'

    # ══════════ FULL HTML ══════════
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 15mm 14mm;
  @bottom-center {{ content: "AetherLang Vision Chef v4 — Page " counter(page) "/" counter(pages); font-size: 7px; color: #78716c; }}
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI','Helvetica Neue',Arial,sans-serif; background:#0c0a09; color:#fafaf9; font-size:10pt; line-height:1.5; }}
table {{ width:100%; border-collapse:collapse; }}

/* Header */
.header {{ text-align:center; padding:20px 0; border-bottom:3px solid #f59e0b; margin-bottom:18px; }}
.header .brand {{ font-size:8pt; color:#f59e0b; letter-spacing:4px; text-transform:uppercase; }}
.header h1 {{ font-size:22pt; color:#fafaf9; margin:8px 0 2px; font-weight:800; }}
.header .sub {{ color:#78716c; font-size:11px; }}
.header .desc {{ color:#a8a29e; font-size:10px; margin-top:8px; max-width:480px; display:inline-block; }}
.badges {{ display:flex; gap:6px; justify-content:center; margin-top:10px; flex-wrap:wrap; }}
.badge {{ padding:2px 10px; border-radius:10px; font-size:8px; font-weight:600; }}
.badge-prep {{ background:#92400e; color:#fbbf24; }}
.badge-cook {{ background:#7f1d1d; color:#fca5a5; }}
.badge-total {{ background:#1e3a5f; color:#93c5fd; }}
.badge-meta {{ background:#1c1917; color:#a8a29e; border:1px solid #44403c; }}

/* Sections */
.section {{ background:#1c1917; border:1px solid #292524; border-radius:8px; padding:16px 20px; margin-bottom:14px; page-break-inside:avoid; }}
.section h2 {{ color:#fbbf24; font-size:13pt; border-bottom:2px solid #44403c; padding-bottom:4px; margin-bottom:10px; }}

/* Ingredients */
.ic {{ padding:5px 8px; color:#fbbf24; font-weight:700; width:24px; text-align:center; font-size:9px; }}
.in {{ padding:5px 8px; font-size:10px; }}
.in b {{ color:#fafaf9; }}
.ia {{ padding:5px 8px; color:#fbbf24; font-weight:600; white-space:nowrap; font-size:10px; }}
.ip {{ padding:5px 8px; color:#78716c; font-size:9px; text-align:right; }}
.dim {{ color:#78716c; font-size:9px; }}
.tip {{ color:#a855f7; font-size:8px; font-style:italic; }}

/* Steps */
.step {{ margin-bottom:12px; page-break-inside:avoid; }}
.step-head {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; flex-wrap:wrap; }}
.step-num {{ background:#92400e; color:#fbbf24; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-weight:800; font-size:12px; flex-shrink:0; }}
.step-title {{ color:#fafaf9; font-weight:700; font-size:11px; }}
.step-time {{ color:#f59e0b; font-size:9px; font-weight:600; }}
.step-temp {{ color:#ef4444; font-size:9px; font-weight:600; }}
.step-action {{ color:#d6d3d1; font-size:10px; line-height:1.6; margin:0 0 4px 34px; }}
.step-box {{ margin-left:34px; padding:5px 10px; border-radius:4px; font-size:9px; margin-bottom:3px; border-left:3px solid; }}
.step-box.visual {{ background:#1a1510; border-color:#fbbf24; color:#fafaf9; }}
.step-box.science {{ background:#0f1520; border-color:#3b82f6; color:#cbd5e1; }}
.step-box.protip {{ background:#150f20; border-color:#a855f7; color:#d4bfff; }}
.step-box.haccp {{ background:#0f1a10; border-color:#22c55e; color:#bbf7d0; }}
.step-box.chef {{ background:#1a1510; border-color:#f59e0b; color:#fde68a; font-style:italic; }}
.step-equip {{ margin-left:34px; color:#78716c; font-size:8px; }}

/* Allergens */
.allergen-grid {{ display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px; }}
.allergen {{ padding:3px 8px; border-radius:4px; font-size:8px; font-weight:600; }}
.allergen.red {{ background:#7f1d1d; color:#fca5a5; }}
.allergen.yellow {{ background:#78350f; color:#fde68a; }}
.allergen.green {{ background:#14532d; color:#bbf7d0; }}
.sub-note {{ font-size:9px; color:#a8a29e; margin:3px 0; }}

/* Cost */
.cost-grid {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:8px; }}
.cost-item {{ background:#292524; padding:8px 14px; border-radius:6px; text-align:center; flex:1; min-width:80px; }}
.cost-label {{ display:block; font-size:7px; color:#78716c; text-transform:uppercase; letter-spacing:1px; }}
.cost-val {{ display:block; font-size:14px; color:#fafaf9; font-weight:800; }}
.cost-val.gold {{ color:#fbbf24; }}

/* Wine */
.wine {{ background:linear-gradient(135deg,#2d1b2e,#1c1917); }}
.wine-name {{ color:#fafaf9; font-size:13px; font-weight:700; }}
.wine-why {{ color:#a8a29e; font-size:10px; margin-top:3px; }}
.wine-bridge {{ color:#e879a0; font-size:9px; font-style:italic; margin-top:3px; }}
.wine-alt {{ color:#78716c; font-size:9px; margin-top:3px; }}

/* Charts */
.chart-md {{ width:260px; display:block; margin:8px auto; border-radius:6px; }}
.chart-sm {{ width:160px; display:block; margin:6px auto; }}

/* Other */
.verdict {{ color:#fafaf9; font-size:11px; text-align:center; margin-top:6px; }}
.fix {{ color:#fbbf24; font-size:10px; text-align:center; }}
.compounds {{ color:#78716c; font-size:9px; text-align:center; font-style:italic; }}
.calories {{ text-align:center; font-size:22px; color:#f59e0b; font-weight:800; margin:4px 0; }}
.flags {{ display:flex; gap:4px; justify-content:center; flex-wrap:wrap; margin-top:6px; }}
.flag {{ background:#292524; padding:2px 8px; border-radius:10px; font-size:8px; color:#a8a29e; }}
.council-note {{ font-size:9px; color:#fbbf24; font-style:italic; margin-top:6px; border-top:1px solid #44403c; padding-top:4px; }}
.mistake {{ background:#292524; padding:6px 10px; border-radius:5px; margin-bottom:3px; font-size:9px; color:#fafaf9; line-height:1.4; }}
.pl-item {{ font-size:10px; margin:3px 0; }}
.pl-label {{ color:#78716c; font-weight:600; }}
.scale-item {{ font-size:9px; color:#d6d3d1; margin:3px 0; }}
.zw-idea {{ font-size:9px; color:#d6d3d1; margin:2px 0; }}
.zw-store {{ font-size:9px; color:#78716c; margin-top:3px; }}
.zw-stock {{ font-size:9px; color:#a8a29e; margin-top:3px; }}
.masterclass {{ background:linear-gradient(135deg,#1a1400,#1c1917); }}
.tech-name {{ color:#fbbf24; font-size:14px; font-weight:800; }}
.tech-exp {{ color:#d6d3d1; font-size:10px; margin-top:4px; }}
.tech-why {{ color:#3b82f6; font-size:9px; margin-top:3px; }}
.tech-tip {{ color:#a855f7; font-size:9px; margin-top:3px; }}

/* Signatures */
.signatures {{ background:linear-gradient(135deg,#1c1917,#0c0a09); border:1px solid #fbbf24; }}
.sig-grid {{ display:flex; flex-wrap:wrap; gap:6px; }}
.sig-card {{ flex:1; min-width:140px; background:#292524; padding:8px; border-radius:6px; }}
.sig-icon {{ font-size:16px; }}
.sig-text {{ font-size:8px; color:#a8a29e; margin-top:2px; }}

/* Wisdom */
.wisdom {{ text-align:center; margin:16px 0; padding:16px; background:linear-gradient(135deg,#1a1208,#1c1917); border-radius:8px; border:1px solid #44403c; }}
.wis-icon {{ font-size:24px; margin-bottom:4px; }}
.wis-text {{ color:#fbbf24; font-size:11px; font-style:italic; line-height:1.6; }}

/* Footer */
.footer {{ text-align:center; padding:10px 0; border-top:1px solid #44403c; margin-top:14px; }}
.footer .fb {{ font-size:8px; color:#f59e0b; letter-spacing:1px; }}
.footer .fd {{ font-size:7px; color:#555; margin-top:2px; }}
.metrics {{ text-align:center; padding:6px; background:#292524; border-radius:4px; font-size:8px; color:#78716c; margin-top:8px; }}
</style></head><body>

<div class="header">
<p class="brand">AetherLang Vision Chef v4 — Culinary Council</p>
<h1>{name}</h1>"""

    if name_en and name_en != name:
        page += f'<p class="sub">{name_en}</p>'
    if cuisine:
        page += f'<p class="sub">{cuisine}</p>'
    page += '<div class="badges">'
    if prep:
        page += f'<span class="badge badge-prep">🔪 {prep}min prep</span>'
    if cook:
        page += f'<span class="badge badge-cook">🔥 {cook}min cook</span>'
    if total_t:
        page += f'<span class="badge badge-total">⏱ {total_t}min total</span>'
    page += f'<span class="badge badge-meta">📊 {diff}</span>'
    page += f'<span class="badge badge-meta">🍽 {svgs} servings</span>'
    if cost_data.get("suggested_menu_price_eur"):
        page += f'<span class="badge badge-meta">💶 €{cost_data["suggested_menu_price_eur"]}</span>'
    page += '</div>'
    if desc:
        page += f'<p class="desc">{desc}</p>'
    page += f'<p style="font-size:7px;color:#555;margin-top:6px">{now}</p></div>'

    page += f'<div class="section"><h2>🧾 Ingredients</h2><table>{ing_rows}</table></div>'
    page += f'<div class="section"><h2>👨‍🍳 Steps ({len(recipe.get("steps", []))})</h2>{steps_html}</div>'
    page += mac_html + wine_html + nutr_html + cost_html
    page += allergen_html + tech_html + mist_html + pl_html
    page += scale_html + culture_html + zw_html + sig_html + wis_html

    page += f'<div class="footer"><p class="fb">AetherLang Vision Chef v4.0 — 6-Member Culinary Council</p>'
    page += f'<p class="fd">Generated by NeuroAether APEX Platform • {now}</p>{met_html}</div></body></html>'

    # ── Render ──
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    raw = output_path + ".raw.pdf"
    page = _strip_emojis(page)
    WeasyHTML(string=page).write_pdf(raw)

    try:
        subprocess.run([
            "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/prepress", "-dNOPAUSE", "-dBATCH", "-dQUIET",
            f"-sOutputFile={output_path}", raw
        ], check=True, timeout=30)
        os.remove(raw)
    except (subprocess.CalledProcessError, FileNotFoundError):
        if os.path.exists(raw):
            os.rename(raw, output_path)

    log.info(f"Recipe PDF: {output_path} ({os.path.getsize(output_path)} bytes)")
    return output_path


# ═══════════════════════════════════════════════════════════════
#  6. TELEGRAM FORMATTER
# ═══════════════════════════════════════════════════════════════

def format_vision_telegram(recipe: dict, metrics: dict, pdf_sent: bool = False) -> str:
    """Compact Telegram HTML summary — full details in PDF"""
    def e(t):
        if t is None:
            return ""
        return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    p = []
    name = recipe.get("dish_name_greek") or recipe.get("recipe_name") or "Recipe"
    p.append(f"🧑‍🍳 <b>{e(name)}</b>")
    if recipe.get("recipe_name") and recipe.get("dish_name_greek"):
        p.append(f"<i>{e(recipe['recipe_name'])}</i>")
    if recipe.get("description"):
        d = recipe["description"]
        p.append(f"\n{e(d[:250])}{'...' if len(d) > 250 else ''}")

    meta = []
    if recipe.get("total_time_minutes"):
        meta.append(f"⏱ {recipe['total_time_minutes']}min")
    if recipe.get("difficulty"):
        meta.append(f"📊 {recipe['difficulty']}")
    if recipe.get("servings"):
        meta.append(f"🍽 {recipe['servings']}")
    cost_data = recipe.get("cost_analysis", {})
    if cost_data.get("suggested_menu_price_eur"):
        meta.append(f"💶 €{cost_data['suggested_menu_price_eur']}")
    if meta:
        p.append(" | ".join(meta))

    # ALL Ingredients
    ings = recipe.get("ingredients", [])
    if ings:
        p.append("\n<b>🧾 Ingredients / Υλικά:</b>")
        for ing in ings:
            if isinstance(ing, dict):
                n = ing.get('name', '')
                ne = ing.get('name_english', '')
                amt = ing.get('amount', '')
                prep = ing.get('preparation', '')
                line = f"  • <b>{e(n)}</b>"
                if ne:
                    line += f" ({e(ne)})"
                line += f" — {e(amt)}"
                if prep:
                    line += f" | {e(prep)}"
                p.append(line)

    # ALL Steps with FULL detail
    steps = recipe.get("steps", [])
    if steps:
        p.append(f"\n<b>👨‍🍳 {len(steps)} Steps:</b>")
        for s in steps:
            title = s.get("title") or s.get("technique", "")
            tim = f" ⏱ {e(s['timing'])}" if s.get('timing') else ""
            temp = f" 🌡 {e(s['temperature'])}" if s.get('temperature') else ""
            p.append(f"\n<b>{s.get('step_number', '')}. {e(title)}</b>{tim}{temp}")
            if s.get("action"):
                p.append(f"{e(s['action'])}")
            if s.get("visual_cue"):
                p.append(f"👁 {e(s['visual_cue'])}")
            if s.get("pro_tip"):
                p.append(f"💡 {e(s['pro_tip'])}")
            if s.get("equipment"):
                eq = s["equipment"]
                if isinstance(eq, list):
                    eq = ", ".join(eq)
                p.append(f"🍳 {e(str(eq))}")

    # Wine
    w = recipe.get("wine_pairing", {})
    primary = w.get("primary", w) if isinstance(w.get("primary"), dict) else w
    wine_name = primary.get("wine", w.get("recommended", ""))
    if wine_name:
        p.append(f"\n🍷 <b>Wine:</b> {e(wine_name)}")

    # MacYuFBI
    mac = recipe.get("mac_yu_fbi", {})
    if mac and mac.get("balance_verdict"):
        p.append(f"\n🎯 {e(mac['balance_verdict'])}")

    # Allergens
    allergens = recipe.get("allergen_matrix", {})
    if allergens and allergens.get("contains"):
        p.append(f"\n⚠️ <b>Allergens:</b> {', '.join(allergens['contains'])}")

    # Wisdom
    cw = recipe.get("chef_wisdom", "")
    if cw:
        p.append(f'\n<i>👨‍🍳 "{e(cw[:120])}{"..." if len(cw) > 120 else ""}"</i>')

    if pdf_sent:
        p.append("\n📄 <b>Full recipe + charts + council analysis → PDF ☝️</b>")

    # Council badge
    p.append("\n🏛️ <i>Reviewed by 6-Member Culinary Council</i>")

    # Metrics
    m = metrics or {}
    if m.get("total_seconds"):
        p.append(f"\n<code>v{m.get('pipeline_version', '4.0')} | {m['total_seconds']}s | {m.get('total_tokens', '?')} tok</code>")

    return "\n".join(p)
