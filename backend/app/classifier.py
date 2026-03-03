import io
import json
import os
import re
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
    "Municipal - PWD (Roads)":         "broken roads, potholes, cracked pavement, damaged footpaths, bridge damage",
    "Municipal - Sanitation":          "garbage dumps, overflowing trash bins, dirty public toilets, waste piles on streets",
    "Municipal - Horticulture":        "fallen or uprooted trees, overgrown vegetation, unmaintained parks, dead/dry plants",
    "Municipal - Street Lighting":     "broken street lights, non-functional lamp posts, dark or unlit public roads",
    "Municipal - Water & Sewerage":    "waterlogging, flooded streets, blocked drains, sewer overflow, water pipe leaks",
    "Utility - Power (DISCOM)":        "dangling electrical wires, open or damaged transformers, hazardous power cables",
    "State Transport":                 "damaged bus shelters, broken state road buses, bus terminal damage — bus/road transport ONLY, does NOT include railway stations or trains",
    "Pollution Control Board":         "air pollution, thick smoke, industrial waste dumping, open burning of garbage",
    "Police - Local Law Enforcement":  "illegal parking, footpath encroachment, public nuisance, fights or brawls",
    "Police - Traffic":                "failed traffic signals, road blockages, severe traffic congestion, traffic deadlock, gridlock, chaotic traffic, peak-hour jams, no lane marking, uncontrolled intersections, crowded marketplace roads",
    "Uncategorized":                   "does not clearly match any of the above civic categories",
}

# Keywords that indicate a non-civic / irrelevant photo
_NEGATIVE_KEYWORDS = [
    "selfie", "portrait", "food", "meal", "restaurant", "cartoon", "anime",
    "gaming", "screenshot", "indoor furniture", "appliance", "pet", "animal",
    "beautiful landscape", "clear sky",
    # Indian Railways is Central Government — not in scope for this portal
    "railway station", "train station", "railway platform", "train platform",
    "railway track", "train track", "metro station",
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
    (["garbage", "trash", "waste", "litter", "dump", "rubbish", "overflowing bin",
      "pile of", "large pile", "heap of", "plastic bottles", "plastic bottle",
      "glass bottles", "broken glass", "broken bottles", "empty bottles",
      "scattered", "junk", "filth", "filthy", "open dump", "roadside dump"],
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
    (["traffic signal", "signal failure", "traffic jam", "road blockage",
      "traffic congestion", "gridlock", "traffic deadlock",
      "standstill", "peak hour", "rush hour", "no lane", "chaotic traffic"],
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
                "- If you see a train, railway platform, or railway station, say so EXPLICITLY "
                "in the description — do NOT describe a railway platform as a 'sidewalk' or 'road'.\n"
                "- If the dominant scene is heavy vehicle traffic, crowded roads, traffic jam, "
                "or congestion with NO clear infrastructure damage, set primary_issue to "
                "'traffic congestion' and description should reflect that.\n"
                "- Do NOT mention potholes unless you can clearly see road surface damage.\n"
                "- Do NOT mention garbage/fallen trees unless clearly visible.\n"
                "- Be specific: 'traffic congestion' / 'pothole' / 'waterlogging' / "
                "'broken street light' / 'fallen tree' / 'garbage dump' / 'dangling wire' / "
                "'railway platform' / 'train station'\n"
                "- Keep description under 40 words\n"
                "- No markdown, no explanation outside JSON"
            )
            _simple_prompt = (
                "Look at this image carefully and describe ONLY what you can clearly see. "
                "What is the main activity or condition visible in the scene? "
                "How many vehicles or people are present? "
                "Is there any obvious physical damage to roads, infrastructure, or surroundings? "
                "Describe in 2-3 factual sentences without guessing or assuming."
            )

            def _build_kwargs(model_name: str) -> dict:
                if model_name in _json_capable:
                    return dict(
                        model=model_name,
                        format="json",
                        prompt=_json_prompt,
                        images=[image_bytes],
                        options={"num_ctx": 1024},
                    )
                return dict(model=model_name, prompt=_simple_prompt, images=[image_bytes])

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
                              f"→ unloading and trying next tier: {next_tier}")
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
                              f"→ falling back to {next_tier}")
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

            _RAIL_TRANSIT_TERMS = [
                "train", "railway", "railroad", "locomotive",
                "railway station", "train station", "railway platform",
                "train platform", "metro station", "station platform",
                "rail track", "railway track", "train track",
            ]
            if any(term in _all_payload_text for term in _RAIL_TRANSIT_TERMS):
                print(f"[classifier] non-civic scene detected (rail/transit) in payload — returning Uncategorized")
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
                }

            print(f"[classifier] full payload — primary_issue={vision_payload.get('primary_issue','')!r}  setting={vision_payload.get('setting','')!r}")

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
                    print(f"[classifier] WARNING: vision model returned uninterpretable output — description left empty")
                    _vision_was_garbage = True

            print(f"[classifier] vision ({active_vision_model}): {description[:120]}")

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
            # POLICE-TRAFFIC VETO: "traffic congestion" (or similar congestion
            # phrases) alone is not sufficient evidence — a crowded railway
            # platform, festival crowd, or busy market also "looks congested".
            # Require at least ONE vehicle term anywhere in the combined payload.
            # If absent, override to Uncategorized so the reasoning model (or
            # the keyword fallback) gets a chance to re-evaluate.
            # ------------------------------------------------------------------
            if canonical == "Police - Traffic":
                _VEHICLE_TERMS = [
                    "car", "cars", "vehicle", "vehicles", "bus", "buses",
                    "truck", "trucks", "motorcycle", "motorcycles", "auto",
                    "autorickshaw", "rickshaw", "two-wheeler", "scooter",
                    "cab", "taxi", "van", "jeep", "lorry", "minibus",
                ]
                has_vehicle = any(v in _all_payload_text for v in _VEHICLE_TERMS)
                if not has_vehicle:
                    print(f"[classifier] Police-Traffic VETO: no vehicle terms in payload "
                          f"— overriding to Uncategorized (was conf={model_confidence:.2f})")
                    canonical = "Uncategorized"
                    is_ambiguous = True          # allow reasoning model to re-classify
                    model_confidence = 0.3

            # ------------------------------------------------------------------
            # STEP 3 — Optional Reasoning: Only if rule engine is ambiguous
            #          Skipped entirely when RULE_ENGINE_ONLY=true
            # ------------------------------------------------------------------
            raw_json_str = raw_vision_json  # default audit trail

            if _vision_was_garbage:
                print(f"[classifier] SKIPPING reasoning — vision was garbage, reasoning will hallucinate")
                is_ambiguous = False   # prevent reasoning, let retry handle it

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

            # Final fallback: keyword scan if still Uncategorized
            if canonical == "Uncategorized":
                keyword_result = _keyword_fallback(description)
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
                _alternate_models = [
                    m for m in _full_chain
                    if m and m != active_vision_model
                ]
                print(f"[classifier] alternate_models={_alternate_models}")
                if _alternate_models:
                    alt_model = _alternate_models[0]
                    print(f"[classifier] still Uncategorized after all steps — "
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
                                alt_kw = _keyword_fallback(alt_desc)
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
            desc_lower = description.lower()
            is_non_civic = any(kw in desc_lower for kw in _NEGATIVE_KEYWORDS)
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
            }

        except Exception as e:
            print(f"Classification Error: {e}")
            return {
                "department": "Unknown",
                "label": "Could not classify image",
                "confidence": 0.0,
                "is_valid": False,
                "is_non_civic": False,
                "error": str(e),
                "method": "error",
                "rationale": "",
                "raw_json": "",
            }
        finally:
            ollama_lock.release()
