import ollama
import os
import re
import time
from app.config import settings
from app.llm_lock import ollama_lock

# deep-translator language codes for Indian languages
# GoogleTranslator uses BCP-47 / ISO 639-1 codes matching what we already store.
_GOOGLE_LANG_MAP = {
    "hi": "hi",  # Hindi
    "mr": "mr",  # Marathi
    "ta": "ta",  # Tamil
    "te": "te",  # Telugu
    "kn": "kn",  # Kannada
    "bn": "bn",  # Bengali
    "gu": "gu",  # Gujarati
}

_TARGET_COMPLAINT_WORDS = 67
_TARGET_MIN_WORDS = 62
_TARGET_MAX_WORDS = 72
_BAD_TRAILING_WORDS = {
    "a", "an", "the", "and", "or", "of", "to", "from", "with",
    "in", "on", "for", "by", "as", "at", "is", "are", "was", "were",
}
_UNKNOWN_LOCATION_MARKERS = (
    "not specified",
    "not available",
    "unknown",
    "unavailable",
    "cannot be determined",
    "metadata",
)

_LOW_INFO_HINTS = (
    "possibly",
    "maybe",
    "appears to be",
    "seems to be",
    "looks like",
    "object",
    "circular shape",
    "machinery",
    "equipment",
)

_CONCRETE_CIVIC_HINTS = (
    "fire", "flame", "smoke", "spark", "wire", "transformer", "panel",
    "tree", "branch", "pothole", "drain", "garbage", "street light",
    "waterlogging", "encroachment", "traffic", "sewage", "leak",
)

_COMPLAINT_OUTPUT_MODES = {"paragraph", "email"}


def _normalize_text(text: str) -> str:
    out = " ".join(text.split())
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    out = re.sub(r"\.{2,}", ".", out)
    return out


def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _split_sentences(text: str) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def _is_unknown_location(address: str) -> bool:
    raw = (address or "").strip().lower()
    if not raw:
        return True
    return any(marker in raw for marker in _UNKNOWN_LOCATION_MARKERS)


def _issue_phrase_from_text(text: str) -> str:
    out = _normalize_text(text)
    out = re.sub(r"^(?:the|this)?\s*image\s+(?:shows|depicts|contains|captures)\s+", "", out, flags=re.IGNORECASE)
    out = re.sub(r"^a\s+close-?up\s+of\s+", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\b(?:this situation|this condition)\s+poses\b.*$", "", out, flags=re.IGNORECASE)
    out = re.sub(
        r"\b(?:appears?|is\s+visible|is\s+seen|can\s+be\s+seen)\s+in\s+the\s+"
        r"(?:foreground|background|attached\s+image)\b.*$",
        "",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\b(?:in|of)\s+the\s+attached\s+image\b.*$", "", out, flags=re.IGNORECASE)

    sentences = _split_sentences(out)
    phrase = sentences[0] if sentences else out
    words = _tokenize_words(phrase)
    if len(words) > 26:
        phrase = " ".join(words[:26]).rstrip(",;:-")

    phrase = phrase.strip().rstrip(".")
    if not phrase:
        return "a potentially hazardous civic condition"
    return phrase


def _is_low_information_issue(text: str) -> bool:
    t = _normalize_text(text).lower()
    if not t:
        return True
    has_low_info_hint = any(h in t for h in _LOW_INFO_HINTS)
    has_concrete_hint = any(h in t for h in _CONCRETE_CIVIC_HINTS)
    return has_low_info_hint and not has_concrete_hint


def _department_issue_fallback(category: str) -> str:
    c = (category or "").lower()
    if any(k in c for k in ["fire", "rescue"]):
        return "a visible fire-related hazard in a public area"
    if any(k in c for k in ["electrical", "power", "discom"]):
        return "an unsafe electrical condition involving exposed or damaged components"
    if any(k in c for k in ["street lighting", "lighting"]):
        return "a non-functional or unsafe street-lighting condition"
    if any(k in c for k in ["road", "pwd", "civil", "pothole"]):
        return "a damaged road or public infrastructure condition"
    if any(k in c for k in ["horticulture", "park", "garden", "tree"]):
        return "an unsafe horticulture-related condition in a public green area"
    if any(k in c for k in ["enforcement", "traffic", "police"]):
        return "an obstruction or enforcement-related safety issue in public space"
    if any(k in c for k in ["health", "sanitation", "waste"]):
        return "an unhygienic sanitation condition affecting public health"
    return "an unsafe civic condition requiring immediate attention"


def _refine_issue_phrase(issue_text: str, category: str) -> str:
    phrase = _issue_phrase_from_text(issue_text)
    phrase = re.sub(r"\b(?:possibly|maybe|likely|appears to be|seems to be|looks like)\b", "", phrase, flags=re.IGNORECASE)
    phrase = _normalize_text(phrase).strip().rstrip(".,;:-")

    if _is_low_information_issue(phrase):
        return _department_issue_fallback(category)
    return phrase


def _department_risk_hint(category: str) -> str:
    c = (category or "").lower()
    if any(k in c for k in ["fire", "flame", "rescue"]):
        return "fire spread, injury, and property damage"
    if any(k in c for k in ["electrical", "power", "discom"]):
        return "electrocution, fire, and power disruption"
    if any(k in c for k in ["street lighting", "lighting"]):
        return "low visibility, safety threats, and avoidable accidents"
    if any(k in c for k in ["road", "pwd", "pothole"]):
        return "road accidents, vehicle damage, and commuter risk"
    if any(k in c for k in ["horticulture", "park", "garden", "tree"]):
        return "falling branches, obstruction of movement, and injury to pedestrians"
    if any(k in c for k in ["enforcement", "traffic", "police"]):
        return "traffic obstruction, unsafe movement, and collision risk"
    if any(k in c for k in ["water", "drain", "sewer"]):
        return "water contamination, sanitation concerns, and health risk"
    return "injury to citizens, disruption of civic services, and avoidable local damage"


def _department_action_hint(category: str) -> str:
    c = (category or "").lower()
    if any(k in c for k in ["fire", "flame", "rescue"]):
        return "Kindly deploy emergency response, secure the affected area, and neutralize the hazard"
    if any(k in c for k in ["electrical", "power", "discom"]):
        return "Kindly de-energize unsafe lines where required, rectify the electrical fault, and make the site safe"
    if any(k in c for k in ["street lighting", "lighting"]):
        return "Kindly restore lighting functionality and complete necessary repairs to ensure safe night-time movement"
    if any(k in c for k in ["road", "pwd", "civil", "pothole"]):
        return "Kindly inspect the site, carry out durable repairs, and restore safe public movement"
    if any(k in c for k in ["horticulture", "park", "garden", "tree"]):
        return "Kindly inspect the area, remove the immediate hazard, and complete horticulture maintenance without delay"
    if any(k in c for k in ["enforcement", "traffic", "police"]):
        return "Kindly conduct immediate on-ground enforcement, clear the obstruction, and restore orderly movement"
    if any(k in c for k in ["health", "sanitation", "waste"]):
        return "Kindly arrange immediate sanitation action, remove the source of nuisance, and disinfect the affected area"
    return "Kindly arrange immediate inspection and corrective action"


def _compact_location(address: str, max_words: int = 12) -> str:
    words = _tokenize_words(_normalize_text(address or ""))
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",;:-")


def _salutation_department(category: str) -> str:
    dep = (category or "").strip()
    if not dep:
        return "Concerned Department"
    dep_lower = dep.lower()
    if dep_lower.endswith("department") or dep_lower.endswith("authority") or dep_lower.endswith("cell"):
        return dep
    return f"{dep} Department"


def _compose_official_mail_text(issue_text: str, category: str, address: str) -> str:
    issue_phrase = _refine_issue_phrase(issue_text, category)
    department = (category or "").strip() or "concerned department"
    salutation_department = _salutation_department(department)
    risk_hint = _department_risk_hint(f"{department} {issue_phrase}")
    action_hint = _department_action_hint(department)

    if _is_unknown_location(address):
        location_line = ""
    else:
        location_line = f"The reported location is {_compact_location(address)}."

    location_part = f"{location_line} " if location_line else ""

    return (
        f"Dear {salutation_department}, the attached image indicates {issue_phrase}. "
        f"{location_part}"
        f"This issue may lead to {risk_hint} if not addressed promptly. "
        f"{action_hint}. "
        "Immediate attention is requested in public interest."
    )


def _compose_structured_email_text(issue_text: str, category: str, address: str) -> str:
    issue_phrase = _refine_issue_phrase(issue_text, category)
    department = (category or "").strip() or "Concerned Department"
    salutation_department = _salutation_department(department)
    risk_hint = _department_risk_hint(f"{department} {issue_phrase}")
    action_hint = _department_action_hint(department).strip().rstrip(". ")

    if _is_unknown_location(address):
        location_sentence = (
            "The exact location could not be confirmed from metadata, "
            "but the attached evidence indicates this issue is within your jurisdiction."
        )
    else:
        location_sentence = f"The specific location requiring attention is {_compact_location(address)}."

    subject_issue = issue_phrase[:1].upper() + issue_phrase[1:] if issue_phrase else "Civic Hazard"

    return (
        f"Subject: Urgent Civic Grievance - Immediate Action Required regarding {subject_issue}\n\n"
        f"Dear {salutation_department},\n\n"
        "I am writing to formally bring to your attention a matter of public concern that requires urgent resolution. "
        f"The attached photographic evidence indicates {issue_phrase}. {location_sentence}\n\n"
        f"If left unaddressed, this issue poses a significant risk of {risk_hint}. "
        f"{action_hint}.\n\n"
        "Your prompt intervention in this matter is requested in the interest of public safety.\n\n"
        "Sincerely,\n"
        "Concerned Citizen"
    )


def _align_with_observed_issue(text: str, observed_issue: str) -> str:
    """
    Remove contradiction-style absence claims when the observed issue itself
    already indicates fire/smoke/sparks.
    """
    out = _normalize_text(text)
    issue = (observed_issue or "").lower()
    issue_has_fire_signal = any(k in issue for k in ["fire", "flame", "flames", "smoke", "burning", "spark", "sparks"])

    if issue_has_fire_signal:
        out = re.sub(
            r"\b(?:with\s+)?(?:there is|there's)?\s*no\s+(?:visible|clear\s+(?:indication|evidence)\s+of)\s+"
            r"(?:fire|smoke)(?:\s+or\s+(?:fire|smoke))?\.?\s*",
            "",
            out,
            flags=re.IGNORECASE,
        )

    # Repair common truncated phrase artifacts from small-model outputs.
    out = re.sub(r"\bcannot be determined from the\.?\b", "cannot be determined from metadata.", out, flags=re.IGNORECASE)

    # Remove common dangling connector left behind after phrase stripping.
    out = re.sub(r"\bin an area with\s+(?=The location\b)", "in the affected area. ", out, flags=re.IGNORECASE)
    out = re.sub(r"\bin an area\s+(?=The location\b)", "in the affected area. ", out, flags=re.IGNORECASE)

    # If phrase removal collapsed words (e.g., "withThe"), restore spacing.
    out = re.sub(r"([a-z])([A-Z])", r"\1 \2", out)

    return _normalize_text(out)


def _fit_to_target_words(text: str, target_words: int = _TARGET_COMPLAINT_WORDS) -> str:
    """
    Normalize a generated paragraph to a tight target range.

    This keeps UI output consistent and aligned with the requested style length.
    """
    sentences = _split_sentences(text)
    words: list[str] = []

    min_words = max(40, target_words - 5)
    max_words = target_words + 5

    # Prefer complete sentences so outputs never end mid-thought.
    used_sentence_count = 0
    if sentences:
        selected: list[str] = []
        used = 0
        for sentence in sentences:
            sentence_words = _tokenize_words(sentence)
            if not sentence_words:
                continue
            if used + len(sentence_words) <= max_words:
                selected.append(sentence)
                used += len(sentence_words)
                used_sentence_count += 1
            else:
                break

        if selected:
            words = _tokenize_words(" ".join(selected))

    if not words:
        words = _tokenize_words(_normalize_text(text))

    if len(words) > max_words:
        words = words[:max_words]
        # Avoid clipped sentence fragments at the boundary.
        while words and words[-1][-1] not in ".!?":
            words.pop()

    # If we're still short and there is an unselected sentence, consume part of it
    # before using generic filler so output stays content-rich.
    if len(words) < min_words and used_sentence_count < len(sentences):
        remaining = min_words - len(words)
        next_sentence_words = _tokenize_words(sentences[used_sentence_count])
        if next_sentence_words:
            take = min(len(next_sentence_words), remaining)
            words.extend(next_sentence_words[:take])
            # Remove awkward trailing stop words after partial sentence copy.
            while words and words[-1].strip(".,;:-").lower() in _BAD_TRAILING_WORDS:
                words.pop()

    if len(words) < min_words:
        filler_chunks: list[list[str]] = [
            ["Immediate", "attention", "is", "requested", "in", "public", "interest."],
            ["Necessary", "corrective", "measures", "may", "kindly", "be", "expedited."],
            ["This", "matter", "may", "please", "be", "treated", "as", "priority."],
            ["An", "early", "compliance", "update", "is", "requested."],
            ["Urgent", "intervention", "is", "solicited."],
            ["Without", "delay."],
            ["Today."],
        ]

        remaining = min_words - len(words)
        filler_idx = 0
        while remaining > 0:
            options = [c for c in filler_chunks if len(c) <= remaining]
            if not options:
                break
            current_text = " ".join(words).lower()
            non_repeating = [
                c for c in options
                if " ".join(c).lower().rstrip(".") not in current_text
            ]
            choose_from = non_repeating if non_repeating else options
            chunk = choose_from[filler_idx % len(choose_from)]
            filler_idx += 1
            words.extend(chunk)
            remaining -= len(chunk)

    # Keep outputs within upper bound if filler pushed us over.
    if len(words) > max_words:
        words = words[:max_words]
        while words and words[-1][-1] not in ".!?":
            words.pop()

    out = _normalize_text(" ".join(words).strip())
    out = out.rstrip(",;:-")
    if out and out[-1] not in ".!?":
        out += "."
    return out


def _translate(text: str, target_lang: str) -> str:
    """
    Translate `text` from English to `target_lang` using deep-translator.
    Falls back to the original English text if translation fails so the
    complaint is never lost.

    Primary:  GoogleTranslator (free, no API key, via unofficial API)
    Fallback: MyMemoryTranslator (free, 10K chars/day, no key)
    """
    google_code = _GOOGLE_LANG_MAP.get(target_lang)
    if not google_code:
        return text  # unsupported language — return as-is

    # Primary: Google Translate
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="en", target=google_code).translate(text)
        if isinstance(translated, str) and translated.strip():
            print(f"[generator] Translated to {target_lang} via GoogleTranslator")
            return translated.strip()
    except Exception as e:
        print(f"[generator] GoogleTranslator failed ({e}), trying MyMemory...")

    # Fallback: MyMemory
    try:
        from deep_translator import MyMemoryTranslator
        translated = MyMemoryTranslator(source="en", target=google_code).translate(text)
        if isinstance(translated, str) and translated.strip():
            print(f"[generator] Translated to {target_lang} via MyMemoryTranslator")
            return translated.strip()
    except Exception as e:
        print(f"[generator] MyMemoryTranslator also failed ({e}), returning English text")

    return text  # both failed — return original English


def _get_loaded_model_names(client: ollama.Client, quiet: bool = False) -> tuple[list[str], bool]:
    """
    Return currently loaded Ollama model names.

    Returns:
        (names, status_known)
    """
    try:
        running = client.ps()
        running_models = running.models if hasattr(running, "models") else running.get("models", [])
        names: list[str] = []
        for m in running_models:
            if hasattr(m, "model"):
                raw_name = m.model
            elif isinstance(m, dict):
                raw_name = m.get("model", "")
            else:
                raw_name = ""
            names.append(raw_name if isinstance(raw_name, str) else str(raw_name or ""))
        return names, True
    except Exception as e:
        if not quiet:
            print(f"[generator] unable to query loaded models ({e}); using blind unload fallback")
        return [], False


def _wait_for_model_unload(client: ollama.Client, model_name: str, timeout: float | None = None) -> None:
    """
    Poll Ollama's running-models list until `model_name` is no longer present
    or `timeout` seconds have elapsed. The keep_alive=0 call is async on the
    Ollama side — without this wait llama3.2:1b starts loading while the vision
    model is still resident, causing OOM or slow generation.
    """
    effective_timeout = timeout if timeout is not None else settings.model_unload_timeout_seconds
    poll_interval = max(settings.model_unload_poll_interval_seconds, 0.05)

    deadline = time.monotonic() + effective_timeout
    while time.monotonic() < deadline:
        names, status_known = _get_loaded_model_names(client, quiet=True)
        if status_known and not any(model_name in n for n in names):
            return
        time.sleep(poll_interval)

    print(
        f"[generator] unload wait timed out for {model_name} after "
        f"{effective_timeout:.1f}s; continuing"
    )


def _effective_output_mode() -> str:
    mode = (settings.complaint_output_mode or "paragraph").strip().lower()
    if mode in _COMPLAINT_OUTPUT_MODES:
        return mode
    return "paragraph"


def generate_complaint(image_path, classification_result, user_details, location_details, language: str = "en"):
    """
    Generates a civic grievance description using the reasoning model (llama3.2:1b).

    Always uses text-only generation — the vision model has already run during
    classification and produced a structured description. Re-running the vision model
    here was the original bottleneck (60–250 s extra per request).
    """

    category = classification_result.get("department") or classification_result.get("label", "Civic Issue")
    description = (
        classification_result.get("vision_description")
        or classification_result.get("label", "")
        or "A civic issue requiring attention"
    )
    address = location_details.get("address", "Location not specified")
    output_mode = _effective_output_mode()

    # ── Step 1: Always generate in English ───────────────────────────────────
    # Small models (1B) cannot reliably generate in Indian scripts.
    # We generate a quality English complaint, then post-translate it.
    if output_mode == "email":
        system_prompt = (
            "You are a formal civic grievance drafter for Indian government portals. "
            "Write highly professional, structured email complaints in plain English."
        )
        prompt = (
            f"Issue observed: {description}\n"
            f"Department: {category}\n"
            f"Location: {address}\n\n"
            "Draft a formal email complaint that includes:\n"
            "1. A clear Subject line.\n"
            "2. A formal salutation ('Dear <Department>,').\n"
            "3. A structured body with issue details, location, and risk.\n"
            "4. A clear action request.\n"
            "5. A formal sign-off ('Sincerely, Concerned Citizen').\n"
            "Rules: no markdown, no bullet points in final draft, "
            "never contradict the observed issue, and do not add absence statements "
            "like 'no visible fire/smoke' unless explicitly stated.\n\n"
            "Draft Email:"
        )
    else:
        system_prompt = (
            "You are a civic complaint drafting assistant for Indian government portals. "
            "Write formal, concise complaint descriptions in plain English."
        )
        prompt = (
            f"Issue observed: {description}\n"
            f"Department: {category}\n"
            f"Location: {address}\n\n"
            f"Write approximately {_TARGET_MIN_WORDS}-{_TARGET_MAX_WORDS} words in a professional official-mail tone as a single paragraph.\n"
            f"Rules: begin with 'Dear <Department>,', no sign-offs, no 'Subject:' line, no bullet points, "
            f"no meta-commentary, no markdown. "
            f"Never contradict the observed issue. "
            f"Do not add absence statements like 'no visible fire/smoke' unless explicitly stated in the observed issue. "
            f"Include: (1) issue observed, (2) risk/impact, (3) location availability status, "
            f"(4) clear action request to the concerned department.\n\n"
            f"Complaint description:"
        )

    with ollama_lock:
        try:
            client = ollama.Client(host=settings.ollama_base_url)

            # Check what is currently loaded before issuing unload requests.
            loaded_models, status_known = _get_loaded_model_names(client)
            vision_models_to_check = list(dict.fromkeys(
                m for m in [settings.vision_model, settings.mid_vision_model] if m
            ))

            for vision_model in vision_models_to_check:
                should_unload = (not status_known) or any(vision_model in lm for lm in loaded_models)
                if not should_unload:
                    print(f"[generator] {vision_model} not loaded; skipping unload")
                    continue
                try:
                    client.generate(model=vision_model, prompt="", keep_alive=0)
                    _wait_for_model_unload(client, vision_model)
                    print(f"[generator] {vision_model} unloaded, ready for {settings.reasoning_model}")
                    loaded_models, status_known = _get_loaded_model_names(client, quiet=True)
                except Exception:
                    pass

            response = client.generate(
                model=settings.reasoning_model,
                prompt=prompt,
                system=system_prompt,
                options={"temperature": 0.3},
            )
            if response is None:
                raise RuntimeError("Reasoning model returned no response.")
            raw = response["response"].strip()

            # Strip meta-commentary the small model sometimes prepends
            skip_prefixes = ("i'd", "i 'd", "here ", "note:", "sure", "certainly", "of course", "as requested")
            lines = [
                line for line in raw.splitlines()
                if not line.strip().lower().startswith(skip_prefixes)
            ]
            clean = "\n".join(lines).strip()

            # Unload reasoning model after use unless warm mode is enabled.
            if not settings.keep_reasoning_model_warm:
                try:
                    client.generate(model=settings.reasoning_model, prompt="", keep_alive=0)
                except Exception:
                    pass
            else:
                print(f"[generator] keeping {settings.reasoning_model} warm for faster follow-up requests")

            english_text = clean if clean else raw
            english_text = _align_with_observed_issue(english_text, description)
            source_issue = description if len(_tokenize_words(description)) >= 6 else english_text
            if output_mode == "email":
                english_text = _compose_structured_email_text(source_issue, category, address)
            else:
                english_text = _compose_official_mail_text(source_issue, category, address)
                english_text = _fit_to_target_words(english_text)

            # ── Step 2: Post-translate if a non-English language was requested ──
            if language and language != "en":
                english_text = _translate(english_text, target_lang=language)

            return english_text

        except Exception as e:
            print(f"[generator] Draft generation failed ({e}); using deterministic complaint template")
            fallback_source = description if len(_tokenize_words(description)) >= 6 else "A civic issue requiring attention"
            if output_mode == "email":
                fallback = _compose_structured_email_text(fallback_source, category, address)
            else:
                fallback = _compose_official_mail_text(fallback_source, category, address)
                fallback = _fit_to_target_words(fallback)
            if language and language != "en":
                fallback = _translate(fallback, target_lang=language)
            return fallback
