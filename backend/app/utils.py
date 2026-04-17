"""
Shared utilities for Jan-Sunwai AI backend.

Fix M-2: `fix_id()` was duplicated in three separate router files
(complaints.py, notifications.py, workers.py). Extracted here as the
single source of truth. Import from this module going forward.
"""
from __future__ import annotations

from typing import Optional


def fix_id(doc: Optional[dict]) -> Optional[dict]:
    """
    Convert MongoDB ObjectId ``_id`` to a plain string in-place.

    Returns the same dict (mutated) for convenient chaining:
        return fix_id(await db["complaints"].find_one(...))
    Returns None unchanged so callers don't need a separate None check.
    """
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc
