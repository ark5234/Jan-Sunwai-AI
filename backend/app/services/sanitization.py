from __future__ import annotations

import re

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


def sanitize_text(value: str, max_len: int | None = None) -> str:
    """Basic text sanitization for user-provided free text.

    - Strips null bytes and control characters (injection risk)
    - Normalizes repeated spaces
    - Does NOT HTML-escape — values are stored in MongoDB and returned as JSON;
      escaping here causes double-encoding when the frontend renders them.
      XSS prevention is the frontend's responsibility (React escapes by default).
    """
    text = (value or "").strip()
    text = _CONTROL_CHAR_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    if max_len is not None:
        text = text[:max_len]
    return text.strip()


def sanitize_phone_number(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9+\-() ]", "", value).strip()
    if len(cleaned) > 20:
        cleaned = cleaned[:20]
    return cleaned or None
