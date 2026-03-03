"""
Shared threading lock for all Ollama model operations.

The classifier (vision model) and the generator (unloads vision, loads reasoning)
both touch the same Ollama model slots.  Without serialisation these two paths
race: the generator can unload the vision model mid-inference, causing the
classifier to throw an exception and return {"method": "error"}.

Both classify() and generate_complaint() acquire this lock before making any
Ollama API call, so they can never run concurrently.
"""
import threading

ollama_lock = threading.Lock()
