
from app.rule_engine import classify_by_rules
import json

def test_scenario(name, payload):
    print(f"--- SCENARIO: {name} ---")
    result = classify_by_rules(payload)
    print(f"Category: {result['category']} (Conf: {result['confidence']})")
    # print(json.dumps(result['scores'], indent=2))
    print("-" * 40)

# 1. Civil vs VBD: Pipe leak causing stagnant water
payload_leak = {
    "description": "Large pool of stagnant water formed due to a leaking pipe on the roadside.",
    "visible_objects": ["water", "pipe"],
    "primary_issue": "leaking pipe",
    "secondary_issue": "stagnant water",
    "hazards": [],
    "setting": "roadside"
}

# 2. Civil vs VBD: Road depression causing water pooling
payload_depression = {
    "description": "Standing water accumulated in a major road depression after the rain.",
    "visible_objects": ["water", "road"],
    "primary_issue": "road depression",
    "secondary_issue": "standing water",
    "hazards": [],
    "setting": "road"
}

# 3. VBD pure: Mosquito larvae in a bucket
payload_vbd = {
    "description": "Discarded bucket with stagnant water showing visible mosquito larvae.",
    "visible_objects": ["bucket", "water", "larvae"],
    "primary_issue": "mosquito breeding",
    "secondary_issue": "",
    "hazards": [],
    "setting": "residential area"
}

# 4. Enforcement vs Civil: Vendor on broken pavement
payload_encroachment = {
    "description": "Unauthorized vendor has set up a stall on the footpath, blocking pedestrian movement on the broken pavement.",
    "visible_objects": ["vendor", "stall", "footpath"],
    "primary_issue": "hawker encroachment",
    "secondary_issue": "footpath damage",
    "hazards": [],
    "setting": "footpath"
}

# 5. Horticulture: Leaves on sidewalk (The original problem)
payload_leaves = {
    "description": "The image shows a sidewalk with some debris and a few leaves scattered about.",
    "visible_objects": ["sidewalk", "leaves"],
    "primary_issue": "debris",
    "secondary_issue": "",
    "hazards": [],
    "setting": "sidewalk"
}

test_scenario("Infrastructure Leak (Civil vs VBD)", payload_leak)
test_scenario("Road Depression (Civil vs VBD)", payload_depression)
test_scenario("Pure VBD (Mosquitoes)", payload_vbd)
test_scenario("Hawker Encroachment (Enforcement vs Civil)", payload_encroachment)
test_scenario("Leaves on Sidewalk (Horticulture)", payload_leaves)
