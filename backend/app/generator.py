import io
import ollama
import os
from PIL import Image
from app.config import settings
from app.model_selector import select_vision_model


def _load_image_as_jpeg_bytes(image_path: str) -> bytes:
    """Convert any image to RGB JPEG bytes to avoid GGML_ASSERT/format errors."""
    with Image.open(image_path) as img:
        if img.mode not in ("RGB",):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()


def generate_complaint(image_path, classification_result, user_details, location_details):
    """
    Generates a formal government complaint letter using the configured Ollama vision model.
    For capable models (qwen2.5vl), uses the image directly with a detailed prompt.
    For small models (moondream), uses a simpler prompt and supplements with
    the classifier's description for better results.
    """
    
    # Validation
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}."

    # Use the civic department/category, not 'label' which is the raw vision description text
    category = classification_result.get("department") or classification_result.get("label", "Civic Issue")
    description = classification_result.get("vision_description") or classification_result.get("label", "")
    user_name = user_details.get("name", "Concerned Citizen")
    address = location_details.get("address", "New Delhi (Exact location pending)")
    
    try:
        # Use explicit client so host URL comes from config (not localhost default)
        client = ollama.Client(host=settings.ollama_base_url)
        image_bytes = _load_image_as_jpeg_bytes(image_path)

        # Proactive RAM check: pick the best model that fits in available memory
        selected_model = select_vision_model()
        is_primary = (selected_model == settings.vision_model)

        if is_primary:
            # Full prompt for capable models
            prompt = (
                f"You are writing a civic grievance description for an Indian government complaint portal.\n\n"
                f"TASK: Write a SHORT factual grievance description (60-90 words) about the issue shown in the image.\n\n"
                f"DETAILS:\n"
                f"- Location: {address}\n"
                f"- Issue Type: {category}\n\n"
                f"RULES:\n"
                f"- Do NOT write a letter. No 'Dear Sir', 'To The Officer', 'Respectfully submitted', salutations, or sign-offs.\n"
                f"- Do NOT include Subject line.\n"
                f"- Write ONLY a plain description of the problem as if filling a complaint form.\n"
                f"- First sentence: What the issue is and where it is located.\n"
                f"- Second/third sentences: Why it is dangerous or inconvenient for the public.\n"
                f"- Last sentence: What action is needed.\n"
                f"- Be direct, specific, factual. Maximum 90 words.\n\n"
                f"Write the grievance description now:"
            )
        else:
            # Small vision models (moondream) can't write structured text well.
            # Use the text-only reasoning model (llama3.2:1b) instead — it's
            # much better at following instructions.  Feed it the classifier's
            # description so it doesn't need to see the image.
            reasoning_prompt = (
                f"[COMPLAINT FORM FIELD — plain text only, no letter format]\n\n"
                f"Issue observed: {description}\n"
                f"Department: {category}\n"
                f"Location: {address}\n\n"
                f"Fill in the complaint description field below (60-90 words).\n"
                f"Rules: no salutations, no sign-offs, no 'Dear Sir', no 'Subject:' line, "
                f"no meta-commentary about writing style. "
                f"Start directly with the issue. Describe what the problem is, "
                f"why it is dangerous or inconvenient, and what action is needed.\n\n"
                f"Complaint description:"
            )

            try:
                # Unload vision model first to free memory for reasoning model
                try:
                    client.generate(model=selected_model, prompt="", keep_alive=0)
                except Exception:
                    pass

                response = client.generate(
                    model=settings.reasoning_model,
                    prompt=reasoning_prompt,
                )
                raw = response["response"].strip()
                # Strip any meta-commentary the small model prepends
                # (lines starting with "I ", "Here ", "Note:", "Sure" etc.)
                lines = raw.splitlines()
                cleaned_lines = []
                skip_prefixes = ("i \'d", "i'd", "here ", "note:", "sure", "certainly", "of course", "as requested")
                for line in lines:
                    if line.strip().lower().startswith(skip_prefixes):
                        continue  # skip meta-commentary lines
                    cleaned_lines.append(line)
                clean_text = "\n".join(cleaned_lines).strip()
                # Unload reasoning model after use
                try:
                    client.generate(model=settings.reasoning_model, prompt="", keep_alive=0)
                except Exception:
                    pass
                return clean_text if clean_text else raw
            except Exception as e:
                return (
                    f"System Note: Automated drafting failed ({str(e)}). "
                    f"Please draft manually based on category: {category}."
                )

        # --- Primary model path: use vision model with full prompt ---
        models_to_try = [selected_model]
        other = (settings.fallback_vision_model
                 if selected_model == settings.vision_model
                 else settings.vision_model)
        if other and other != selected_model:
            models_to_try.append(other)

        response = None
        used_model = selected_model
        for model_name in models_to_try:
            try:
                response = client.generate(
                    model=model_name,
                    prompt=prompt,
                    images=[image_bytes]
                )
                used_model = model_name
                break
            except Exception as model_err:
                err_msg = str(model_err).lower()
                is_oom = any(kw in err_msg for kw in [
                    "memory", "oom", "out of memory", "not enough",
                    "insufficient", "cannot allocate",
                ])
                if is_oom and model_name != models_to_try[-1]:
                    print(f"[generator] {model_name} OOM, falling back to {models_to_try[-1]}")
                    try:
                        client.generate(model=model_name, prompt="", keep_alive=0)
                    except Exception:
                        pass
                    continue
                raise

        # Unload vision model after letter generation to free VRAM
        try:
            client.generate(model=used_model, prompt="", keep_alive=0)
        except Exception:
            pass
        return response['response']
    except Exception as e:
        return f"System Note: Automated drafting failed ({str(e)}). Please draft manually based on category: {category}."
