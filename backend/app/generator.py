import ollama
import os
from app.config import settings


def generate_complaint(image_path, classification_result, user_details, location_details):
    """
    Generates a civic grievance description using the reasoning model (llama3.2:1b).

    Always uses text-only generation — the vision model has already run during
    classification and produced a structured description. Re-running a vision model
    with the image here was the original bottleneck (took 60–250 s extra).
    """

    # Use the civic department/category, not 'label' (raw vision description text)
    category = classification_result.get("department") or classification_result.get("label", "Civic Issue")
    description = (
        classification_result.get("vision_description")
        or classification_result.get("label", "")
        or "A civic issue requiring attention"
    )
    address = location_details.get("address", "Location not specified")

    prompt = (
        f"[COMPLAINT FORM FIELD — plain text only, no letter format]\n\n"
        f"Issue observed: {description}\n"
        f"Department: {category}\n"
        f"Location: {address}\n\n"
        f"Fill in the complaint description field below (60-90 words).\n"
        f"Rules: no salutations, no sign-offs, no 'Dear Sir', no 'Subject:' line, "
        f"no meta-commentary. "
        f"Start directly with the issue. Describe what the problem is, "
        f"why it is dangerous or inconvenient, and what action is needed.\n\n"
        f"Complaint description:"
    )

    try:
        client = ollama.Client(host=settings.ollama_base_url)

        # Unload any vision model currently in VRAM before loading the reasoning model.
        # This is the key step — without it, llama3.2:1b can't load if qwen2.5vl:3b
        # or granite is still resident after classification.
        for vision_model in {settings.vision_model, settings.mid_vision_model}:
            if vision_model:
                try:
                    client.generate(model=vision_model, prompt="", keep_alive=0)
                except Exception:
                    pass

        response = client.generate(
            model=settings.reasoning_model,
            prompt=prompt,
        )
        raw = response["response"].strip()

        # Strip meta-commentary the small model sometimes prepends
        skip_prefixes = ("i'd", "i 'd", "here ", "note:", "sure", "certainly", "of course", "as requested")
        lines = [
            line for line in raw.splitlines()
            if not line.strip().lower().startswith(skip_prefixes)
        ]
        clean = "\n".join(lines).strip()

        # Unload reasoning model after use to free RAM for the next request
        try:
            client.generate(model=settings.reasoning_model, prompt="", keep_alive=0)
        except Exception:
            pass

        return clean if clean else raw

    except Exception as e:
        return (
            f"Automated drafting failed ({str(e)}). "
            f"Please describe the issue manually. Category: {category}."
        )
