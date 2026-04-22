
from app.rule_engine import _CATEGORY_RULES, _score_text, _LEAF_DOMINANT_TERMS, _STRONG_SANITATION_TERMS, _first_mention_position, classify_by_rules
import json

def debug_scores(text_lower):
    print(f"DEBUGGING TEXT: '{text_lower}'")
    
    # Check Leaf Dominance
    leaf_matches = [term for term in _LEAF_DOMINANT_TERMS if term in text_lower]
    sanitation_matches = [term for term in _STRONG_SANITATION_TERMS if term in text_lower]
    park_matches = [term for term in ["park", "garden", "greenery", "vegetation"] if term in text_lower]
    
    print(f"Leaf terms found: {leaf_matches}")
    print(f"Strong sanitation terms found: {sanitation_matches}")
    print(f"Park terms found: {park_matches}")
    
    scores = {}
    matches = {}
    for category, rules in _CATEGORY_RULES.items():
        cat_score = 0.0
        cat_matches = []
        for keywords, weight in rules:
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                cat_score += weight
                cat_matches.append((found, weight))
        scores[category] = cat_score
        matches[category] = cat_matches
    
    print("\nRaw Scores and Matches:")
    for cat, score in scores.items():
        if score > 0:
            print(f"  {cat}: {score} (Matches: {matches[cat]})")

    # Re-run the logic steps
    has_leaf_dominant = len(leaf_matches) > 0
    has_strong_sanitation = len(sanitation_matches) > 0
    has_park_context = len(park_matches) > 0
    
    if has_leaf_dominant and not has_strong_sanitation:
        penalty = 0.25 if not has_park_context else 0.1
        boost = 2.5 if not has_park_context else 4.0
        print(f"\nApplying Leaf preference: penalty={penalty}, boost={boost}")
        scores["Health Department"] *= penalty
        scores["Horticulture"] += boost
    else:
        print("\nLeaf preference NOT applied.")
        if not has_leaf_dominant: print("  - Reason: Not leaf dominant")
        if has_strong_sanitation: print("  - Reason: Strong sanitation present")

    _ALL_CATEGORY_SIGNALS = {
        cat: [kw for kws, _w in rules for kw in kws if _w >= 2.0]
        for cat, rules in _CATEGORY_RULES.items()
    }
    first_positions = {}
    for cat, kws in _ALL_CATEGORY_SIGNALS.items():
        pos = -1
        best_kw = None
        for kw in kws:
            p = text_lower.find(kw)
            if p != -1 and (pos == -1 or p < pos):
                pos = p
                best_kw = kw
        if pos >= 0:
            first_positions[cat] = pos
            print(f"  Signal for {cat} found at {pos}: '{best_kw}'")

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    if len(ranked) >= 2:
        top_cat, top_sc = ranked[0]
        run_cat, run_sc = ranked[1]
        print(f"\nTop category: {top_cat} ({top_sc}), Runner-up: {run_cat} ({run_sc})")
        if (top_sc - run_sc) <= 2.0 and top_cat in first_positions and run_cat in first_positions:
            if first_positions[run_cat] < first_positions[top_cat]:
                print(f"  Boosting {run_cat} due to earlier mention.")
                scores[run_cat] += 2.0

    print("\nFinal Scores:")
    for cat, score in sorted(scores.items(), key=lambda x: -x[1]):
        if score > 0:
            print(f"  {cat}: {score}")

# Test with the exact text from the screenshot
text = "The image shows a sidewalk with some debris and a few leaves scattered about."
debug_scores(text.lower())
