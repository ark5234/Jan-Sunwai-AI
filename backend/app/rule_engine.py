"""
Deterministic Rule Engine for Civic Complaint Classification.

Replaces heavy reliance on small reasoning LLMs (1B) with a fast,
VRAM-free Python rule engine. Designed for 4 GB GPU (RTX 3050) local
deployment where every MB of VRAM matters.

Pipeline:
    Vision JSON → Rule Engine → Category  (no LLM needed for clear cases)
    Vision JSON → Rule Engine → AMBIGUOUS → optional LLM reasoning

The rule engine scores EVERY category and picks the highest. If the
winning score is below a threshold, it flags the result as ambiguous
so the caller can optionally invoke a reasoning model.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from app.category_utils import CANONICAL_CATEGORIES


# ═══════════════════════════════════════════════════════════════════
# WEIGHTED KEYWORD RULES
# Each rule: (keywords, weight)
# Higher weight = stronger signal. Rules are scored additively.
# ═══════════════════════════════════════════════════════════════════

_CATEGORY_RULES: Dict[str, List[Tuple[List[str], float]]] = {
    "Municipal - PWD (Roads)": [
        (["pothole", "potholes"], 3.0),
        (["pothole-filled"], 3.5),
        (["road damage", "damaged road", "broken road", "cracked road"], 3.0),
        (["damaged pavement", "broken pavement", "cracked pavement"], 2.5),
        (["footpath damage", "broken footpath", "damaged footpath"], 2.5),
        (["manhole", "manhole cover"], 2.0),
        (["road crack", "road surface"], 2.0),
        (["bridge damage", "damaged bridge"], 2.0),
        (["puddle", "puddles", "water on road", "water on the road"], 1.5),
        (["asphalt", "tar road", "concrete road"], 1.0),
        # NOTE: generic terms like 'road'/'street'/'lane' intentionally removed —
        # they fire on every road photo and unfairly inflate PWD Roads score.
    ],
    "Municipal - Sanitation": [
        (["garbage", "trash", "rubbish", "refuse"], 3.0),
        (["waste pile", "waste dump", "waste heap"], 3.0),
        (["overflowing bin", "overflowing trash", "overflowing garbage"], 3.0),
        (["litter", "littered", "littering"], 2.5),
        (["dump", "dumped", "dumping"], 2.0),
        (["dirty toilet", "filthy toilet", "unclean toilet"], 2.5),
        (["debris", "scattered waste"], 1.5),
        (["stench", "foul smell", "unhygienic"], 1.0),
        # Extra patterns the vision model produces for unsorted waste scenes
        (["pile of", "large pile", "heap of"], 2.5),
        (["plastic bottles", "plastic bottle", "glass bottles", "broken glass",
          "broken bottles", "empty bottles"], 2.5),
        (["scattered", "scattered items", "scattered objects", "scattered garbage"], 2.0),
        (["junk", "clutter", "mess", "filth", "filthy"], 1.5),
        (["waste on", "waste near", "waste around", "waste along"], 2.0),
        (["open dump", "roadside dump", "illegal dump"], 3.0),
        (["waste management", "garbage collection", "garbage clearance"], 1.5),
    ],
    "Municipal - Horticulture": [
        (["fallen tree", "uprooted tree", "collapsed tree"], 3.0),
        (["overgrown", "unmaintained park", "neglected park"], 2.5),
        (["dead plant", "dead plants", "dry plants", "withered"], 2.5),
        (["broken branch", "tree branch", "branches blocking"], 2.0),
        (["tree blocking road", "tree fell", "tree on road"], 3.0),
        (["garden", "park", "greenery", "vegetation"], 0.5),
    ],
    "Municipal - Street Lighting": [
        (["street light", "streetlight", "street lamp"], 3.0),
        (["lamp post", "lamppost", "light pole"], 3.0),
        (["broken light", "non-functional light", "damaged light"], 2.5),
        (["unlit road", "dark road", "dark street", "no lighting"], 2.5),
        (["bulb", "illumination"], 0.5),
    ],
    "Municipal - Water & Sewerage": [
        (["waterlogging", "waterlogged", "water logging"], 3.0),
        (["flooded", "flooding", "flood"], 3.0),
        (["drain overflow", "overflowing drain", "blocked drain"], 3.0),
        (["sewer overflow", "sewer leak", "sewage"], 3.0),
        (["pipe leak", "water leak", "leaking pipe", "burst pipe"], 2.5),
        (["stagnant water", "standing water", "water pooling"], 2.5),
        (["drainage problem", "drainage issue", "clogged drain"], 2.0),
        (["water gushing", "water spraying"], 2.0),
    ],
    "Utility - Power (DISCOM)": [
        (["dangling wire", "hanging wire", "loose wire", "fallen wire"], 3.0),
        (["open transformer", "damaged transformer", "leaking transformer"], 3.0),
        (["fallen electric pole", "tilted pole", "broken pole"], 3.0),
        (["exposed wire", "bare wire", "naked cable"], 2.5),
        (["power cable", "electric cable", "power line"], 2.0),
        (["sparking", "electrical hazard", "electrocution risk"], 2.5),
        (["transformer", "electric pole", "utility pole"], 1.5),
    ],
    "Pollution Control Board": [
        (["air pollution", "smoke emission", "thick smoke"], 3.0),
        (["industrial waste", "factory waste", "effluent"], 3.0),
        (["open burning", "burning garbage", "burning waste"], 3.0),
        (["chemical dump", "toxic waste", "hazardous waste"], 3.0),
        (["pollution", "polluted", "contaminated"], 2.0),
        (["smoke", "smog", "haze"], 1.5),
    ],
    "Police - Traffic": [
        (["traffic signal", "signal failure", "broken signal", "failed signal"], 3.5),
        (["traffic deadlock", "deadlock", "standstill", "bumper to bumper", "bumper-to-bumper"], 3.5),
        (["traffic jam"], 3.0),
        # 'traffic congestion' alone is insufficient — a packed platform or crowded
        # market is also 'congested'. Score is low; rises only when vehicle keywords appear.
        (["traffic congestion", "heavily congested", "severe congestion"], 1.5),
        (["congestion"], 0.8),
        (["gridlock", "chaotic traffic", "traffic chaos", "disorganized traffic", "mismanagement"], 3.0),
        (["road blockage", "road blocked", "road obstruction"], 2.5),
        (["peak hour", "peak office", "rush hour", "office hour", "rush-hour"], 2.5),
        (["no lane", "lane violation", "wrong side driving", "no traffic lane", "no proper lane"], 2.5),
        (["vehicles blocking", "vehicles crowding", "crowded road", "crowded street"], 2.5),
        (["uncontrolled traffic", "no signal", "traffic police", "traffic management"], 2.0),
        (["marketplace congestion", "market area", "congested market"], 1.5),
        # Vehicle corroboration: without at least one of these, 'congestion' alone is ambiguous
        (["car", "cars", "vehicle", "vehicles", "bus", "buses", "truck", "trucks",
          "motorcycle", "motorcycles", "auto", "autorickshaw", "rickshaw", "two-wheeler",
          "scooter", "cab", "taxi"], 2.0),
        (["multiple vehicles", "many vehicles", "heavy vehicles"], 0.5),
    ],
    "Police - Local Law Enforcement": [
        (["illegal parking", "wrong parking", "no parking zone"], 3.0),
        (["encroachment", "footpath encroachment", "pavement encroachment"], 3.0),
        (["public nuisance", "disturbance", "rowdy"], 2.5),
        (["footpath blocked", "path blocked", "walkway blocked"], 2.0),
        (["unauthorized", "illegal occupation", "hawker"], 1.5),
    ],
    "State Transport": [
        (["bus shelter", "bus stop", "damaged bus stop"], 3.0),
        (["state bus", "broken bus", "damaged bus"], 3.0),
        (["transport terminal", "bus terminal", "bus depot"], 2.5),
    ],
}

# Negative signals: if these appear, suppress civic categories
_NON_CIVIC_KEYWORDS = [
    "selfie", "portrait", "food", "meal", "restaurant", "cartoon", "anime",
    "gaming", "screenshot", "indoor furniture", "appliance", "pet", "animal",
    "beautiful landscape", "clear sky", "family photo", "group photo",
    # Indian Railways is Central Government — outside this portal's scope
    "railway station", "train station", "railway platform", "train platform",
    "railway track", "train track", "metro station",
]


def _score_text(text: str, rules: List[Tuple[List[str], float]]) -> float:
    """Score text against a set of weighted keyword rules."""
    text_lower = text.lower()
    score = 0.0
    for keywords, weight in rules:
        if any(kw in text_lower for kw in keywords):
            score += weight
    return score


def _first_mention_position(text: str, keywords: List[str]) -> int:
    """Return the earliest character position of any keyword, or -1 if none found."""
    text_lower = text.lower()
    best = -1
    for kw in keywords:
        pos = text_lower.find(kw)
        if pos != -1 and (best == -1 or pos < best):
            best = pos
    return best


def classify_by_rules(
    vision_payload: Dict[str, Any],
    ambiguity_threshold: float = 2.0,
    confidence_gap_threshold: float = 1.0,
) -> Dict[str, Any]:
    """
    Deterministic rule-based classification from structured vision output.

    Args:
        vision_payload: Dict with keys like 'description', 'visible_objects',
                       'primary_issue', 'secondary_issue', 'hazards'.
                       Also accepts raw text string in 'description'.
        ambiguity_threshold: Minimum top score to consider result confident.
        confidence_gap_threshold: Minimum gap between #1 and #2 score.

    Returns:
        dict with:
            category:    best matching canonical category
            confidence:  float 0.0–1.0 (derived from rule scores)
            is_ambiguous: True if reasoning model should be consulted
            scores:      dict of all category scores (for debugging)
            method:      'rule_engine'
    """
    # Build combined text from all available fields
    desc = str(vision_payload.get("description", ""))
    objects = " ".join(vision_payload.get("visible_objects", []))
    primary = str(vision_payload.get("primary_issue", ""))
    secondary = str(vision_payload.get("secondary_issue", ""))
    hazards = " ".join(vision_payload.get("hazards", []))
    # Background text: description + visible objects + secondary issue
    background = f"{desc} {objects} {secondary}"
    # High-signal text: primary_issue + hazards (vision model's most direct assertion)
    high_signal = f"{primary} {hazards}"

    # Check for non-civic content first
    combined = f"{background} {high_signal}"
    combined_lower = combined.lower()
    if any(kw in combined_lower for kw in _NON_CIVIC_KEYWORDS):
        return {
            "category": "Uncategorized",
            "confidence": 0.85,
            "is_ambiguous": False,
            "scores": {},
            "method": "rule_engine_non_civic",
        }

    # Score every category:
    # - background text scored at 1× (incidental mentions in description)
    # - primary_issue + hazards scored at 3× (vision model's direct assertion)
    # This prevents background observations ("road", "street") from drowning
    # out the model's explicit primary classification signal.
    scores: Dict[str, float] = {}
    for category, rules in _CATEGORY_RULES.items():
        bg_score = _score_text(background, rules)
        hs_score = _score_text(high_signal, rules)
        scores[category] = bg_score + (hs_score * 3.0)

    # ── First-mention boost ────────────────────────────────────────
    # When the description mentions keywords from multiple categories,
    # boost the category whose keywords appear FIRST in the text.
    # This approximates "primary issue" for plain-text descriptions
    # (e.g. moondream) where primary_issue field is empty.
    # Only apply when the gap between top-2 is small (≤ 2.0).
    combined = f"{background} {high_signal}"  # rebuild for first-mention scan
    desc_lower = combined.lower()
    _ALL_CATEGORY_SIGNALS: Dict[str, List[str]] = {
        cat: [kw for kws, _w in rules for kw in kws if _w >= 2.0]
        for cat, rules in _CATEGORY_RULES.items()
    }
    first_positions = {}
    for cat, kws in _ALL_CATEGORY_SIGNALS.items():
        pos = _first_mention_position(desc_lower, kws)
        if pos >= 0:
            first_positions[cat] = pos

    ranked_raw = sorted(scores.items(), key=lambda x: -x[1])
    if len(ranked_raw) >= 2:
        top_cat, top_sc = ranked_raw[0]
        run_cat, run_sc = ranked_raw[1]
        # If both categories have signals and gap is small, boost the one mentioned first
        if (top_sc - run_sc) <= 2.0 and top_cat in first_positions and run_cat in first_positions:
            if first_positions[run_cat] < first_positions[top_cat]:
                # Runner-up's keywords appear first → boost it
                scores[run_cat] += 2.0
                print(f"[rule_engine] first-mention boost: {run_cat} "
                      f"(pos {first_positions[run_cat]}) over {top_cat} "
                      f"(pos {first_positions[top_cat]})")

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    top_category, top_score = ranked[0] if ranked else ("Uncategorized", 0.0)
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0

    # Determine ambiguity
    gap = top_score - runner_up_score
    is_ambiguous = (top_score < ambiguity_threshold) or (gap < confidence_gap_threshold)

    if top_score <= 0.0:
        return {
            "category": "Uncategorized",
            "confidence": 0.1,
            "is_ambiguous": True,
            "scores": scores,
            "method": "rule_engine_no_match",
        }

    # Convert score to 0.0–1.0 confidence
    # Max plausible score is ~9.0 (3 rules * 3.0 weight each)
    raw_confidence = min(top_score / 6.0, 1.0)
    # Reduce confidence if gap is small (ambiguous)
    if gap < confidence_gap_threshold and len(ranked) > 1:
        raw_confidence *= 0.7

    return {
        "category": top_category,
        "confidence": round(raw_confidence, 3),
        "is_ambiguous": is_ambiguous,
        "scores": scores,
        "method": "rule_engine",
    }


def parse_vision_text_to_payload(text: str) -> Dict[str, Any]:
    """
    Convert a plain-text vision description (non-JSON) into a payload
    dict that the rule engine can process.
    """
    return {
        "description": text,
        "visible_objects": [],
        "primary_issue": "",
        "secondary_issue": "",
        "hazards": [],
    }
