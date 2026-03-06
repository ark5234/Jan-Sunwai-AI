"""
Proactive RAM-aware model selection for Ollama vision models.

Before loading a model, checks available system memory and compares it
against the estimated runtime requirement.  If the primary model won't
fit, automatically selects the lighter fallback model.

No external dependencies — uses only Python stdlib + the Ollama client.
"""

from __future__ import annotations

import os
import platform
from typing import Optional

import ollama
from app.config import settings

# ── Runtime memory multipliers ──────────────────────────────────────────
# On-disk (quantised GGUF) size × multiplier ≈ runtime RAM needed.
# qwen2.5vl:3b is ~2.0 GB on disk; at 1.8× that's ~3.6 GB estimated runtime
# which fits comfortably on a 15 GB RAM machine while leaving headroom.
# The previous 2.6× value was too aggressive and caused moondream (a poor
# captioning model that hallucinates civic problems) to be selected instead.
_VISION_RUNTIME_MULTIPLIER  = 1.8   # e.g. 2.0 GB on disk → ~3.6 GB runtime
_TEXT_RUNTIME_MULTIPLIER    = 1.5   # e.g. 1.3 GB on disk → ~2.0 GB runtime
_DEFAULT_RUNTIME_MULTIPLIER = 1.8   # safe middle ground

# Families that include a vision encoder (higher memory overhead)
_VISION_FAMILIES = {"qwen25vl", "llava", "clip", "phi2", "minicpm", "granite", "moondream"}

# ── Safety margin ───────────────────────────────────────────────────────
# Keep some RAM free for OS + other processes (in bytes).
# 256 MB is enough headroom; 512 MB was too conservative and caused models
# that actually run fine (e.g. granite3.2-vision:2b at 4.3 GB available)
# to be rejected and then immediately used as the last-resort fallback anyway.
_SAFETY_MARGIN_BYTES = 256 * 1024 * 1024  # 256 MB


def _get_available_ram_bytes() -> Optional[int]:
    """Return available (free) system RAM in bytes, or None if unknown."""
    system = platform.system()
    try:
        if system in ("Linux", "Darwin"):
            # Works in Docker containers too (reads host /proc/meminfo via cgroup)
            page_size: int = getattr(os, "sysconf")("SC_PAGE_SIZE")
            avail_pages: int = getattr(os, "sysconf")("SC_AVPHYS_PAGES")
            return page_size * avail_pages
        elif system == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
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
            return int(stat.ullAvailPhys)
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
        models = response.models if hasattr(response, "models") else response.get("models", [])  # type: ignore[union-attr]
        for m in models:
            name: str = str(
                m.model if hasattr(m, "model") else m.get("model", m.get("name", ""))  # type: ignore[union-attr]
            )
            size: int = int(
                m.size if hasattr(m, "size") else m.get("size", 0)  # type: ignore[union-attr]
            )
            details = m.details if hasattr(m, "details") else m.get("details", {})  # type: ignore[union-attr]
            families_raw = (
                details.families if hasattr(details, "families") and details is not None
                else (details.get("families", []) if isinstance(details, dict) else [])
            )
            families: set[str] = set(f.lower() for f in (families_raw or []))

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
    Pick the best vision model from the 3-tier priority chain that fits in RAM.

    Priority order: vision_model → mid_vision_model → fallback_vision_model

    Returns the first model that fits, or the last model in the chain as a
    last-resort fallback if none are detected in Ollama's model list.
    """
    # Build deduplicated, ordered chain (skip empty / duplicate entries)
    chain: list[str] = list(dict.fromkeys(
        m for m in [
            settings.vision_model,
            settings.mid_vision_model,
            settings.fallback_vision_model,
        ] if m
    ))

    if len(chain) == 1:
        return chain[0]

    available_ram = _get_available_ram_bytes()
    if available_ram is None:
        print("[model_selector] could not detect available RAM, using primary model")
        return chain[0]

    available_gb = available_ram / (1024 ** 3)

    client = ollama.Client(host=settings.ollama_base_url)
    model_info = _get_model_info(client)

    for model in chain:
        info = model_info.get(model)
        if not info:
            # Model not yet pulled — skip the RAM check, caller handles missing model
            print(f"[model_selector] '{model}' not found in Ollama list, skipping RAM check")
            continue
        needed = info["estimated_runtime_bytes"] + _SAFETY_MARGIN_BYTES
        needed_gb = needed / (1024 ** 3)
        if available_ram >= needed:
            print(f"[model_selector] ✓ {model} fits "
                  f"(needs ~{needed_gb:.1f} GB, available {available_gb:.1f} GB)")
            return model
        else:
            print(f"[model_selector] ✗ {model} too large "
                  f"(needs ~{needed_gb:.1f} GB, available {available_gb:.1f} GB) "
                  f"→ trying next tier")

    # All models either too large or not found — use last in chain as last resort
    last = chain[-1]
    print(f"[model_selector] all tiers exhausted, falling back to last option: {last}")
    return last
