import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.classifier import CivicClassifier
from app.rule_engine import classify_by_rules

def test_rule_engine():
    classifier = CivicClassifier()
    
    test_cases = [
        {
            "name": "Construction Waste (Rebar/Cement)",
            "payload": {
                "description": "The image shows a pile of construction materials including rebar iron rods and cement bags on the side of a road.",
                "primary_issue": "construction material",
                "visible_objects": ["rebar", "iron rods", "cement bags"],
                "hazards": ["tripping hazard", "obstruction"]
            }
        },
        {
            "name": "Vegetation Pile (Dry Grass)",
            "payload": {
                "description": "A large pile of dry grass and vegetation debris is seen on the roadside.",
                "primary_issue": "vegetation pile",
                "visible_objects": ["dry grass", "piles of vegetation"],
                "hazards": []
            }
        },
        {
            "name": "Sand vs Leaves (Roadside)",
            "payload": {
                "description": "A sidewalk with dust accumulation and sand on the roadside, also containing some scattered dried leaves.",
                "primary_issue": "sand accumulation",
                "visible_objects": ["sand", "dust", "leaves"],
                "hazards": ["slippery surface"]
            }
        }
    ]
    
    print("--- Rule Engine Verification ---")
    for case in test_cases:
        result = classify_by_rules(case["payload"])
        print(f"Test: {case['name']}")
        print(f"  Result Category: {result['category']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Is Ambiguous: {result.get('is_ambiguous', False)}")
        print(f"  Scores: {result['scores']}")
        print()

if __name__ == "__main__":
    test_rule_engine()
