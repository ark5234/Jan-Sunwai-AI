import io
import json
import os
import ollama
from PIL import Image
from app.config import settings
from app.category_utils import CANONICAL_CATEGORIES, canonicalize_label
from app.rule_engine import classify_by_rules, parse_vision_text_to_payload

# Use an explicit client so the host URL comes from OLLAMA_BASE_URL config
# (the module-level ollama.generate() defaults to localhost:11434 which
# breaks inside Docker where localhost = the container, not the host).
def _get_ollama_client() -> ollama.Client:
    return ollama.Client(host=settings.ollama_base_url)

# Human-readable definitions passed to the reasoning model so it can
# make a contextual decision rather than just matching a string.
CATEGORY_DEFINITIONS: dict[str, str] = {
    "Municipal - PWD (Roads)":         "broken roads, potholes, cracked pavement, damaged footpaths, bridge damage",
    "Municipal - Sanitation":          "garbage dumps, overflowing trash bins, dirty public toilets, waste piles on streets",
    "Municipal - Horticulture":        "fallen or uprooted trees, overgrown vegetation, unmaintained parks, dead/dry plants",
    "Municipal - Street Lighting":     "broken street lights, non-functional lamp posts, dark or unlit public roads",
    "Municipal - Water & Sewerage":    "waterlogging, flooded streets, blocked drains, sewer overflow, water pipe leaks",
    "Utility - Power (DISCOM)":        "dangling electrical wires, open or damaged transformers, hazardous power cables",
    "State Transport":                 "damaged bus shelters, broken state buses, transport terminal damage",
    "Pollution Control Board":         "air pollution, thick smoke, industrial waste dumping, open burning of garbage",
    "Police - Local Law Enforcement":  "illegal parking, footpath encroachment, public nuisance, fights or brawls",
    "Police - Traffic":                "failed traffic signals, road blockages, severe traffic congestion",
    "Uncategorized":                   "does not clearly match any of the above civic categories",
}

# Keywords that indicate a non-civic / irrelevant photo
_NEGATIVE_KEYWORDS = [
    "selfie", "portrait", "food", "meal", "restaurant", "cartoon", "anime",
    "gaming", "screenshot", "indoor furniture", "appliance", "pet", "animal",
    "beautiful landscape", "clear sky",
]

# Keyword fallback: if reasoning model fails, map description keywords → category
# Ordered from most-specific to least-specific
_KEYWORD_FALLBACK: list[tuple[list[str], str]] = [
    (["pothole", "road damage", "cracked road", "broken road", "damaged road",
      "damaged pavement", "broken pavement", "footpath damage", "manhole"],
     "Municipal - PWD (Roads)"),
    (["waterlog", "flooded", "flood", "drain overflow", "sewer overflow",
      "pipe leak", "water gushing", "stagnant water", "blocked drain",
      "drainage problem"],
     "Municipal - Water & Sewerage"),
    (["garbage", "trash", "waste", "litter", "dump", "rubbish", "overflowing bin"],
     "Municipal - Sanitation"),
    (["fallen tree", "uprooted tree", "overgrown", "dead plant", "broken branch",
      "tree blocking"],
     "Municipal - Horticulture"),
    (["street light", "lamp post", "unlit road", "broken light", "dark road"],
     "Municipal - Street Lighting"),
    (["dangling wire", "hanging wire", "open transformer", "fallen electric pole",
      "exposed wire", "power cable"],
     "Utility - Power (DISCOM)"),
    (["smoke", "burning", "industrial waste", "air pollution", "open burning"],
     "Pollution Control Board"),
    (["traffic signal", "signal failure", "traffic jam", "road blockage"],
     "Police - Traffic"),
    (["illegal parking", "encroachment", "footpath blocked", "public nuisance"],
     "Police - Local Law Enforcement"),
    (["bus shelter", "state bus", "transport terminal"],
     "State Transport"),
]


def _keyword_fallback(description: str) -> str:
    """Scan the vision description for civic keywords and return best category."""
    desc = description.lower()
    for keywords, category in _KEYWORD_FALLBACK:
        if any(kw in desc for kw in keywords):
            return category
    return "Uncategorized"


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

    def classify(self, image_path: str) -> dict:
        if not os.path.exists(image_path):
            return {
                "department": "Unknown",
                "label": "Image file not found",
                "confidence": 0.0,
                "is_valid": False,
                "method": "error",
                "rationale": "file not found",
                "raw_json": "",
            }

        try:
            image_bytes = _load_image_as_jpeg_bytes(image_path)
            client = _get_ollama_client()

            # ------------------------------------------------------------------
            # STEP 1 — Vision: Structured JSON description (qwen2.5vl:3b)
            # ------------------------------------------------------------------
            vision_response = client.generate(
                model=settings.vision_model,
                format="json",
                prompt=(
                    "You are a civic-issue vision analyst for Indian municipal complaints. "
                    "Analyze the image and return strict JSON only.\n\n"
                    "JSON schema:\n"
                    "{\n"
                    '  "description": "2-3 sentence factual description of what you see",\n'
                    '  "visible_objects": ["object1", "object2"],\n'
                    '  "primary_issue": "single phrase describing the main problem",\n'
                    '  "secondary_issue": "single phrase or empty string",\n'
                    '  "hazards": ["hazard1", "hazard2"],\n'
                    '  "setting": "road/park/drain/building/etc",\n'
                    '  "confidence": "low/medium/high"\n'
                    "}\n\n"
                    "Rules:\n"
                    "- Keep description under 40 words\n"
                    "- Be specific about damage type (pothole, crack, leak, etc.)\n"
                    "- List all visible hazards\n"
                    "- No markdown, no explanation outside JSON"
                ),
                images=[image_bytes],
                options={"num_ctx": 1024},
            )
            raw_vision_json: str = vision_response["response"].strip()

            # Parse the structured vision output
            try:
                vision_payload = json.loads(raw_vision_json)
            except json.JSONDecodeError:
                # Fallback: treat raw output as plain description
                vision_payload = parse_vision_text_to_payload(raw_vision_json)

            # Ensure all expected keys exist
            vision_payload.setdefault("description", "")
            vision_payload.setdefault("visible_objects", [])
            vision_payload.setdefault("primary_issue", "")
            vision_payload.setdefault("secondary_issue", "")
            vision_payload.setdefault("hazards", [])
            vision_payload.setdefault("setting", "")

            description = str(vision_payload.get("description", ""))

            # ------------------------------------------------------------------
            # STEP 2 — Rule Engine: Deterministic classification (zero VRAM)
            # ------------------------------------------------------------------
            rule_result = classify_by_rules(vision_payload)
            canonical = rule_result["category"]
            model_confidence = rule_result["confidence"]
            method = rule_result["method"]
            rationale = f"top_score={rule_result['scores'].get(canonical, 0):.1f}"
            is_ambiguous = rule_result["is_ambiguous"]

            print(f"[classifier] rule_engine: {canonical} "
                  f"(conf={model_confidence:.2f}, ambiguous={is_ambiguous})")

            # ------------------------------------------------------------------
            # STEP 3 — Optional Reasoning: Only if rule engine is ambiguous
            #          Skipped entirely when RULE_ENGINE_ONLY=true
            # ------------------------------------------------------------------
            raw_json_str = raw_vision_json  # default audit trail

            if is_ambiguous and settings.reasoning_model and not settings.rule_engine_only:
                print(f"[classifier] ambiguous → invoking {settings.reasoning_model}")
                # Unload vision model before loading reasoning model to stay within VRAM budget
                self._unload_model(settings.vision_model)
                categories_block = "\n".join(
                    f"- {cat}: {CATEGORY_DEFINITIONS[cat]}"
                    for cat in CANONICAL_CATEGORIES
                )

                reasoning_response = client.generate(
                    model=settings.reasoning_model,
                    format="json",
                    options={"num_ctx": 1024},
                    prompt=(
                        f"You are a civic complaint classifier for Indian municipal authorities.\n\n"
                        f"Image description: \"{description}\"\n"
                        f"Visible objects: {json.dumps(vision_payload.get('visible_objects', []))}\n"
                        f"Primary issue: \"{vision_payload.get('primary_issue', '')}\"\n"
                        f"Hazards: {json.dumps(vision_payload.get('hazards', []))}\n\n"
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

                # Use reasoning result if it's more confident than rule engine
                if reasoning_canonical != "Uncategorized" or canonical == "Uncategorized":
                    canonical = reasoning_canonical
                    model_confidence = reasoning_conf
                    method = "reasoning"

                # Unload reasoning model to free VRAM after use
                if settings.unload_after_reasoning:
                    self._unload_model(settings.reasoning_model)

            # Final fallback: keyword scan if still Uncategorized
            if canonical == "Uncategorized":
                keyword_result = _keyword_fallback(description)
                if keyword_result != "Uncategorized":
                    canonical = keyword_result
                    method = "keyword_fallback"
                    model_confidence = min(model_confidence, 0.65)

            # Determine validity
            desc_lower = description.lower()
            is_non_civic = any(kw in desc_lower for kw in _NEGATIVE_KEYWORDS)
            is_valid = (canonical != "Uncategorized") and not is_non_civic

            return {
                "department": canonical,
                "label": description,
                "confidence": model_confidence if is_valid else max(model_confidence * 0.5, 0.1),
                "is_valid": is_valid,
                "vision_description": description,
                "vision_payload": vision_payload,
                "raw_category": canonical,
                "rationale": rationale,
                "method": method,
                "model_used": settings.vision_model,
                "raw_json": raw_json_str,
            }

        except Exception as e:
            print(f"Classification Error: {e}")
            return {
                "department": "Unknown",
                "label": "Could not classify image",
                "confidence": 0.0,
                "is_valid": False,
                "error": str(e),
                "method": "error",
                "rationale": "",
                "raw_json": "",
            }

