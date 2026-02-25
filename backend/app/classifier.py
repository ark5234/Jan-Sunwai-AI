import io
import os
import ollama
from PIL import Image
from app.config import settings
from app.category_utils import CANONICAL_CATEGORIES, canonicalize_label

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
    Two-step Vision-to-Reasoning classifier.

    Step 1 — Vision (qwen2.5-vl:3b):
        Narrates what is physically present and problematic in the image.

    Step 2 — Reasoning (llama3.2:1b):
        Maps the narration to a canonical civic category using folder definitions.
    """

    def classify(self, image_path: str) -> dict:
        if not os.path.exists(image_path):
            return {
                "department": "Unknown",
                "label": "Image file not found",
                "confidence": 0.0,
                "is_valid": False,
            }

        try:
            # Convert image to RGB JPEG bytes (avoids GGML_ASSERT on RGBA
            # images and "unknown format" errors on BMP/TIFF/WebP variants)
            image_bytes = _load_image_as_jpeg_bytes(image_path)

            # ------------------------------------------------------------------
            # STEP 1 — Vision: Describe the image
            # ------------------------------------------------------------------
            vision_response = ollama.generate(
                model=settings.vision_model,
                prompt=(
                    "You are analyzing a civic complaint photo from India. "
                    "Describe what you see in 2-3 factual sentences. "
                    "Focus on: what is visibly damaged or problematic, "
                    "the setting (road, park, building, drain, etc.), "
                    "and any visible hazards or health/safety risks. "
                    "Be specific and objective. Do not greet or explain yourself."
                ),
                images=[image_bytes],
                options={"num_ctx": 2048},
            )
            description: str = vision_response["response"].strip()

            # ------------------------------------------------------------------
            # STEP 2 — Reasoning: Map description to canonical category
            # ------------------------------------------------------------------
            categories_block = "\n".join(
                f"- {cat}: {CATEGORY_DEFINITIONS[cat]}"
                for cat in CANONICAL_CATEGORIES
            )

            reasoning_response = ollama.generate(
                model=settings.reasoning_model,
                options={"num_ctx": 1024},
                prompt=(
                    f"You are a civic complaint classifier for Indian municipal authorities.\n\n"
                    f"Image description: \"{description}\"\n\n"
                    f"Choose the SINGLE best matching category. Read ALL options before deciding.\n\n"
                    f"Categories:\n"
                    f"{categories_block}\n\n"
                    f"Decision rules (apply in order):\n"
                    f"1. If description mentions dangling wires, power cables, open transformer, fallen electric pole → Utility - Power (DISCOM)\n"
                    f"2. If description mentions waterlogging, flooded street, drain overflow, sewer, pipe leak, water gushing → Municipal - Water & Sewerage\n"
                    f"3. If description mentions garbage, trash, waste, dump, litter, bins, debris scattered on ground → Municipal - Sanitation\n"
                    f"4. If description mentions potholes, road cracks, broken road, damaged pavement, footpath damage, manhole cover damage → Municipal - PWD (Roads)\n"
                    f"5. If description mentions broken street lights, non-functional lamp posts, unlit road (no wires mentioned) → Municipal - Street Lighting\n"
                    f"6. If description mentions fallen/uprooted trees, overgrown parks, dead plants, tree branches blocking road → Municipal - Horticulture\n"
                    f"7. If description mentions smoke, burning, industrial pollution, waste dumping into water → Pollution Control Board\n"
                    f"8. If description mentions illegal parking, footpath encroachment, shops blocking path → Police - Local Law Enforcement\n"
                    f"9. If description mentions traffic signal failure, severe road blockage, traffic jam → Police - Traffic\n"
                    f"10. If description mentions damaged bus shelter, broken state bus, bus terminal → State Transport\n"
                    f"11. If the image is black, blurry, unrecognisable, or shows a person/selfie/food → Uncategorized\n"
                    f"12. If nothing matches clearly → Uncategorized\n\n"
                    f"IMPORTANT: Do NOT default to Municipal - Water & Sewerage unless water/flooding/drain is explicitly described.\n"
                    f"IMPORTANT: Litter and waste on a road/street = Municipal - Sanitation (not Transport, not Roads).\n"
                    f"IMPORTANT: A pole with hanging wires = Utility - Power (DISCOM), not Horticulture or Roads.\n"
                    f"Reply with ONLY the exact category name. No explanation.\n\n"
                    f"Category:"
                ),
            )
            raw_label: str = reasoning_response["response"].strip()

            # Guard: some models echo "Category: X" — strip the prefix if present
            if ":" in raw_label:
                raw_label = raw_label.split(":", 1)[-1].strip()

            canonical = canonicalize_label(raw_label)

            # Determine validity
            desc_lower = description.lower()
            is_non_civic = any(kw in desc_lower for kw in _NEGATIVE_KEYWORDS)
            is_valid = (canonical != "Uncategorized") and not is_non_civic

            return {
                "department": canonical,
                "label": description,
                "confidence": 0.9 if is_valid else 0.4,
                "is_valid": is_valid,
                "vision_description": description,
                "raw_category": raw_label,
            }

        except Exception as e:
            print(f"Classification Error: {e}")
            return {
                "department": "Unknown",
                "label": "Could not classify image",
                "confidence": 0.0,
                "is_valid": False,
                "error": str(e),
            }

