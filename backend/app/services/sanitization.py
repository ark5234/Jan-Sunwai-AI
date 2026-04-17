from __future__ import annotations

import html
import re

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


def sanitize_text(value: str, max_len: int | None = None) -> str:
    """Basic text sanitization for user-provided free text.

    - Strips null bytes and control characters (injection risk)
    - Normalizes repeated spaces
    - HTML-escapes angle brackets and special characters so XSS payloads
      stored in MongoDB are neutralised at the source (defence-in-depth).
      React additionally escapes on render, preventing double-encoding issues
      when raw values are interpolated into non-JSX contexts (e.g. email).
    """
    text = (value or "").strip()
    text = _CONTROL_CHAR_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    if max_len is not None:
        text = text[:max_len]
    text = html.escape(text.strip(), quote=False)
    return text


def sanitize_phone_number(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9+\-() ]", "", value).strip()
    if len(cleaned) > 20:
        cleaned = cleaned[:20]
    return cleaned or None
