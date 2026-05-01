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
        (["garbage", "trash", "rubbish", "refuse", "plastic waste", "plastic bags", "sweeping"], 3.0),
        (["debris"], 2.0),
        (["waste pile", "waste dump", "waste heap", "open dump", "illegal dump"], 3.0),
        (["overflowing bin", "overflowing trash", "overflowing garbage", "spilled garbage"], 3.0),
        (["dustbin", "trash bin", "garbage bin", "overturned bin", "tipped bin", "spilled trash"], 3.0),
        (["litter", "littered", "littering", "scattered waste"], 2.5),
        (["filthy toilet", "unclean toilet", "public urination", "open defecation", "spitting"], 2.5),
        (["stench", "foul smell", "unhygienic", "rotten"], 1.5),
        (["dead animal", "carcass", "dead dog"], 3.0),
        (["medical waste", "hospital waste", "bio hazard"], 3.0),
        (["pollution", "chemical dump", "toxic waste"], 2.5),
    ],
    "Civil Department": [
        (["pothole", "potholes", "pothole-filled", "crater", "visible potholes", "road depression", "sinkage", "road sink", "caved in", "sinkhole"], 3.0),
        (["road damage", "damaged road", "broken road", "cracked road", "uneven road", "dirt road", "peeling asphalt", "bad road condition", "rubble", "cracked surface", "uneven surface"], 3.0),
        (["damaged pavement", "broken pavement", "cracked pavement", "pavement damage", "road surface", "uneven surface", "road with fallen leaves"], 2.5),
        (["footpath damage", "broken footpath", "damaged footpath"], 2.5),
        (["waterlogging", "waterlogged", "water logging", "puddles", "stagnant water on road", "flooded", "flooding", "flood"], 3.0),
        (["drain overflow", "overflowing drain", "blocked drain", "dirty drain"], 3.0),
        (["sewer overflow", "sewer leak", "sewage"], 3.0),
        (["pipe leak", "water leak", "leaking pipe", "burst pipe", "broken water pipe", "water gushing"], 3.0),
        (["manhole", "manhole cover", "missing cover"], 2.0),
        (["bridge damage", "damaged bridge", "crack in bridge"], 2.0),
        # Sand / mud / unpaved road surface issues
        (["wet sand", "muddy road", "muddy path", "sandy road", "sand on road", "sand on roadside",
          "sand on the road", "sand on the roadside", "gravel road", "unpaved road",
                    "mud on road", "slushy road", "slush", "waterlogged road",
                    "wet road", "sand and mud", "mud and sand", "sandy mud", "muddy surface",
                    "slippery road", "slippery surface", "road is slippery"], 3.0),
        (["road construction", "road repair", "road digging", "road dug up", "construction debris on road", "rebar", "iron rod", "steel rod", "cement bag", "construction material", "construction waste"], 3.0),
    ],
    "Horticulture": [
        (["overgrown", "unmaintained park", "neglected park", "overgrown weeds", "fallen leaves", "dry leaves", "leaves scattered", "leaf litter", "leaf debris", "leaves", "leaf", "pile of grass", "dry grass", "vegetation pile", "vegetation debris", "garden waste"], 3.0),
        (["dead plant", "dead plants", "dry plants", "withered"], 2.5),
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

# Hard non-civic signals: always suppress civic categories.
_HARD_NON_CIVIC_KEYWORDS = [
    # Indian Railways is Central Government — outside this portal's scope
    "railway station", "train station", "railway platform", "train platform",
    "railway track", "train track", "metro station",
]

# Soft non-civic signals: suppress only if no civic context appears.
_SOFT_NON_CIVIC_KEYWORDS = [
    "selfie", "portrait", "food", "meal", "restaurant", "cartoon", "anime",
    "gaming", "screenshot", "indoor furniture", "appliance", "pet", "animal",
    "beautiful landscape", "clear sky", "family photo", "group photo",
]

_CIVIC_CONTEXT_KEYWORDS = [
    "garbage", "trash", "waste", "litter", "dump", "rubbish", "dustbin", "overflowing bin",
    "pothole", "road damage", "broken road", "cracked road", "waterlogging", "blocked drain",
    "street light", "dangling wire", "exposed wire", "transformer", "electrical box",
    "illegal parking", "encroachment", "mosquito", "larvae", "fogging", "illegal construction",
    "building collapse", "fire hazard", "industrial waste", "chemical dump", "burning wire",
]

_LEAF_DOMINANT_TERMS = [
    "fallen leaves", "dry leaves", "leaves scattered", "leaf litter", "leaf debris",
    "leaves", "leaf",
]

# Unambiguous sanitation cues that should always provide a strong counter-signal to leaves.
_HARD_SANITATION_TERMS = [
    "dump", "dustbin", "bin", "plastic", "bottle", "dead animal", "carcass",
    "medical waste", "hospital waste", "bio hazard", "stench", "foul smell",
    "filthy", "open defecation", "toxic waste", "waste bags", "trash bags",
]

# Generic terms that vision models often use for any scattered material.
# We treat these as "weak" when "leaves" + "park" context is present.
_GENERIC_SANITATION_TERMS = ["garbage", "trash", "waste", "rubbish"]

_STRONG_SANITATION_TERMS = _HARD_SANITATION_TERMS + _GENERIC_SANITATION_TERMS


def _has_civic_context(text_lower: str) -> bool:
    return any(kw in text_lower for kw in _CIVIC_CONTEXT_KEYWORDS)


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
    has_hard_non_civic = any(kw in combined_lower for kw in _HARD_NON_CIVIC_KEYWORDS)
    has_soft_non_civic = any(kw in combined_lower for kw in _SOFT_NON_CIVIC_KEYWORDS)
    if has_hard_non_civic or (has_soft_non_civic and not _has_civic_context(combined_lower)):
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

    # Leaf-litter scenes are usually horticulture unless there are clear
    # sanitation cues (garbage/trash/bin/plastic/etc.).
    has_leaf_dominant = any(term in combined_lower for term in _LEAF_DOMINANT_TERMS)
    has_hard_sanitation = any(term in combined_lower for term in _HARD_SANITATION_TERMS)
    has_generic_sanitation = any(term in combined_lower for term in _GENERIC_SANITATION_TERMS)
    
    # Horticulture issues (like leaves) often occur on sidewalks, footpaths, and roadsides, 
    # not just inside parks. We include these in the 'friendly context'.
    leaf_friendly_terms = ["park", "garden", "greenery", "vegetation", "sidewalk", "footpath", "roadside", "pavement", "curb"]
    has_leaf_friendly_context = any(term in combined_lower for term in leaf_friendly_terms)

    # Allow generic "garbage" mentions to be suppressed if we are in a leaf-friendly location,
    # as long as no HARD sanitation cues (bins, bags, dead animals) are present.
    has_blocking_sanitation = has_hard_sanitation or (has_generic_sanitation and not has_leaf_friendly_context)

    if has_leaf_dominant and not has_blocking_sanitation:
        # Stronger preference if it's explicitly a park/garden
        is_explicit_park = any(term in combined_lower for term in ["park", "garden", "greenery"])
        penalty = 0.25 if not is_explicit_park else 0.1
        boost = 2.5 if not is_explicit_park else 4.0
        scores["Health Department"] = scores.get("Health Department", 0.0) * penalty
        scores["Horticulture"] = scores.get("Horticulture", 0.0) + boost

    # ── VBD vs. Civil: Source-over-Symptom ─────────────────────────────
    # If a road depression, pipe leak, or sinkage is present, stagnant water 
    # is a symptom of infrastructure failure. Prioritize Civil Department.
    has_infrastructure_failure = any(term in combined_lower for term in [
        "pothole", "potholes", "road damage", "damaged road", "broken road", 
        "road depression", "sinkage", "road sink", "pipe leak", "leaking pipe", 
        "broken water pipe", "burst pipe", "caved in", "sinkhole"
    ])
    has_stagnant_water = any(term in combined_lower for term in ["stagnant water", "standing water", "water pooling", "waterlog"])
    
    if has_infrastructure_failure and has_stagnant_water:
        scores["VBD Department"] = scores.get("VBD Department", 0.0) * 0.2
        scores["Civil Department"] = scores.get("Civil Department", 0.0) + 2.0

    # ── Civil vs. Horticulture: Infrastructure-over-Landscape ──────────
    # Sand, dust accumulation, construction materials, or pavement damage
    # on a sidewalk/roadside is a Civil issue, even if a few leaves are present.
    has_sand_or_dust = any(term in combined_lower for term in [
        "sand on road", "sand on roadside", "dust accumulation", "sandy", "dusty", "gravel", "silt", "gravel road", "unpaved road"
    ])
    has_construction_materials = any(term in combined_lower for term in [
        "road construction", "road repair", "road digging", "road dug up", 
        "construction debris on road", "rebar", "iron rod", "steel rod", 
        "cement bag", "construction material", "construction waste", "metal pipe"
    ])
    has_sidewalk_pavement = any(term in combined_lower for term in ["sidewalk", "pavement", "footpath", "curb"])
    
    if (has_sand_or_dust or has_infrastructure_failure or has_construction_materials) and has_leaf_dominant:
        # If it's a sidewalk/road with sand/damage/construction, suppress the Horticulture signal
        # unless it's an explicit park/garden (and no construction materials are involved).
        is_explicit_park = any(term in combined_lower for term in ["park", "garden", "greenery"])
        if not is_explicit_park or has_construction_materials:
            scores["Horticulture"] = scores.get("Horticulture", 0.0) * 0.4
            scores["Civil Department"] = scores.get("Civil Department", 0.0) + 2.5
            print(f"[rule_engine] prioritizing Civil over Horticulture for roadside sand/damage/construction")

    # ── Enforcement vs. Civil: Activity-over-Infrastructure ────────────────
    # Active management of vendors/parking usually takes priority over
    # minor pavement damage in encroachment scenes.
    has_encroachment = any(term in combined_lower for term in ["hawker", "vendor", "illegal parking", "encroachment"])
    if has_encroachment and scores.get("Civil Department", 0.0) < 4.0:
        scores["Enforcement"] = scores.get("Enforcement", 0.0) + 1.5
        scores["Civil Department"] = scores.get("Civil Department", 0.0) * 0.5

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

    # Tie-breaker for leaf-heavy walkway scenes: if sanitation evidence is weak,
    # prefer Horticulture over Health when both are near each other.
    if has_leaf_dominant and not has_blocking_sanitation:
        health_sc = scores.get("Health Department", 0.0)
        hort_sc = scores.get("Horticulture", 0.0)
        # Only boost Horticulture if it's lagging or neck-and-neck with Health.
        # Don't overwrite if Horticulture already has a dominant lead.
        if health_sc > hort_sc and (health_sc - hort_sc) <= 2.0:
            scores["Horticulture"] = health_sc + 0.1

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
