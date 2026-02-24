from __future__ import annotations

import re
from typing import Dict

CANONICAL_CATEGORIES = [
    "Municipal - PWD (Roads)",
    "Municipal - Sanitation",
    "Municipal - Horticulture",
    "Municipal - Street Lighting",
    "Municipal - Water & Sewerage",
    "Utility - Power (DISCOM)",
    "State Transport",
    "Pollution Control Board",
    "Police - Local Law Enforcement",
    "Police - Traffic",
    "Uncategorized",
]

_ALIAS_TO_CANONICAL: Dict[str, str] = {
    "municipal - pwd (roads)": "Municipal - PWD (Roads)",
    "municipal - pwd roads": "Municipal - PWD (Roads)",
    "municipal - pwd (bridges)": "Municipal - PWD (Roads)",
    "municipal - sanitation": "Municipal - Sanitation",
    "municipal - horticulture": "Municipal - Horticulture",
    "municipal - street lighting": "Municipal - Street Lighting",
    "municipal - water & sewerage": "Municipal - Water & Sewerage",
    "municipal - water and sewerage": "Municipal - Water & Sewerage",
    "utility - power (discom)": "Utility - Power (DISCOM)",
    "state transport": "State Transport",
    "pollution control board": "Pollution Control Board",
    "police - local law enforcement": "Police - Local Law Enforcement",
    "police - traffic": "Police - Traffic",
    "uncategorized": "Uncategorized",
}

_SAFE_FOLDER_TO_CANONICAL = {
    "Municipal_-_PWD_Roads": "Municipal - PWD (Roads)",
    "Municipal_-_Sanitation": "Municipal - Sanitation",
    "Municipal_-_Horticulture": "Municipal - Horticulture",
    "Municipal_-_Street_Lighting": "Municipal - Street Lighting",
    "Municipal_-_Water_and_Sewerage": "Municipal - Water & Sewerage",
    "Utility_-_Power_DISCOM": "Utility - Power (DISCOM)",
    "State_Transport": "State Transport",
    "Pollution_Control_Board": "Pollution Control Board",
    "Police_-_Local_Law_Enforcement": "Police - Local Law Enforcement",
    "Police_-_Traffic": "Police - Traffic",
    "Uncategorized": "Uncategorized",
}


def safe_dirname(label: str) -> str:
    return label.replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and")


def folder_to_label(folder_name: str) -> str:
    if folder_name in _SAFE_FOLDER_TO_CANONICAL:
        return _SAFE_FOLDER_TO_CANONICAL[folder_name]
    return canonicalize_label(folder_name.replace("_", " "))


def canonicalize_label(label: str) -> str:
    cleaned = _normalize(label)
    if cleaned in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[cleaned]

    for alias, canonical in _ALIAS_TO_CANONICAL.items():
        if cleaned in alias or alias in cleaned:
            return canonical

    return "Uncategorized"


def labels_match(expected: str, predicted: str) -> bool:
    return canonicalize_label(expected) == canonicalize_label(predicted)


def _normalize(text: str) -> str:
    text = text.strip().lower().replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text
