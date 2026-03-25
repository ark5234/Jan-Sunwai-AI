from __future__ import annotations

import re

CANONICAL_CATEGORIES = [
    "Health Department",
    "Civil Department",
    "Horticulture",
    "Electrical Department",
    "IT Department",
    "Commercial",
    "Enforcement",
    "VBD Department",
    "EBR Department",
    "Fire Department",
    "Uncategorized",
]

_ALIAS_TO_CANONICAL: dict[str, str] = {
    "health department": "Health Department",
    "health": "Health Department",
    "civil department": "Civil Department",
    "civil": "Civil Department",
    "civil-i": "Civil Department",
    "civil-ii": "Civil Department",
    "civil-iii": "Civil Department",
    "horticulture": "Horticulture",
    "electrical department": "Electrical Department",
    "electrical": "Electrical Department",
    "electric": "Electrical Department",
    "electric-i": "Electrical Department",
    "electric-ii": "Electrical Department",
    "it department": "IT Department",
    "it": "IT Department",
    "commercial": "Commercial",
    "enforcement": "Enforcement",
    "vbd department": "VBD Department",
    "vbd": "VBD Department",
    "ebr department": "EBR Department",
    "ebr": "EBR Department",
    "fire department": "Fire Department",
    "fire": "Fire Department",
    "uncategorized": "Uncategorized",
    # Legacy aliases for smooth migration of any old data
    "municipal - pwd (roads)": "Civil Department",
    "municipal - sanitation": "Health Department",
    "municipal - street lighting": "Electrical Department",
    "municipal - water & sewerage": "Civil Department",
    "utility - power (discom)": "Electrical Department",
    "police - local law enforcement": "Enforcement",
    "police - traffic": "Enforcement",
}

_SAFE_FOLDER_TO_CANONICAL: dict[str, str] = {
    "Health_Department": "Health Department",
    "Civil_Department": "Civil Department",
    "Horticulture": "Horticulture",
    "Electrical_Department": "Electrical Department",
    "IT_Department": "IT Department",
    "Commercial": "Commercial",
    "Enforcement": "Enforcement",
    "VBD_Department": "VBD Department",
    "EBR_Department": "EBR Department",
    "Fire_Department": "Fire Department",
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
