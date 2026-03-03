import ollama
import os
import time
from app.config import settings
from app.llm_lock import ollama_lock


def _wait_for_model_unload(client: ollama.Client, model_name: str, timeout: float = 30.0) -> None:
    """
    Poll Ollama's running-models list until `model_name` is no longer present
    or `timeout` seconds have elapsed. The keep_alive=0 call is async on the
    Ollama side — without this wait llama3.2:1b starts loading while the vision
    model is still resident, causing OOM or slow generation.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            running = client.ps()  # returns list of currently loaded models
            names = [
                (m.model if hasattr(m, "model") else m.get("model", ""))
                for m in (running.models if hasattr(running, "models") else running.get("models", []))
            ]
            if not any(model_name in n for n in names):
                return  # fully unloaded
        except Exception:
            return  # if ps() fails, proceed anyway
        time.sleep(0.5)


def generate_complaint(image_path, classification_result, user_details, location_details):
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

    with ollama_lock:
        try:
            client = ollama.Client(host=settings.ollama_base_url)

            # Signal each vision model to unload, then WAIT until Ollama confirms
            # it is no longer in the running-models list before loading llama3.2:1b.
            for vision_model in dict.fromkeys(
                m for m in [settings.vision_model, settings.mid_vision_model] if m
            ):
                try:
                    client.generate(model=vision_model, prompt="", keep_alive=0)
                    _wait_for_model_unload(client, vision_model, timeout=30.0)
                    print(f"[generator] {vision_model} unloaded, loading {settings.reasoning_model}")
                except Exception:
                    pass

            response = client.generate(
                model=settings.reasoning_model,
                prompt=prompt,
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
