import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FuturesTimeout
import ollama
from PIL import Image
from app.config import settings
from app.category_utils import CANONICAL_CATEGORIES, canonicalize_label
from app.rule_engine import classify_by_rules, parse_vision_text_to_payload
from app.model_selector import select_vision_model
from app.llm_lock import ollama_lock

# Use an explicit client so the host URL comes from OLLAMA_BASE_URL config
# (the module-level ollama.generate() defaults to localhost:11434 which
# breaks inside Docker where localhost = the container, not the host).
def _get_ollama_client() -> ollama.Client:
    return ollama.Client(host=settings.ollama_base_url)

# Human-readable definitions passed to the reasoning model so it can
# make a contextual decision rather than just matching a string.
CATEGORY_DEFINITIONS: dict[str, str] = {
    "Civil Department":                "broken roads, potholes, road depression, sinkage, cracked pavement, damaged footpaths, leaking pipes, bridge damage, waterlogging, flooded streets, blocked drains",
    "Health Department":               "garbage dumps, overflowing trash bins, dirty public toilets, waste piles on streets",
    "Horticulture":                    "fallen or uprooted trees, overgrown vegetation, unmaintained parks, leaf litter, accumulated dead leaves",
    "Electrical Department":           "broken street lights, non-functional lamp posts, dark public roads, dangling wires, open transformers",
    "Commercial":                      "property tax issues, municipal billing disputes, commercial licensing",
    "Enforcement":                     "illegal parking, footpath encroachment, unauthorized vendors, hawkers blocking pavement, public nuisance",
    "VBD Department":                  "mosquito breeding, mosquito larvae in stagnant water, fogging requests, vector-borne disease risks (excluding roadside flooding)",
    "EBR Department":                  "illegal construction, building code violations, unauthorized modifications",
    "Fire Department":                 "fire hazards, flammable dumps, lack of fire safety",
    "IT Department":                   "portal errors, online payment failures, app bugs",
    "Uncategorized":                   "does not clearly match any of the above civic categories",
}

# Keywords that strongly indicate a non-civic / irrelevant _vision description_
# (checked after the vision model has run against its full text output)
_NON_CIVIC_VISION_PHRASES: list[str] = [
    # Payment / financial
    "payment receipt", "transaction", "upi", "bank statement", "invoice",
    "receipt", "bill payment", "debit", "credit card", "bank transfer",
    "amount paid", "transaction id", "debited", "credited",
    # UI / digital
    "mobile screen", "phone screen", "app screenshot", "computer screen",
    "monitor screen", "website screenshot", "chat screenshot", "text message",
    "digital receipt", "qr code", "barcode",
    # Documents
    "document", "certificate", "id card", "aadhar", "passport", "form filled",
]

# Hard non-civic cues: always out-of-scope regardless of nearby words.
_HARD_NON_CIVIC_KEYWORDS = [
    # Indian Railways is Central Government — not in scope for this portal
    "railway station", "train station", "railway platform", "train platform",
    "railway track", "train track", "metro station",
]

# Soft non-civic cues: may still be civic when strong civic context is present
# (e.g., animal tearing open garbage bags in a sanitation complaint).
_SOFT_NON_CIVIC_KEYWORDS = [
    "selfie", "portrait", "food", "meal", "restaurant", "cartoon", "anime",
    "gaming", "screenshot", "indoor furniture", "appliance", "pet", "animal",
    "beautiful landscape", "clear sky",
]

# Backward-compat alias for existing checks.
_NEGATIVE_KEYWORDS = _SOFT_NON_CIVIC_KEYWORDS + _HARD_NON_CIVIC_KEYWORDS

_CIVIC_CONTEXT_TERMS = [
    # Sanitation / waste
    "garbage", "trash", "waste", "litter", "dump", "rubbish", "dustbin",
    "trash bin", "garbage bin", "overflowing bin", "spilled garbage", "spilled trash",
    "waste pile", "open dump",
    # Roads / drains
    "pothole", "road damage", "cracked road", "broken road", "waterlogging",
    "blocked drain", "drain overflow", "sewer overflow", "stagnant water",
    # Electrical
    "street light", "dangling wire", "exposed wire", "transformer", "electrical box",
    # Other civic domains
    "illegal parking", "encroachment", "mosquito", "larvae", "fogging",
    "illegal construction", "building collapse", "fire hazard", "chemical dump",
]

_TRAFFIC_TERMS: list[str] = [
    "traffic congestion", "traffic jam", "gridlock", "traffic deadlock",
    "road congestion", "heavy traffic", "vehicle congestion", "chaotic traffic",
]

_VEHICLE_TERMS: list[str] = [
    "car", "cars", "vehicle", "vehicles", "bus", "buses", "truck", "trucks",
    "motorcycle", "motorcycles", "auto", "autorickshaw", "rickshaw",
    "two-wheeler", "scooter", "cab", "taxi", "van", "jeep", "lorry", "minibus",
]

_ELECTRICAL_TERMS: list[str] = [
    "electrical", "electric", "wire", "wires", "cable", "cables", "transformer",
    "meter box", "fuse box", "junction box", "electrical box", "distribution panel",
    "panel board", "switchboard", "circuit breaker", "short circuit", "overload",
    "high voltage", "live wire", "sparking",
]

_FIRE_TERMS: list[str] = [
    "fire", "flame", "flames", "burning", "smoke", "spark", "sparks", "blaze",
    "ignition", "scorch",
]

# Keyword fallback: if reasoning model fails, map description keywords → category
# Ordered from most-specific to least-specific
_KEYWORD_FALLBACK_BY_DEPARTMENT: dict[str, list[str]] = {
    # Keep Electrical first so electrical-fire scenes don't get swallowed by generic smoke words.
    "Electrical Department": [
        "electrical fire", "panel fire", "meter fire", "transformer fire",
        "short circuit", "electrical overload", "burning wire", "burning cable",
        "sparking wire", "smoke from panel", "distribution panel", "junction box",
        "fuse box", "electrical box", "circuit breaker", "street light", "lamp post",
        "unlit road", "broken light", "dark road", "pole light", "dangling wire",
        "hanging wire", "open transformer", "fallen electric pole", "exposed wire",
        "power cable", "sparking", "live wire", "high voltage",
    ],
    "Civil Department": [
        "pothole", "road damage", "cracked road", "broken road", "damaged road",
        "road depression", "sinkage", "road sinking", "uneven road surface",
        "damaged pavement", "broken pavement", "footpath damage", "manhole",
        "caved in", "uneven road", "missing cover", "crater", "waterlog",
        "flooded", "flood", "drain overflow", "sewer overflow", "pipe leak", "water leak",
        "leaking pipe", "burst pipe", "broken water pipe", "water gushing", 
        "stagnant water", "blocked drain", "drainage problem", "water supply", "sewage leak", "drain",
        "wet sand", "muddy road", "muddy path", "sandy road", "sand on road",
        "sand on roadside", "sand on the road", "sand on the roadside",
        "gravel road", "unpaved road", "mud on road", "slushy road", "slush",
        "waterlogged road", "wet road", "sand and mud", "mud and sand",
        "sandy mud", "muddy surface", "slippery road", "slippery surface",
        "road is slippery", "road construction", "road digging",
        "rebar", "iron rod", "steel rod", "cement bag", "construction material",
        "construction waste", "construction debris",
    ],
    "Health Department": [
        "garbage", "trash", "waste", "litter", "dump", "rubbish", "overflowing bin",
        "dustbin", "trash bin", "garbage bin", "overturned bin", "tipped bin",
        "spilled trash", "spilled garbage", "debris",
        "pile of", "large pile", "heap of", "plastic bottles", "plastic bottle",
        "glass bottles", "broken glass", "broken bottles", "empty bottles", "scattered waste",
        "junk", "filth", "filthy", "open dump", "roadside dump", "dead animal",
        "stench", "medical waste",
    ],
    "Horticulture": [
        "fallen tree", "uprooted tree", "overgrown", "dead plant", "broken branch",
        "tree blocking", "overgrown bush", "dry leaves", "park unmaintained", "weed",
        "fallen leaves", "dry leaves", "leaves scattered", "leaf litter", "leaf debris",
        "leaves", "leaf", "pile of grass", "dry grass", "vegetation pile", "garden waste",
    ],
    "Enforcement": [
        "traffic signal", "signal failure", "traffic jam", "road blockage",
        "traffic congestion", "gridlock", "traffic deadlock", "standstill",
        "peak hour", "rush hour", "no lane", "chaotic traffic", "accident",
        "illegal parking", "encroachment", "footpath blocked", "public nuisance",
        "hawker", "unauthorized vendor", "illegal occupation", "vendor blockage",
    ],
    "VBD Department": ["mosquito", "dengue", "malaria", "fogging", "larvae", "mosquito breeding"],
    "EBR Department": ["illegal construction", "unauthorized construction", "building collapse", "unsafe building"],
    "Commercial": ["faulty meter", "property tax", "billing", "license"],
    "IT Department": ["portal bug", "app bug", "login failed", "server error"],
    "Fire Department": ["smoke", "burning", "industrial waste", "air pollution", "open burning", "chemical dump", "toxic"],
}

_RAIL_STRONG_TERMS: list[str] = [
    "railway station", "train station", "railway platform", "train platform",
    "metro station", "station platform", "railway track", "train track", "rail track",
]

_RAIL_WEAK_WHOLE_WORD_TERMS: list[str] = [
    "railway", "railroad", "locomotive", "train", "metro",
]

_TEMPLATE_PLACEHOLDER_SNIPPETS: list[str] = [
    "single phrase",
    "dominant problem visible",
    "2-3 sentence factual description",
    "road/park/drain/building/railway station/train platform/etc",
    "object1",
    "object2",
    "hazard1",
    "hazard2",
    "low/medium/high",
]


def _keyword_fallback(description: str) -> str:
    """Scan the vision description for civic keywords and return best category."""
    desc = description.lower()
    for category, keywords in _KEYWORD_FALLBACK_BY_DEPARTMENT.items():
        if any(kw in desc for kw in keywords):
            return category
    return "Uncategorized"


def _payload_text_for_keyword_fallback(vision_payload: dict) -> str:
    """Combine all structured vision fields into one text blob for fallback matching."""
    parts = [
        str(vision_payload.get("description", "")),
        " ".join(str(item) for item in vision_payload.get("visible_objects", [])),
        str(vision_payload.get("primary_issue", "")),
        str(vision_payload.get("secondary_issue", "")),
        str(vision_payload.get("setting", "")),
        " ".join(str(item) for item in vision_payload.get("hazards", [])),
    ]
    return " ".join(parts)


def _has_civic_context(text: str) -> bool:
    text_lower = text.lower()
    return any(term in text_lower for term in _CIVIC_CONTEXT_TERMS)


def _is_non_civic_text(text: str) -> bool:
    text_lower = text.lower()
    if any(kw in text_lower for kw in _HARD_NON_CIVIC_KEYWORDS):
        return True
    if any(kw in text_lower for kw in _SOFT_NON_CIVIC_KEYWORDS):
        return not _has_civic_context(text_lower)
    return False


def _contains_whole_word(text: str, term: str) -> bool:
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


def _looks_like_template_placeholder(value: str) -> bool:
    v = value.strip().lower()
    if not v:
        return False
    return any(snippet in v for snippet in _TEMPLATE_PLACEHOLDER_SNIPPETS)


def _clean_vision_payload(vision_payload: dict) -> dict:
    """Remove schema-placeholder artifacts occasionally echoed by vision models."""
    for key in ("description", "primary_issue", "secondary_issue", "setting"):
        raw = str(vision_payload.get(key, ""))
        if _looks_like_template_placeholder(raw):
            vision_payload[key] = ""

    cleaned_objects = []
    for item in vision_payload.get("visible_objects", []):
        text = str(item).strip()
        if not text:
            continue
        if _looks_like_template_placeholder(text):
            continue
        cleaned_objects.append(text)
    vision_payload["visible_objects"] = cleaned_objects

    cleaned_hazards = []
    for item in vision_payload.get("hazards", []):
        text = str(item).strip()
        if not text:
            continue
        if _looks_like_template_placeholder(text):
            continue
        cleaned_hazards.append(text)
    vision_payload["hazards"] = cleaned_hazards

    return vision_payload


def _rail_signal_score(
    description: str,
    primary_issue: str,
    setting: str,
    visible_objects_text: str,
) -> int:
    """
    Compute rail-scene confidence from multiple signals.

    We require multiple signals to avoid false positives from one hallucinated term.
    """
    desc = description.lower()
    high_signal = f"{primary_issue} {setting} {visible_objects_text}".lower()

    score = 0
    # Strong rail phrases in high-signal fields carry more weight.
    if any(term in high_signal for term in _RAIL_STRONG_TERMS):
        score += 2
    # Strong phrases in description alone are weaker evidence.
    if any(term in desc for term in _RAIL_STRONG_TERMS):
        score += 1
    # Weak single-word hints require whole-word matching.
    if any(_contains_whole_word(high_signal, term) for term in _RAIL_WEAK_WHOLE_WORD_TERMS):
        score += 1
    if any(_contains_whole_word(desc, term) for term in _RAIL_WEAK_WHOLE_WORD_TERMS):
        score += 1

    return score


def _is_screen_capture(image_path: str) -> bool:
    """
    Heuristic PIL-based check: returns True if the image looks like a
    screenshot, UI screen capture, payment receipt, or scanned document
    rather than an outdoor photograph.

    Key insight from real-world data:
    - Outdoor photos:  all_colors > 15000, center_bright ≈ 0, center_colors > 4000
    - Phone screenshots / receipts: all_colors ≈ 2000 (JPEG), center_bright > 0.80,
      center_colors < 400, high grayscale fraction (mostly black text on white)

    Four independent signals — any two firing together = screenshot:
      S1. Center-region brightness > 0.75  (white document/receipt background)
      S2. Center-region unique-colour count < 400  (few colours in content area)
      S3. Global grayscale fraction > 0.82  (mostly black/white/gray = text doc)
      S4. Global unique-colour count < 3500  (far fewer than real outdoor JPEG)
    """
    try:
        with Image.open(image_path) as img:
            # Downscale for fast sampling
            thumb = img.convert("RGB").resize((200, 200), Image.Resampling.NEAREST)
            width, height = thumb.size

            # ── Center 50% region (avoids phone border / dark status bar noise)
            cx1, cy1 = width // 4, height // 4
            cx2, cy2 = width - width // 4, height - height // 4
            center = thumb.crop((cx1, cy1, cx2, cy2))
            center_px = list(center.getdata())  # type: ignore

            center_colors = len(set(center_px))
            center_total = len(center_px)
            center_bright = sum(1 for r, g, b in center_px if r > 230 and g > 230 and b > 230) / center_total

            # ── Global pixel sample
            all_px = list(thumb.getdata())  # type: ignore
            all_colors = len(set(all_px))
            total = len(all_px)

            # Grayscale: pixels where R≈G≈B (within 25 of each other)
            gray_count = sum(
                1 for r, g, b in all_px
                if abs(int(r) - int(g)) < 25 and abs(int(g) - int(b)) < 25
            )
            gray_frac = gray_count / total

            # ── Individual signals
            s1_bright_center = center_bright > 0.75     # white doc/receipt interior
            s2_few_center    = center_colors < 400      # sparse content area
            s3_grayscale     = gray_frac > 0.82         # mostly black+white text doc
            s4_few_global    = all_colors < 3500        # sparse palette overall

            # Require at least 2 signals to fire (reduces false-positives on
            # foggy/overcast outdoor photos which can look slightly washed out)
            score = sum([s1_bright_center, s2_few_center, s3_grayscale, s4_few_global])
            is_screenshot = score >= 2

            if is_screenshot:
                print(
                    f"[classifier] screenshot heuristic TRIGGERED (score={score}/4): "
                    f"center_bright={center_bright:.2f}, center_colors={center_colors}, "
                    f"gray_frac={gray_frac:.2f}, all_colors={all_colors}"
                )
            return is_screenshot
    except Exception as e:
        print(f"[classifier] _is_screen_capture check failed ({e}) - skipping")
        return False


def _load_image_as_jpeg_bytes(image_path: str) -> bytes:
    """
    Load any image file, convert to RGB, and return JPEG bytes.
    This prevents:
    - GGML_ASSERT errors from RGBA/4-channel images
    - "unknown format" errors from BMP, TIFF, WebP variants, etc.
    """
    with Image.open(image_path) as img:
        # Strip alpha channel and palette modes
        if img.mode not in ("RGB",):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()


class CivicClassifier:
    """
    Hybrid Vision → Rule Engine → Optional Reasoning classifier.

    Optimised for 4 GB VRAM (RTX 3050) local deployment.

    Pipeline:
        Step 1 — Vision (qwen2.5vl:3b): Produces structured JSON description.
        Step 2 — Rule Engine (Python, zero VRAM): Deterministic keyword scoring.
        Step 3 — Reasoning (llama3.2:1b, OPTIONAL): Only invoked when the rule
                 engine flags the result as ambiguous.

    This hybrid approach:
        - Saves ~1.2 GB VRAM (reasoning model unloaded most of the time)
        - Is faster (rule engine is instant)
        - Is more deterministic (known rule set for 11 categories)
        - Falls back to LLM only for genuinely hard cases
    """

    def _unload_model(self, model_name: str) -> None:
        """Ask Ollama to unload a model from VRAM (keep_alive=0)."""
        try:
            client = _get_ollama_client()
            client.generate(model=model_name, prompt="", keep_alive=0)
        except Exception:
            pass  # best-effort; server may not support keep_alive

    def classify_user_description(self, user_text: str) -> dict:
        """
        Classify an optional user-provided grievance description for routing.

        This is deterministic (rule engine + keyword fallback) and does not
        invoke any additional LLM model.
        """
        normalized = " ".join(str(user_text or "").split()).strip()
        if not normalized:
            return {
                "department": "Uncategorized",
                "label": "",
                "confidence": 0.0,
                "is_valid": False,
                "is_non_civic": False,
                "method": "user_text_empty",
                "rationale": "empty user grievance text",
            }

        normalized_lower = normalized.lower()
        if _is_non_civic_text(normalized_lower):
            return {
                "department": "Uncategorized",
                "label": normalized,
                "confidence": 0.2,
                "is_valid": False,
                "is_non_civic": True,
                "method": "user_text_non_civic",
                "rationale": "user grievance text appears out-of-scope/non-civic",
            }

        payload = parse_vision_text_to_payload(normalized)
        rule_result = classify_by_rules(
            payload,
            ambiguity_threshold=1.2,
            confidence_gap_threshold=0.75,
        )
        canonical = canonicalize_label(str(rule_result.get("category", "Uncategorized")))
        confidence = float(rule_result.get("confidence", 0.0))
        method = f"user_text_{rule_result.get('method', 'rule_engine')}"
        rationale = "rule engine over user grievance text"

        if canonical == "Uncategorized":
            keyword_result = canonicalize_label(_keyword_fallback(normalized))
            if keyword_result != "Uncategorized":
                canonical = keyword_result
                confidence = max(confidence, 0.62)
                method = "user_text_keyword_fallback"
                rationale = "keyword fallback over user grievance text"

        is_valid = canonical != "Uncategorized"
        if is_valid:
            confidence = max(confidence, 0.6)
        else:
            confidence = max(confidence * 0.5, 0.1)

        return {
            "department": canonical,
            "label": normalized,
            "confidence": round(confidence, 3),
            "is_valid": is_valid,
            "is_non_civic": False,
            "method": method,
            "rationale": rationale,
        }

    def classify(self, image_path: str) -> dict:
        timings = {
            "vision_ms": 0.0,
            "rule_engine_ms": 0.0,
            "reasoning_ms": 0.0,
        }
        if not os.path.exists(image_path):
            return {
                "department": "Unknown",
                "label": "Image file not found",
                "confidence": 0.0,
                "is_valid": False,
                "error": "resolved upload file does not exist",
                "details": "resolved upload file does not exist",
                "method": "error",
                "rationale": "file not found",
                "raw_json": "",
                "timings": timings,
            }

        # ── Pre-check: PIL-based screenshot / document detector ──────────────
        # Run BEFORE acquiring the ollama_lock so we don't block the GPU thread.
        if _is_screen_capture(image_path):
            return {
                "department": "Invalid Content",
                "label": "Screenshot or digital document — not a civic photo",
                "confidence": 0.9,
                "is_valid": False,
                "is_non_civic": True,
                "vision_description": "Image appears to be a screenshot, payment receipt, or digital document rather than an outdoor civic issue photograph.",
                "vision_payload": {},
                "raw_category": "Invalid Content",
                "rationale": "PIL heuristic: low unique-colour count / solid background indicates screen capture or document scan",
                "method": "non_civic_guard",
                "model_used": "pil_heuristic",
                "raw_json": "",
                "timings": timings,
            }

        ollama_lock.acquire()
        try:
            image_bytes = _load_image_as_jpeg_bytes(image_path)
            client = _get_ollama_client()

            # Track whether we've already tried a second vision model
            _retry_used = False
            _vision_was_garbage = False   # True when primary vision returned empty/garbage

            # ------------------------------------------------------------------
            # STEP 1 — Vision: Structured JSON description
            #          3-tier cascade: primary → mid → fallback
            #          Each tier has a wall-clock timeout; on timeout or OOM
            #          the model is unloaded and the next tier is tried.
            # ------------------------------------------------------------------
            vision_start = time.perf_counter()

            # Proactive RAM check: pick the best model that fits (3-tier aware)
            active_vision_model = select_vision_model()

            # Models that can handle the JSON-schema prompt and format="json".
            # moondream (and other pure-captioning models) need a simpler prompt.
            _json_capable: set[str] = {
                m for m in [settings.vision_model, settings.mid_vision_model] if m
            }

            # Prompt strings — defined once, selected per tier inside the loop
            _json_prompt = (
                "You are a civic-issue vision analyst for Indian municipal complaints. "
                "Analyze the image and return strict JSON only.\n\n"
                "JSON schema:\n"
                "{\n"
                '  "description": "2-3 sentence factual description of what you CLEARLY see",\n'
                '  "visible_objects": ["object1", "object2"],\n'
                '  "primary_issue": "single phrase — the DOMINANT problem visible",\n'
                '  "secondary_issue": "single phrase or empty string",\n'
                '  "hazards": ["hazard1", "hazard2"],\n'
                '  "setting": "road/park/drain/building/railway station/train platform/etc",\n'
                '  "confidence": "low/medium/high"\n'
                "}\n\n"
                "STRICT RULES:\n"
                "- ONLY describe what you can CLEARLY and DIRECTLY see. Do NOT infer or guess.\n"
                "- If a scene contains scattered litter, determine if it is primarily plant-based (dried leaves, twigs, fallen branches, piles of dry grass) or man-made waste (plastic, food wrappers, metal, glass, construction debris).\n"
                "- If you see a sidewalk or roadside covered in significant dust, sand, gravel, or silt, explicitly mention 'sand on the road' or 'dust accumulation' in the description.\n"
                "- Only describe an issue as 'sanitation' or 'garbage' if man-made waste, trash bags, or waste bins are clearly visible.\n"
                "- If you see construction materials like rebar (iron rods), cement bags, or bricks piled on a road or sidewalk, explicitly mention them as 'construction material' or 'construction waste'.\n"
                "- If the dominant objects are fallen or dried leaves or piles of grass, explicitly describe them as such and avoid the word 'garbage'.\n"
                "- If you see flames/smoke/sparks near wires, a transformer, meter box, or electrical panel, "
                "set primary_issue to 'electrical fire hazard' (NOT traffic congestion).\n"
                "- If you see a train, railway platform, or railway station, say so EXPLICITLY "
                "in the description — do NOT describe a railway platform as a 'sidewalk' or 'road'.\n"
                "- If the dominant scene is heavy vehicle traffic, crowded roads, traffic jam, "
                "or congestion with NO clear infrastructure damage, set primary_issue to "
                "'traffic congestion' and description should reflect that.\n"
                "- Never use 'traffic congestion' unless vehicles are clearly visible and dominant in the scene.\n"
                "- Be specific: 'traffic congestion' / 'road damage' / 'waterlogging' / 'pipe leak' / "
                "'broken street light' / 'fallen tree' / 'garbage dump' / 'dangling wire' / "
                "'hawker encroachment' / 'illegal parking' / 'broken water pipe' / 'railway platform' / 'rebar on road' / 'vegetation pile' / 'sand accumulation'\n"
                "- If stagnant water is visible near a broken road, pothole, or caved-in area, prioritize naming the infrastructure damage ('road damage' / 'pothole') as the primary issue.\n"
                "- If you see a small dark object on the ground, do NOT assume it is a 'broken water pipe' unless it is clearly a metallic or PVC pipe and water is leaking. If it's just debris or animal waste, call it 'debris' or 'scattered litter'.\n"
                "- If you see vendors, stalls, or hawkers blocking a sidewalk or road, use 'encroachment' or 'hawker blockage' as the primary issue.\n"
                "- If the image is a phone screenshot, payment receipt, bank transaction, "
                "UPI screen, chat message, or any digital/scanned document, set "
                "primary_issue to 'non_civic_document' and description to describe it as such.\n"
                "- Keep description under 40 words\n"
                "- No markdown, no explanation outside JSON"
            )
            _simple_prompt = (
                "Look at this image carefully and describe ONLY what you can clearly see. "
                "What is the main activity or condition visible in the scene? "
                "Look for: garbage/litter, broken roads/potholes, leaking pipes, "
                "fallen trees/branches, broken street lights, dangling wires, "
                "stagnant water, or unauthorized vendors blocking pavements. "
                "Describe in 2-3 factual sentences without guessing or assuming."
            )

            def _build_kwargs(model_name: str) -> dict:
                if model_name in _json_capable:
                    return dict(
                        model=model_name,
                        format="json",
                        prompt=_json_prompt,
                        images=[image_bytes],
                        options={"num_ctx": 1024, "temperature": 0.0},
                    )
                return dict(model=model_name, prompt=_simple_prompt, images=[image_bytes], options={"temperature": 0.0})

            # Build 3-tier ordered chain starting from the RAM-selected model.
            # Tiers below the selected one are skipped (already known to be too large).
            _full_chain: list[str] = list(dict.fromkeys(
                m for m in [
                    settings.vision_model,
                    settings.mid_vision_model,
                    settings.fallback_vision_model,
                ] if m
            ))
            try:
                start_idx = _full_chain.index(active_vision_model)
            except ValueError:
                start_idx = 0
            models_to_try = _full_chain[start_idx:]

            if not models_to_try:
                raise RuntimeError(
                    "No vision models available (check VISION_MODEL / MID_VISION_MODEL config)."
                )

            vision_response = None
            timeout_secs = settings.vision_timeout_seconds

            for model_name in models_to_try:
                is_last = (model_name == models_to_try[-1])
                try:
                    # Use shutdown(wait=False) so a timed-out model thread is
                    # abandoned immediately rather than blocking until it finishes.
                    _pool = ThreadPoolExecutor(max_workers=1)
                    try:
                        future = _pool.submit(client.generate, **_build_kwargs(model_name))
                        vision_response = future.result(timeout=timeout_secs)
                    except _FuturesTimeout:
                        _pool.shutdown(wait=False, cancel_futures=True)
                        raise
                    finally:
                        # non-timeout path: let the pool finish normally
                        try:
                            _pool.shutdown(wait=False)
                        except Exception:
                            pass
                    active_vision_model = model_name
                    break  # success
                except _FuturesTimeout:
                    if not is_last:
                        next_tier = models_to_try[models_to_try.index(model_name) + 1]
                        print(f"[classifier] {model_name} timed out after {timeout_secs}s "
                            f"-> unloading and trying next tier: {next_tier}")
                        self._unload_model(model_name)
                        continue
                    raise RuntimeError(
                        f"All vision models timed out after {timeout_secs}s. "
                        "Try increasing VISION_TIMEOUT_SECONDS or freeing GPU/RAM."
                    )
                except Exception as model_err:
                    err_msg = str(model_err).lower()
                    is_oom = any(kw in err_msg for kw in [
                        "memory", "oom", "out of memory", "not enough",
                        "insufficient", "cannot allocate",
                    ])
                    if is_oom and not is_last:
                        next_tier = models_to_try[models_to_try.index(model_name) + 1]
                        print(f"[classifier] {model_name} OOM ({model_err}) "
                            f"-> falling back to {next_tier}")
                        self._unload_model(model_name)
                        continue
                    raise  # not OOM or last model → propagate

            if vision_response is None:
                raise RuntimeError("No vision model responded — all models timed out or failed.")
            raw_vision_text: str = vision_response["response"].strip()
            if not raw_vision_text:
                raise RuntimeError("Vision model returned an empty response.")

            # Parse the vision output based on model capability
            if active_vision_model in _json_capable:
                # JSON-capable model (qwen2.5vl, granite3.2-vision, etc.)
                try:
                    vision_payload = json.loads(raw_vision_text)
                except json.JSONDecodeError:
                    vision_payload = parse_vision_text_to_payload(raw_vision_text)
            else:
                # Plain-text fallback model (moondream, etc.)
                vision_payload = parse_vision_text_to_payload(raw_vision_text)

            raw_vision_json = raw_vision_text  # audit trail

            # Ensure all expected keys exist
            vision_payload.setdefault("description", "")
            vision_payload.setdefault("visible_objects", [])
            vision_payload.setdefault("primary_issue", "")
            vision_payload.setdefault("secondary_issue", "")
            vision_payload.setdefault("hazards", [])
            vision_payload.setdefault("setting", "")
            vision_payload = _clean_vision_payload(vision_payload)
            timings["vision_ms"] = round((time.perf_counter() - vision_start) * 1000.0, 2)

            # ------------------------------------------------------------------
            # EARLY-EXIT: Non-civic scene detection across ALL vision fields.
            # Check EVERY field the model returned, not just the description.
            # This catches cases where the model correctly says "train" in
            # visible_objects or setting but calls the ground a "sidewalk".
            # ------------------------------------------------------------------
            _all_payload_text = " ".join([
                str(vision_payload.get("description", "")),
                " ".join(str(o) for o in vision_payload.get("visible_objects", [])),
                str(vision_payload.get("primary_issue", "")),
                str(vision_payload.get("secondary_issue", "")),
                str(vision_payload.get("setting", "")),
                " ".join(str(h) for h in vision_payload.get("hazards", [])),
                raw_vision_json,  # also scan raw model output for any rail terms
            ]).lower()

            _pre_has_electrical = any(e in _all_payload_text for e in _ELECTRICAL_TERMS)
            _pre_has_fire = any(f in _all_payload_text for f in _FIRE_TERMS)
            _pre_has_electrical_fire_hazard = _pre_has_electrical and _pre_has_fire

            _visible_objects_text = " ".join(str(o) for o in vision_payload.get("visible_objects", []))
            _rail_score = _rail_signal_score(
                description=str(vision_payload.get("description", "")),
                primary_issue=str(vision_payload.get("primary_issue", "")),
                setting=str(vision_payload.get("setting", "")),
                visible_objects_text=_visible_objects_text,
            )

            # Require at least 2 rail signals and suppress this guard when
            # electrical-fire hazard cues are present.
            if _rail_score >= 2 and not _pre_has_electrical_fire_hazard:
                print(
                    "[classifier] non-civic scene detected (rail/transit) in payload "
                    f"(score={_rail_score}) - returning Uncategorized"
                )
                return {
                    "department": "Uncategorized",
                    "label": str(vision_payload.get("description", "Railway/transit scene")),
                    "confidence": 0.85,
                    "is_valid": False,
                    "vision_description": str(vision_payload.get("description", "")),
                    "vision_payload": vision_payload,
                    "raw_category": "Uncategorized",
                    "rationale": "railway/transit scene — not in civic portal scope",
                    "method": "non_civic_guard",
                    "model_used": active_vision_model,
                    "raw_json": raw_vision_json,
                    "timings": timings,
                }
            if _rail_score >= 2 and _pre_has_electrical_fire_hazard:
                print(
                    "[classifier] rail/transit signals ignored because electrical-fire cues are present "
                    f"(rail_score={_rail_score})"
                )

            # ── Non-civic document / screenshot detected by vision model output ──
            _NON_CIVIC_VISION_TRIGGERS = [
                "non_civic_document", "payment receipt", "transaction id",
                "upi", "bank statement", "invoice", "digital receipt",
                "mobile screen", "phone screen", "app screenshot", "chat message",
                "scanned document", "id card", "aadhar",
            ]
            _vision_non_civic_hit = any(
                t in _all_payload_text for t in _NON_CIVIC_VISION_TRIGGERS
            )
            if _vision_non_civic_hit:
                print(f"[classifier] non-civic document/screenshot detected via vision output")
                return {
                    "department": "Invalid Content",
                    "label": str(vision_payload.get("description", "Non-civic digital document or screenshot")),
                    "confidence": 0.9,
                    "is_valid": False,
                    "is_non_civic": True,
                    "vision_description": str(vision_payload.get("description", "")),
                    "vision_payload": vision_payload,
                    "raw_category": "Invalid Content",
                    "rationale": "vision model detected a payment receipt, screenshot, or digital document",
                    "method": "non_civic_guard",
                    "model_used": active_vision_model,
                    "raw_json": raw_vision_json,
                    "timings": timings,
                }

            print(f"[classifier] full payload - primary_issue={vision_payload.get('primary_issue','')!r}  setting={vision_payload.get('setting','')!r}")

            description = str(vision_payload.get("description", ""))

            # Guard: if description is empty, looks like raw JSON/binary, or is
            # too short to be meaningful, reconstruct it from other available fields.
            # The vision model (qwen2.5vl:3b) occasionally returns JSON that has
            # no "description" key, or puts binary/garbage data there.
            def _description_is_garbage(d: str) -> bool:
                d = d.strip()
                if not d or len(d) < 10:
                    return True
                if d.startswith("{") or d.startswith("["):
                    return True
                # Detect sequences that look like binary / function tokens
                if re.search(r"\bfunction\s+\d+\b", d, re.IGNORECASE):
                    return True
                # Pure numeric / hex garbage
                if re.fullmatch(r"[\d\s:,{}\[\]\"']+", d):
                    return True
                return False

            if _description_is_garbage(description):
                parts: list[str] = []
                primary = str(vision_payload.get("primary_issue", "")).strip()
                if primary:
                    parts.append(primary.capitalize())
                objects = vision_payload.get("visible_objects", [])
                if objects:
                    parts.append(f"visible objects: {', '.join(str(o) for o in objects[:4])}")
                setting = str(vision_payload.get("setting", "")).strip()
                if setting:
                    parts.append(f"setting: {setting}")
                secondary = str(vision_payload.get("secondary_issue", "")).strip()
                if secondary:
                    parts.append(secondary)
                description = ". ".join(parts) if parts else ""
                if description:
                    vision_payload["description"] = description
                    print(f"[classifier] rebuilt description from structured fields: {description[:80]}")
                else:
                    print(f"[classifier] WARNING: vision model returned uninterpretable output - description left empty")
                    _vision_was_garbage = True

            print(f"[classifier] vision ({active_vision_model}): {description[:120]}")

            # ------------------------------------------------------------------
            # STEP 2 — Rule Engine: Deterministic classification (zero VRAM)
            # ------------------------------------------------------------------
            rule_start = time.perf_counter()
            rule_result = classify_by_rules(vision_payload)
            timings["rule_engine_ms"] = round((time.perf_counter() - rule_start) * 1000.0, 2)
            canonical = rule_result["category"]
            model_confidence = rule_result["confidence"]
            method = rule_result["method"]
            rationale = f"top_score={rule_result['scores'].get(canonical, 0):.1f}"
            is_ambiguous = rule_result["is_ambiguous"]

            print(f"[classifier] rule_engine: {canonical} "
                  f"(conf={model_confidence:.2f}, ambiguous={is_ambiguous})")

            has_traffic_terms = any(t in _all_payload_text for t in _TRAFFIC_TERMS)
            has_vehicle_terms = any(v in _all_payload_text for v in _VEHICLE_TERMS)
            has_electrical_terms = any(e in _all_payload_text for e in _ELECTRICAL_TERMS)
            has_fire_terms = any(f in _all_payload_text for f in _FIRE_TERMS)
            has_electrical_fire_hazard = has_electrical_terms and has_fire_terms

            if has_electrical_fire_hazard and canonical in ("Enforcement", "Uncategorized", "Civil Department"):
                print(
                    "[classifier] ELECTRICAL-FIRE override: electrical + fire cues present "
                    f"- overriding {canonical} -> Electrical Department"
                )
                canonical = "Electrical Department"
                method = "electrical_fire_guard"
                model_confidence = max(model_confidence, 0.9)
                rationale = "electrical and fire hazard cues detected in vision payload"
                is_ambiguous = False

            # ------------------------------------------------------------------
            # TRAFFIC VETO: "traffic congestion" (or similar congestion
            # phrases) alone is not sufficient evidence — a crowded railway
            # platform, festival crowd, or busy market also "looks congested".
            # Require at least ONE vehicle term anywhere in the combined payload.
            # If absent, override to Uncategorized so keyword fallback / vision
            # retry can re-evaluate without expensive reasoning hops.
            # ------------------------------------------------------------------
            if canonical == "Enforcement" and has_traffic_terms and not has_vehicle_terms:
                print(f"[classifier] Traffic VETO: congestion terms found but no vehicle terms "
                        f"- overriding to Uncategorized (was conf={model_confidence:.2f})")
                if has_electrical_fire_hazard:
                    canonical = "Electrical Department"
                    method = "electrical_fire_guard"
                    model_confidence = max(model_confidence, 0.9)
                    rationale = "traffic mention suppressed: no vehicles, electrical fire hazard present"
                    is_ambiguous = False
                else:
                    canonical = "Uncategorized"
                    # Traffic hallucination without vehicle evidence is usually
                    # not improved by reasoning; prefer faster fallback/retry path.
                    is_ambiguous = False
                    model_confidence = 0.3

            # ------------------------------------------------------------------
            # STEP 3 — Optional Reasoning: Only if rule engine is ambiguous
            #          Skipped entirely when RULE_ENGINE_ONLY=true
            # ------------------------------------------------------------------
            raw_json_str = raw_vision_json  # default audit trail

            if _vision_was_garbage:
                print(f"[classifier] SKIPPING reasoning - vision was garbage, reasoning will hallucinate")
                is_ambiguous = False   # prevent reasoning, let retry handle it

            if (
                is_ambiguous
                and canonical != "Uncategorized"
                and settings.reasoning_model
                and not settings.rule_engine_only
            ):
                print(f"[classifier] ambiguous -> invoking {settings.reasoning_model}")
                reasoning_start = time.perf_counter()
                # Unload vision model before loading reasoning model to stay within VRAM budget
                self._unload_model(settings.vision_model)
                categories_block = "\n".join(
                    f"- {cat}: {CATEGORY_DEFINITIONS[cat]}"
                    for cat in CANONICAL_CATEGORIES
                )

                reasoning_response = client.generate(
                    model=settings.reasoning_model,
                    format="json",
                    options={"num_ctx": 1024, "temperature": 0.0},
                    prompt=(
                        f"You are a civic complaint classifier for Indian municipal authorities.\n\n"
                        f"Image description: \"{description}\"\n"
                        f"Visible objects: {json.dumps(vision_payload.get('visible_objects', []))}\n"
                        f"Primary issue: \"{vision_payload.get('primary_issue', '')}\"\n"
                        f"Setting: \"{vision_payload.get('setting', '')}\"\n"
                        f"Hazards: {json.dumps(vision_payload.get('hazards', []))}\n\n"
                        f"NOTE: If the setting is a railway station, train platform, or metro station, "
                        f"classify as 'Uncategorized' — those are Central Government issues outside this portal's scope.\n\n"
                        f"Categories:\n{categories_block}\n\n"
                        f"Respond with JSON: "
                        f"{{\"department\": \"<exact category name>\", "
                        f"\"confidence\": <0.0-1.0>, \"rationale\": \"<brief reason>\"}}"
                    ),
                )
                raw_json_str = reasoning_response["response"].strip()

                try:
                    parsed = json.loads(raw_json_str)
                    reasoning_label = str(parsed.get("department", "Uncategorized"))
                    reasoning_conf = float(parsed.get("confidence", 0.5))
                    rationale = str(parsed.get("rationale", ""))
                except (json.JSONDecodeError, ValueError, TypeError):
                    reasoning_label = raw_json_str
                    reasoning_conf = 0.5
                    rationale = ""

                reasoning_canonical = canonicalize_label(reasoning_label)

                print(f"[classifier] reasoning returned: label={reasoning_label!r}, "
                      f"canonical={reasoning_canonical!r}, conf={reasoning_conf}")

                # Use reasoning result if it's more confident than rule engine
                if reasoning_canonical != "Uncategorized" or canonical == "Uncategorized":
                    canonical = reasoning_canonical
                    model_confidence = reasoning_conf
                    method = "reasoning"

                print(f"[classifier] after reasoning: canonical={canonical!r}")

                # Unload reasoning model to free VRAM after use
                if settings.unload_after_reasoning:
                    self._unload_model(settings.reasoning_model)

                timings["reasoning_ms"] = round((time.perf_counter() - reasoning_start) * 1000.0, 2)

            # Final fallback: keyword scan if still Uncategorized
            if canonical == "Uncategorized":
                keyword_result = _keyword_fallback(
                    _payload_text_for_keyword_fallback(vision_payload)
                )
                if keyword_result != "Uncategorized":
                    canonical = keyword_result
                    method = "keyword_fallback"
                    model_confidence = min(model_confidence, 0.65)

            # ------------------------------------------------------------------
            # STEP 4 — Vision Retry: If still Uncategorized and there is an
            #          alternate vision model we haven't tried yet, unload the
            #          current model and get a second opinion.  A different
            #          model often describes the same scene differently, which
            #          lets the rule engine / keyword fallback succeed.
            # ------------------------------------------------------------------
            print(f"[classifier] pre-retry check: canonical={canonical!r}, "
                  f"_retry_used={_retry_used}, active_model={active_vision_model!r}, "
                  f"chain={_full_chain}")
            if (canonical == "Uncategorized" or _vision_was_garbage) and not _retry_used:
                _retry_used = True
                # Retry only within the RAM-safe tier chain already chosen above.
                # If selector started at mid/fallback, do not jump back up to a
                # heavier model (e.g. granite -> qwen), which hurts latency.
                _alternate_models = [
                    m for m in models_to_try
                    if m and m != active_vision_model
                ]
                print(f"[classifier] alternate_models={_alternate_models}")
                if _alternate_models:
                    alt_model = _alternate_models[0]
                    print(f"[classifier] still Uncategorized after all steps - "
                          f"retrying with alternate vision model: {alt_model}")
                    self._unload_model(active_vision_model)

                    try:
                        _pool2 = ThreadPoolExecutor(max_workers=1)
                        try:
                            future2 = _pool2.submit(
                                client.generate, **_build_kwargs(alt_model)
                            )
                            alt_response = future2.result(timeout=timeout_secs)
                        except _FuturesTimeout:
                            _pool2.shutdown(wait=False, cancel_futures=True)
                            raise
                        finally:
                            try:
                                _pool2.shutdown(wait=False)
                            except Exception:
                                pass

                        alt_raw = alt_response["response"].strip()
                        if alt_raw:
                            if alt_model in _json_capable:
                                try:
                                    alt_payload = json.loads(alt_raw)
                                except json.JSONDecodeError:
                                    alt_payload = parse_vision_text_to_payload(alt_raw)
                            else:
                                alt_payload = parse_vision_text_to_payload(alt_raw)

                            alt_payload.setdefault("description", "")
                            alt_payload.setdefault("visible_objects", [])
                            alt_payload.setdefault("primary_issue", "")
                            alt_payload.setdefault("secondary_issue", "")
                            alt_payload.setdefault("hazards", [])
                            alt_payload.setdefault("setting", "")
                            alt_payload = _clean_vision_payload(alt_payload)

                            alt_desc = str(alt_payload.get("description", ""))
                            print(f"[classifier] alt vision ({alt_model}): {alt_desc[:120]}")

                            # Re-run rule engine on the alternate description
                            alt_rule = classify_by_rules(alt_payload)
                            alt_canonical = alt_rule["category"]
                            print(f"[classifier] alt rule_engine: {alt_canonical} "
                                  f"(conf={alt_rule['confidence']:.2f})")

                            if alt_canonical != "Uncategorized":
                                canonical = alt_canonical
                                model_confidence = alt_rule["confidence"]
                                method = f"vision_retry_{alt_rule['method']}"
                                description = alt_desc or description
                                vision_payload = alt_payload
                                raw_json_str = alt_raw
                                active_vision_model = alt_model
                                rationale = f"retry_top_score={alt_rule['scores'].get(alt_canonical, 0):.1f}"
                            else:
                                # Try keyword fallback on the alt description
                                alt_kw = _keyword_fallback(
                                    _payload_text_for_keyword_fallback(alt_payload)
                                )
                                if alt_kw != "Uncategorized":
                                    canonical = alt_kw
                                    method = "vision_retry_keyword"
                                    model_confidence = 0.60
                                    description = alt_desc or description
                                    vision_payload = alt_payload
                                    raw_json_str = alt_raw
                                    active_vision_model = alt_model
                                    print(f"[classifier] alt keyword fallback: {alt_kw}")
                    except Exception as retry_err:
                        print(f"[classifier] vision retry failed ({retry_err}), "
                              f"keeping Uncategorized")

            # Determine validity
            is_non_civic = _is_non_civic_text(description)
            is_valid = (canonical != "Uncategorized") and not is_non_civic

            return {
                "department": canonical,
                "label": description,
                "confidence": model_confidence if is_valid else max(model_confidence * 0.5, 0.1),
                "is_valid": is_valid,
                "is_non_civic": is_non_civic,
                "vision_description": description,
                "vision_payload": vision_payload,
                "raw_category": canonical,
                "rationale": rationale,
                "method": method,
                "model_used": active_vision_model,
                "raw_json": raw_json_str,
                "timings": timings,
            }

        except Exception as e:
            print(f"Classification Error: {e}")
            return {
                "department": "Unknown",
                "label": "Could not classify image",
                "confidence": 0.0,
                "is_valid": False,
                "is_non_civic": False,
                "error": "classification_failed",
                "method": "error",
                "rationale": "",
                "raw_json": "",
                "timings": timings,
            }
        finally:
            ollama_lock.release()
