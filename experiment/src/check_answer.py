"""Check all 20 ways to choose three projects, without using a model."""
import itertools

from common import ROOT, read_json


def solve(problem):
    feasible = []
    for selected in itertools.combinations(problem["projects"], problem["choose"]):
        ids = {project["id"] for project in selected}
        cost = sum(project["cost"] for project in selected)
        if cost > problem["budget"]:
            continue
        if any(not any(project["category"] == category for project in selected)
               for category in problem["categories"]):
            continue
        if any(x in ids and y in ids for x, y in problem["conflicts"]):
            continue
        feasible.append({"ids": sorted(ids), "cost": cost,
                         "value": sum(project["value"] for project in selected)})
    feasible.sort(key=lambda answer: (-answer["value"], answer["cost"], answer["ids"]))
    return feasible[0], len(feasible)


if __name__ == "__main__":
    answer, count = solve(read_json(ROOT / "experiment/tasks/portfolio/problem.json"))
    if answer != read_json(ROOT / "experiment/tasks/portfolio/expected.json"):
        raise SystemExit("Reference answer differs from exhaustive enumeration")
    print(f"Reference answer verified: {count} feasible project sets.")
