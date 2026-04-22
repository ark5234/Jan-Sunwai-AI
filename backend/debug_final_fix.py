
from app.rule_engine import _CATEGORY_RULES, _score_text, _LEAF_DOMINANT_TERMS, _HARD_SANITATION_TERMS, _GENERIC_SANITATION_TERMS, classify_by_rules
import json

def debug_final(payload):
    print(f"DEBUGGING PAYLOAD: {json.dumps(payload, indent=2)}")
    
    result = classify_by_rules(payload)
    print("\nCLASSIFICATION RESULT:")
    print(json.dumps(result, indent=2))

# Simulation: Vision model followed old prompt and used 'garbage' as primary issue,
# but it's a park with leaves.
payload_mixed = {
    "description": "The image shows a park sidewalk with some garbage and leaves scattered about.",
    "visible_objects": ["sidewalk", "park", "leaves"],
    "primary_issue": "garbage",
    "secondary_issue": "",
    "hazards": [],
    "setting": "park"
}

print("--- SIMULATING MIXED PARK SCENE WITH 'GARBAGE' KEYWORD ---")
debug_final(payload_mixed)
