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
from typing import Any
from app.category_utils import CANONICAL_CATEGORIES


# ═══════════════════════════════════════════════════════════════════
# WEIGHTED KEYWORD RULES
# Each rule: (keywords, weight)
# Higher weight = stronger signal. Rules are scored additively.
# ═══════════════════════════════════════════════════════════════════

_CATEGORY_RULES: dict[str, list[tuple[list[str], float]]] = {
    "Health Department": [
        (["garbage", "trash", "rubbish", "refuse", "plastic waste", "plastic bags", "debris", "sweeping"], 3.0),
        (["waste pile", "waste dump", "waste heap", "open dump", "illegal dump"], 3.0),
        (["overflowing bin", "overflowing trash", "overflowing garbage", "spilled garbage"], 3.0),
        (["litter", "littered", "littering", "scattered waste"], 2.5),
        (["filthy toilet", "unclean toilet", "public urination", "open defecation", "spitting"], 2.5),
        (["stench", "foul smell", "unhygienic", "rotten"], 1.5),
        (["dead animal", "carcass", "dead dog"], 3.0),
        (["medical waste", "hospital waste", "bio hazard"], 3.0),
        (["pollution", "chemical dump", "toxic waste"], 2.5),
    ],
    "Civil Department": [
        (["pothole", "potholes", "pothole-filled", "crater", "visible potholes"], 3.0),
        (["road damage", "damaged road", "broken road", "cracked road", "uneven road", "dirt road", "peeling asphalt", "bad road condition", "rubble"], 3.0),
        (["damaged pavement", "broken pavement", "cracked pavement", "pavement damage", "road surface", "uneven surface", "road with fallen leaves"], 2.5),
        (["footpath damage", "broken footpath", "damaged footpath"], 2.5),
        (["waterlogging", "waterlogged", "water logging", "puddles", "stagnant water on road"], 3.0),
        (["flooded", "flooding", "flood"], 3.0),
        (["drain overflow", "overflowing drain", "blocked drain", "dirty drain"], 3.0),
        (["sewer overflow", "sewer leak", "sewage"], 3.0),
        (["pipe leak", "water leak", "leaking pipe", "burst pipe"], 2.5),
        (["manhole", "manhole cover", "missing cover", "caved in", "sinkhole"], 2.0),
        (["bridge damage", "damaged bridge", "crack in bridge"], 2.0),
        # Sand / mud / unpaved road surface issues
        (["wet sand", "muddy road", "muddy path", "sandy road", "sand on road", "sand on roadside",
          "sand on the road", "sand on the roadside", "gravel road", "unpaved road",
                    "mud on road", "slushy road", "slush", "waterlogged road",
                    "wet road", "sand and mud", "mud and sand", "sandy mud", "muddy surface",
                    "slippery road", "slippery surface", "road is slippery"], 3.0),
        (["road construction", "road repair", "road digging", "road dug up", "construction debris on road"], 2.5),
    ],
    "Horticulture": [
        (["fallen tree", "uprooted tree", "collapsed tree", "uprooted"], 3.0),
        (["overgrown", "unmaintained park", "neglected park", "overgrown weeds"], 2.5),
        (["dead plant", "dead plants", "dry plants", "withered", "fallen leaves", "dry leaves", "leaves scattered"], 2.5),
        (["broken branch", "tree branch", "branches blocking"], 2.0),
        (["tree blocking road", "tree fell", "tree on road"], 3.0),
        (["garden", "park", "greenery", "vegetation", "weed"], 0.5),
    ],
    "Electrical Department": [
        (["street light", "streetlight", "street lamp", "lamp post", "lamppost"], 3.0),
        (["broken light", "non-functional light", "damaged light"], 2.5),
        (["unlit road", "dark road", "dark street", "no lighting"], 2.5),
        (["dangling wire", "hanging wire", "loose wire", "fallen wire", "electrical wire"], 3.0),
        (["open transformer", "damaged transformer", "leaking transformer", "electrical box", "fuse box", "circuit breaker", "meter box", "distribution panel"], 3.0),
        (["short circuit", "electrical fire", "panel fire", "transformer fire", "electrical overload", "burning wire", "burning cable", "sparking wire"], 3.5),
        (["fallen electric pole", "tilted pole", "broken pole"], 3.0),
        (["exposed wire", "bare wire", "naked cable", "sparking", "live wire", "high voltage", "electrocut"], 2.5),
        (["transformer", "electric pole", "utility pole", "electrical panel"], 1.5),
    ],
    "IT Department": [
        (["app bug", "portal bug", "website down", "app down"], 3.0),
        (["login issue", "server error", "database error", "portal crash", "login failed"], 3.0),
    ],
    "Commercial": [
        (["faulty meter", "broken meter", "meter reading"], 3.0),
        (["billing issue", "wrong bill", "excessive bill", "property tax", "license renewal"], 3.0),
    ],
    "Enforcement": [
        (["illegal parking", "wrong parking", "no parking zone"], 3.0),
        (["encroachment", "footpath encroachment", "pavement encroachment", "commercial encroachment"], 3.0),
        (["illegal occupation", "hawker", "unauthorized vendor", "squatter"], 2.5),
        (["traffic deadlock", "deadlock", "standstill"], 3.5),
        (["traffic jam", "traffic congestion", "gridlock", "chaotic traffic", "severe accident", "heavy traffic"], 3.0),
        (["road blockage", "road blocked", "road obstruction"], 2.5),
        (["lane violation", "wrong side driving"], 2.5),
        (["unauthorized", "public nuisance", "illegal hoarding"], 2.0),
    ],
    "VBD Department": [
        (["mosquitoes", "mosquito breeding", "mosquito larvae", "larvae"], 3.0),
        (["stagnant water", "standing water", "water pooling"], 2.5),
        (["dengue", "malaria", "fogging required", "fumigation", "mosquito net"], 3.0),
    ],
    "EBR Department": [
        (["illegal construction", "unauthorized construction", "building violation"], 3.0),
        (["building collapse", "unsafe building", "dangerous structure"], 3.0),
    ],
    "Fire Department": [
        (["fire", "burning", "flames", "smoke emission", "thick smoke", "smoke billow"], 3.0),
        (["fire hazard", "flammable", "explosive", "gas leak"], 3.0),
    ]
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


def _score_text(text: str, rules: list[tuple[list[str], float]]) -> float:
    """Score text against a set of weighted keyword rules."""
    text_lower = text.lower()
    score = 0.0
    for keywords, weight in rules:
        if any(kw in text_lower for kw in keywords):
            score += weight
    return score


def _first_mention_position(text: str, keywords: list[str]) -> int:
    """Return the earliest character position of any keyword, or -1 if none found."""
    text_lower = text.lower()
    best = -1
    for kw in keywords:
        pos = text_lower.find(kw)
        if pos != -1 and (best == -1 or pos < best):
            best = pos
    return best


def classify_by_rules(
    vision_payload: dict[str, Any],
    ambiguity_threshold: float = 2.0,
    confidence_gap_threshold: float = 1.0,
) -> dict[str, Any]:
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
    scores: dict[str, float] = {}
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
    _ALL_CATEGORY_SIGNALS: dict[str, list[str]] = {
        cat: [kw for kws, _w in rules for kw in kws if _w >= 2.0]
        for cat, rules in _CATEGORY_RULES.items()
    }
    first_positions: dict[str, int] = {}
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


def parse_vision_text_to_payload(text: str) -> dict[str, Any]:
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
