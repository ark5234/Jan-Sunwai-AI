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
    "Civil Department": [
        ([
            "road repair", "road maintenance", "pothole", "potholes", "footpath broken", "footpath repair",
            "footpath divider", "bollard broken", "bollards", "gate broken", "manhole cover missing",
            "mainhole cover", "road signage", "road sign", "spot fixing", "malba stacking", "malba stuck",
            "malba dumped", "zebra crossing", "drainage overflow", "waterlogging", "water logging",
            "dustbin not clean", "open gym maintenance", "cemented base grass", "planning",
            "smart bin", "road drainage", "drainage blocked", "drainage coverage missing", "drainage silt",
            "sewer block", "sewer blocked", "sewer manhole", "sewer overflow", "sewer silt",
            "broken pipeline", "contaminated water", "hand pump", "illegal connection", "water leakage",
            "leakage of water", "low water supply", "water meter faulty", "water atm", "water tanker",
            "debris removal", "construction waste", "improper disposal", "open manhole", "open drain",
            "stagnant water", "sewerage overflow", "storm water", "bathroom repair", "broken manhole",
            "door repair", "window repair", "fencing work", "interlocking flooring", "maintenance of building",
            "building maintenance", "toilet repair", "water tank repair", "water related problem",
            "bell mouth", "gully trap", "rwh", "rainwater harvesting", "monsoon drainage",
            "unpaved road", "road waterlogging", "road crack", "road digging", "road cutting",
            "footpath encroachment", "pavement broken", "pavement repair", "culvert", "bridge repair",
            "retaining wall", "boundary wall", "public toilet maintenance", "community toilet",
            "street repair", "lane repair", "divider repair", "median repair",
            "pipe burst", "pipeline leakage", "water supply disruption", "no water supply",
            "sewer smell", "sewer gas", "drainage smell", "nala overflow", "nala blockage",
            "pump house", "pumping station", "overhead tank", "underground tank", "water pressure low",
            "indoor gym", "indoor gym maintenance", "gym equipment broken", "indoor gym equipment",
            "gym hall", "gymnasium maintenance", "indoor sports facility", "gym room",
            "multipurpose hall maintenance", "ndmc housing", "municipal housing",
            "government housing complaint", "ndmc flat", "ndmc quarter", "quarter repair",
            "residential quarter", "staff quarter", "government quarter maintenance",
            "colony maintenance", "ndmc colony", "housing society complaint",
            "road construction", "construction debris on road", "rebar", "iron rod", "steel rod", "cement bag", "construction material",
            "pothole-filled", "crater", "visible potholes", "road depression", "sinkage", "road sink", "caved in", "sinkhole",
            "damaged road", "broken road", "cracked road", "uneven road", "dirt road", "peeling asphalt", "bad road condition", "rubble", "cracked surface", "uneven surface",
            "damaged pavement", "cracked pavement", "pavement damage", "road surface", "road with fallen leaves",
            "damaged footpath", "puddles", "stagnant water on road", "flooded", "flooding", "flood",
            "overflowing drain", "dirty drain", "sewer leak", "sewage", "pipe leak", "water leak", "leaking pipe", "broken water pipe", "water gushing",
            "manhole", "missing cover", "damaged bridge", "crack in bridge",
            "wet sand", "muddy road", "muddy path", "sandy road", "sand on road", "sand on roadside",
            "sand on the road", "sand on the roadside", "gravel road", "mud on road", "slushy road", "slush", "waterlogged road",
            "wet road", "sand and mud", "mud and sand", "sandy mud", "muddy surface",
            "slippery road", "slippery surface", "road is slippery", "road dug up",
            "sidewalk", "sidewalk broken", "cracked sidewalk", "broken bricks", "broken tiles", "broken paver", "missing bricks"
        ], 3.0),
    ],
    "Health Department": [
        ([
            "air pollution", "smoke from factory", "factory smoke", "industrial smoke",
            "smoke from vehicles", "vehicle smoke", "traffic congestion", "traffic pollution",
            "garbage dumped", "garbage on road", "garbage on public land", "overflowing dhalao",
            "dhalao overflow", "dhalao full", "bricks dumped", "bori dumped", "sand piled",
            "sand on roadside", "barren land", "land to be greened", "unpaved road dust",
            "garbage dump", "garbage dumps", "open garbage", "littering", "public littering",
            "air quality", "dust pollution", "noise pollution", "foul smell", "bad smell",
            "burning waste", "burning garbage", "open burning", "biomass burning",
            "health licensing", "food license", "food safety", "eating house license",
            "slaughterhouse", "dairy license", "health permit",
            "medical services", "public health", "epidemic", "disease outbreak",
            "dengue", "malaria", "cholera", "food poisoning", "contamination",
            "mosquito breeding", "mosquito menace", "pest control", "rat menace",
            "cockroach infestation", "fly menace", "insect infestation",
            "swachh bharat waste", "sanitation complaint", "cleanliness complaint",
            "unhygienic condition", "filth", "improper waste disposal",
            "metro waste", "construction dust", "demolition dust", "road dust",
            "garbage", "trash", "rubbish", "refuse", "plastic waste", "plastic bags", "sweeping",
            "debris", "waste pile", "waste dump", "waste heap", "open dump", "illegal dump",
            "overflowing bin", "overflowing trash", "overflowing garbage", "spilled garbage",
            "dustbin", "trash bin", "garbage bin", "overturned bin", "tipped bin", "spilled trash",
            "scattered waste", "filthy toilet", "unclean toilet", "public urination", "open defecation", "spitting",
            "stench", "rotten", "dead animal", "carcass", "dead dog", "medical waste", "hospital waste", "bio hazard",
            "chemical dump", "toxic waste"
        ], 3.0),
    ],
    "Electrical Department": [
        ([
            "street light not working", "street light off", "street light broken", "street light fault",
            "high mast light", "high mask light", "light not working", "light off",
            "fire in pole", "electric pole fire", "pole burning",
            "wire hanging", "hanging wire", "broken wire", "loose wire", "dangling wire",
            "wire snapped", "wire fallen", "live wire", "electric wire on road",
            "ac not working", "air conditioner fault", "ac breakdown",
            "cctv not working", "cctv fault", "cctv broken", "surveillance camera",
            "water cooler not working", "water cooler fault", "cooler breakdown",
            "appliances burnt", "appliance damage", "electric damage", "burnt appliance",
            "electric building maintenance", "building electrification",
            "transformer fault", "transformer breakdown", "transformer fire",
            "power fluctuation", "voltage fluctuation", "low voltage", "high voltage",
            "electric shock", "electrocution risk", "electric hazard",
            "substation fault", "feeder fault", "load shedding",
            "park light", "park lighting", "garden light", "underpass light",
            "traffic signal fault", "signal not working", "traffic light broken",
            "generator fault", "dg set", "backup power",
            "electrical maintenance", "wiring fault", "short circuit",
            "street light", "streetlight", "street lamp", "lamp post", "lamppost",
            "broken light", "non-functional light", "damaged light",
            "unlit road", "dark road", "dark street", "no lighting",
            "fallen wire", "electrical wire", "open transformer", "damaged transformer", "leaking transformer",
            "electrical box", "fuse box", "circuit breaker", "meter box", "distribution panel",
            "electrical fire", "panel fire", "electrical overload", "burning wire", "burning cable", "sparking wire",
            "fallen electric pole", "tilted pole", "broken pole", "exposed wire", "bare wire", "naked cable",
            "sparking", "electrocut", "transformer", "electric pole", "utility pole"
        ], 3.0),
    ],
    "Commercial": [
        ([
            "electricity bill", "electricity bill problem", "bill issue", "wrong bill",
            "high bill", "bill not received", "bill dispute", "bill error",
            "generate bill", "billing problem", "billing complaint",
            "online payment issue", "payment failed", "payment problem", "payment not updated",
            "transfer of money", "refund", "billing transfer",
            "smart meter", "smart meter not installed", "meter not installed",
            "consumer number not found", "consumer id missing", "consumer number issue",
            "meter data not available", "meter details incorrect", "wrong meter details",
            "meter sparking", "meter spark", "meter catching fire",
            "meter fault", "faulty meter", "meter not working", "meter reading",
            "meter reading issue", "wrong meter reading",
            "new connection", "electricity connection", "new electric connection",
            "release of electricity", "reconnection", "disconnection",
            "power theft", "electricity theft", "detection of power theft",
            "commercial connection", "load extension", "load increase",
            "sanctioned load", "connected load", "tariff issue", "tariff complaint",
            "security deposit", "meter box", "meter seal broken",
            "broken meter", "billing issue", "excessive bill", "property tax", "license renewal"
        ], 3.0),
    ],
    "Enforcement": [
        ([
            "encroachment", "illegal encroachment", "land encroachment", "property encroachment",
            "footpath encroachment", "road encroachment", "public land encroachment",
            "unauthorised hawker", "illegal hawker", "illegal vendor", "illegal stall",
            "street vendor", "unauthorised vending", "vending zone violation",
            "unauthorised advertisement", "illegal hoarding", "illegal banner",
            "illegal flex", "illegal signboard", "unauthorised signage", "hoarding",
            "banner violation", "advertisement violation",
            "unauthorised parking", "illegal parking", "wrong parking", "no parking violation",
            "footpath parking", "divider parking", "public space parking",
            "parking management", "parking complaint", "parking fine",
            "unauthorised construction", "illegal construction", "building violation",
            "demolition order", "sealing", "de-sealing",
            "unauthorised shop", "illegal shop", "shop encroachment",
            "cattle on road", "stray cattle", "cow on road",
            "nuisance", "public nuisance", "noise nuisance",
            "pavement encroachment", "commercial encroachment", "illegal occupation", "hawker", "unauthorized vendor", "squatter",
            "traffic deadlock", "deadlock", "standstill", "traffic jam", "gridlock", "chaotic traffic", "severe accident", "heavy traffic",
            "road blockage", "road blocked", "road obstruction", "lane violation", "wrong side driving", "unauthorized"
        ], 3.0),
    ],
    "Horticulture": [
        ([
            "horticulture waste", "horticulture waste removal", "garden waste",
            "tree branch fallen", "fallen tree", "tree fallen", "uprooted tree",
            "tree trimming", "tree pruning", "tree cutting", "overgrown tree",
            "branch hanging", "branch on road", "dangerous branch",
            "park maintenance", "garden maintenance", "public park",
            "grass cutting", "lawn maintenance", "mowing",
            "plant maintenance", "flower bed", "nursery",
            "dry leaves", "leaf litter", "green waste",
            "tree plantation", "plantation drive", "sapling",
            "park bench broken", "park light", "park path broken",
            "hedge trimming", "shrub trimming", "creeper removal",
            "avenue plantation", "road side plantation", "median plantation",
            "compost", "vermi compost", "organic waste",
            "park cleaning", "park sweeping", "park encroachment",
            "open gym", "outdoor gym", "open gym maintenance",
            "outdoor gym maintenance", "open gym equipment broken",
            "open gym equipment not working", "park gym",
            "park gym equipment", "outdoor exercise equipment",
            "open air gym", "fitness equipment in park",
            "overgrown", "unmaintained park", "neglected park", "overgrown weeds", "fallen leaves", "leaves scattered", "leaf debris", "leaves", "leaf", "pile of grass", "dry grass", "vegetation pile", "vegetation debris",
            "dead plant", "dead plants", "dry plants", "withered", "broken branch", "tree branch", "branches blocking", "tree blocking road", "tree on road", "garden", "park", "greenery", "vegetation", "weed"
        ], 3.0),
    ],
    "EBR Department": [
        ([
            "building design", "architectural plan", "building plan",
            "building approval", "construction approval", "architectural approval",
            "renovation plan", "structural design", "structural approval",
            "building drawing", "layout plan", "site plan",
            "building completion certificate", "occupation certificate",
            "bye law violation", "building bye law", "setback violation",
            "floor area ratio", "far violation", "fsi violation",
            "heritage building", "heritage structure",
            "public building maintenance", "institutional building",
            "office building repair", "government building repair",
            "building collapse", "unsafe building", "dangerous structure"
        ], 3.0),
    ],
    "Fire Department": [
        ([
            "fire", "fire incident", "fire accident", "building fire", "house fire",
            "fire in market", "fire in shop", "fire in vehicle",
            "fire noc", "fire no objection certificate", "fire safety noc",
            "fire safety", "fire safety violation", "fire hazard",
            "fire extinguisher", "fire hydrant", "fire hydrant not working",
            "sprinkler system", "fire alarm", "fire alarm not working",
            "emergency exit blocked", "exit blocked", "evacuation route",
            "fire brigade", "fire engine", "fire tender",
            "gas leak", "lpg leak", "cylinder leak",
            "explosion", "blast", "electrical fire",
            "burning", "flames", "smoke emission", "thick smoke", "smoke billow", "flammable", "explosive"
        ], 3.0),
    ],
    "IT Department": [
        ([
            "website not working", "portal issue", "portal not loading",
            "app not working", "mobile app issue", "ndmc app",
            "online service down", "digital service", "e-service",
            "complaint not registered", "complaint system down",
            "login issue", "password reset", "account issue",
            "data error", "system error", "technical error",
            "otp not received", "verification failed",
            "digital payment portal", "online portal", "citizen portal",
            "network issue", "connectivity issue", "server down",
            "software complaint", "hardware complaint", "computer issue",
            "printer not working", "scanner issue", "biometric",
            "app bug", "portal bug", "website down", "app down", "server error", "database error", "portal crash", "login failed"
        ], 3.0),
    ],
    "VBD Department": [
        ([
            "dengue", "dengue fever", "dengue case", "dengue mosquito",
            "malaria", "malaria case", "malaria mosquito",
            "chikungunya", "vector borne disease", "vector disease",
            "mosquito breeding", "mosquito larvae", "stagnant water mosquito",
            "fogging", "fogging request", "anti larval", "larvicide",
            "aedes mosquito", "anopheles mosquito", "culex mosquito",
            "surveillance worker", "disease surveillance",
            "fever cluster", "disease cluster", "outbreak",
            "sand fly", "kala azar", "filaria",
            "cooler water stagnant", "overhead tank mosquito",
            "water storage mosquito", "container breeding",
            "mosquitoes", "larvae", "stagnant water", "standing water", "water pooling", "fumigation", "mosquito net"
        ], 3.0),
    ],
    "Uncategorized": [
        ([
            "welfare complaint", "community welfare",
            "ptu complaint", "ptu related",
            "general complaint", "miscellaneous complaint",
            "unresolved complaint", "pending complaint"
        ], 3.0),
    ],
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
