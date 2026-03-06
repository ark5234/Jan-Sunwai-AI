"""
Rule-based priority scoring for civic complaints.
Analyses the description text and department to assign a PriorityLevel.
"""
from app.schemas import PriorityLevel

_CRITICAL = [
    "collapse", "caved in", "sinkhole", "flood", "flooded", "electric shock",
    "live wire", "open wire", "exposed wire", "fire", "smoke", "burning",
    "explosion", "gas leak", "sewage overflow", "raw sewage", "injury",
    "injured", "accident", "death", "dead body", "road block", "road blocked",
    "fallen tree", "landslide", "building collapse", "wall collapse",
]

_HIGH = [
    "pothole", "no water", "water cut", "power cut", "no power", "no electricity",
    "blackout", "broken signal", "signal not working", "street light out",
    "broken pipe", "water leakage", "major leak", "dangerous", "hazard",
    "urgent", "overflowing drain", "blocked drain", "sewage smell",
    "garbage pile", "large pothole", "deep pothole",
]

_MEDIUM = [
    "damaged", "broken", "non-functional", "not working", "cracks", "cracked",
    "dirty", "garbage", "waste", "stray", "complaint", "issue", "problem",
    "repair needed", "maintenance", "pothole",
]

_EMERGENCY_DEPTS = {
    "Police - Local Law Enforcement",
    "Police - Traffic",
    "Utility - Power (DISCOM)",
}


def compute_priority(description: str, department: str) -> PriorityLevel:
    text = (description or "").lower()

    for kw in _CRITICAL:
        if kw in text:
            return PriorityLevel.CRITICAL

    for kw in _HIGH:
        if kw in text:
            return PriorityLevel.HIGH

    if department in _EMERGENCY_DEPTS:
        return PriorityLevel.HIGH

    for kw in _MEDIUM:
        if kw in text:
            return PriorityLevel.MEDIUM

    return PriorityLevel.LOW
