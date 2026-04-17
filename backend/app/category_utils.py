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
    "sanitation": "Health Department",
    "civil department": "Civil Department",
    "civil": "Civil Department",
    "civil-i": "Civil Department",
    "civil-ii": "Civil Department",
    "civil-iii": "Civil Department",
    "horticulture": "Horticulture",
    "electrical department": "Electrical Department",
    "electrical": "Electrical Department",
    "electric": "Electrical Department",
    "street lighting": "Electrical Department",
    "electric-i": "Electrical Department",
    "electric-ii": "Electrical Department",
    "it department": "IT Department",
    "it": "IT Department",
    "commercial": "Commercial",
    "enforcement": "Enforcement",
    "traffic": "Enforcement",
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


def _tokenize_for_fuzzy_match(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]


_FUZZY_ALIAS_RULES: list[tuple[list[str], str]] = sorted(
    (
        (tokens, canonical)
        for alias, canonical in _ALIAS_TO_CANONICAL.items()
        if (tokens := _tokenize_for_fuzzy_match(alias))
    ),
    key=lambda item: len(item[0]),
    reverse=True,
)

_IT_CONTEXT_TOKENS: set[str] = {
    "department",
    "team",
    "system",
    "software",
    "app",
    "website",
    "portal",
    "server",
    "network",
    "login",
    "password",
}


def _matches_single_token_alias(alias_token: str, cleaned: str, cleaned_tokens: set[str]) -> bool:
    if alias_token not in cleaned_tokens:
        return False

    if alias_token == "it":
        return cleaned == "it" or bool(cleaned_tokens & _IT_CONTEXT_TOKENS)

    return True

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

    cleaned_tokens = set(_tokenize_for_fuzzy_match(cleaned))

    # Token-based fuzzy matching avoids false positives such as
    # matching alias "it" inside words like "sanitation".
    for alias_tokens, canonical in _FUZZY_ALIAS_RULES:
        if len(alias_tokens) == 1:
            if _matches_single_token_alias(alias_tokens[0], cleaned, cleaned_tokens):
                return canonical
            continue

        if all(token in cleaned_tokens for token in alias_tokens):
            return canonical

    return "Uncategorized"


def labels_match(expected: str, predicted: str) -> bool:
    return canonicalize_label(expected) == canonicalize_label(predicted)


def _normalize(text: str) -> str:
    text = text.strip().lower().replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text
