"""Grade four incident-diagnosis decisions locally; retain prose for review."""
import json


def grade(answer, rubric):
    try:
        decisions = json.loads(answer)
    except ValueError:
        decisions = {}
    if not isinstance(decisions, dict):
        decisions = {}
    matches = {key: decisions.get(key) == value
               for key, value in rubric["expected_decisions"].items()}
    return {"score": sum(matches.values()), "max_score": len(matches),
            "correct": all(matches.values()), "decision_matches": matches}
