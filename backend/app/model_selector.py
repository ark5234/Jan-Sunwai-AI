"""
Proactive RAM-aware model selection for Ollama vision models.

Before loading a model, checks available system memory and compares it
against the estimated runtime requirement.  If the primary model won't
fit, automatically selects the lighter fallback model.

No external dependencies — uses only Python stdlib + the Ollama client.
"""

import os
import platform
import ollama
from app.config import settings

# ── Runtime memory multipliers ──────────────────────────────────────────
# On-disk (quantised GGUF) size × multiplier ≈ runtime RAM needed.
# Vision models carry an extra image encoder, so they need a higher factor.
_VISION_RUNTIME_MULTIPLIER  = 2.6   # e.g. 3.2 GB on disk → ~8.3 GB runtime
_TEXT_RUNTIME_MULTIPLIER    = 1.5   # e.g. 1.3 GB on disk → ~2.0 GB runtime
_DEFAULT_RUNTIME_MULTIPLIER = 2.0   # safe middle ground

# Families that include a vision encoder (higher memory overhead)
_VISION_FAMILIES = {"qwen25vl", "llava", "clip", "phi2", "minicpm"}

# ── Safety margin ───────────────────────────────────────────────────────
# Keep some RAM free for OS + other processes (in bytes)
_SAFETY_MARGIN_BYTES = 512 * 1024 * 1024  # 512 MB


def _get_available_ram_bytes() -> int | None:
    """Return available (free) system RAM in bytes, or None if unknown."""
    system = platform.system()
    try:
        if system == "Linux":
            # Works in Docker containers too (reads host /proc/meminfo via cgroup)
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES")
        elif system == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength",                ctypes.c_ulong),
                    ("dwMemoryLoad",            ctypes.c_ulong),
                    ("ullTotalPhys",            ctypes.c_ulonglong),
                    ("ullAvailPhys",            ctypes.c_ulonglong),
                    ("ullTotalPageFile",         ctypes.c_ulonglong),
                    ("ullAvailPageFile",         ctypes.c_ulonglong),
                    ("ullTotalVirtual",          ctypes.c_ulonglong),
                    ("ullAvailVirtual",          ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual",  ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return stat.ullAvailPhys
        elif system == "Darwin":  # macOS
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES")
    except Exception:
        pass
    return None


def _get_model_info(client: ollama.Client) -> dict[str, dict]:
    """
    Build a dict of model_name → {size_bytes, families, is_vision, estimated_runtime}.
    Caches nothing — always queries Ollama for fresh data.
    """
    info: dict[str, dict] = {}
    try:
        response = client.list()
        models = response.models if hasattr(response, "models") else response.get("models", [])
        for m in models:
            name = m.model if hasattr(m, "model") else m.get("model", m.get("name", ""))
            size = m.size if hasattr(m, "size") else m.get("size", 0)
            details = m.details if hasattr(m, "details") else m.get("details", {})
            families_raw = details.families if hasattr(details, "families") else details.get("families", [])
            families = set(f.lower() for f in (families_raw or []))

            is_vision = bool(families & _VISION_FAMILIES)
            multiplier = _VISION_RUNTIME_MULTIPLIER if is_vision else _TEXT_RUNTIME_MULTIPLIER

            info[name] = {
                "size_bytes": size,
                "families": families,
                "is_vision": is_vision,
                "estimated_runtime_bytes": int(size * multiplier),
            }
    except Exception as e:
        print(f"[model_selector] WARNING: could not list Ollama models: {e}")
    return info


def select_vision_model() -> str:
    """
    Pick the best vision model that fits in available RAM.

    Priority: settings.vision_model  →  settings.fallback_vision_model

    Returns the model name string to use.
    """
    primary  = settings.vision_model
    fallback = settings.fallback_vision_model

    # If no fallback configured, always use primary (let Ollama handle errors)
    if not fallback or fallback == primary:
        return primary

    available_ram = _get_available_ram_bytes()
    if available_ram is None:
        print("[model_selector] could not detect available RAM, using primary model")
        return primary

    available_gb = available_ram / (1024 ** 3)

    client = ollama.Client(host=settings.ollama_base_url)
    model_info = _get_model_info(client)

    primary_info  = model_info.get(primary)
    fallback_info = model_info.get(fallback)

    if not primary_info:
        print(f"[model_selector] primary model '{primary}' not found in Ollama, "
              f"trying fallback '{fallback}'")
        return fallback if fallback_info else primary

    needed = primary_info["estimated_runtime_bytes"] + _SAFETY_MARGIN_BYTES
    needed_gb = needed / (1024 ** 3)

    if available_ram >= needed:
        print(f"[model_selector] ✓ {primary} fits "
              f"(needs ~{needed_gb:.1f} GB, available {available_gb:.1f} GB)")
        return primary
    else:
        # Check if fallback fits
        if fallback_info:
            fb_needed = fallback_info["estimated_runtime_bytes"] + _SAFETY_MARGIN_BYTES
            fb_needed_gb = fb_needed / (1024 ** 3)
            print(f"[model_selector] ✗ {primary} too large "
                  f"(needs ~{needed_gb:.1f} GB, available {available_gb:.1f} GB) "
                  f"→ switching to {fallback} (needs ~{fb_needed_gb:.1f} GB)")
        else:
            print(f"[model_selector] ✗ {primary} too large "
                  f"(needs ~{needed_gb:.1f} GB, available {available_gb:.1f} GB) "
                  f"→ switching to {fallback}")
        return fallback
