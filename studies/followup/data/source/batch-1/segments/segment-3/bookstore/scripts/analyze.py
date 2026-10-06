"""Regenerate CSV, descriptive results and paired tests from public evidence."""
import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

from common import ROOT, write_json
from paired_statistics import distribution, tail_probability, holm
from public_audit import verify

METRICS = ["reasoning_tokens", "correct", "seconds"]
RATES = {"gpt-6-luna": {"input": .10, "output": .50}, "gpt-6.1-sol": {"input": 2., "output": 10.}}
NUMERIC = ["input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_tokens",
           "total_tokens", "seconds", "first_text_seconds", "wire_seconds", "wire_first_text_seconds"]


def analyze(data, output, batch=None, looks=None):
    rows, manifest = verify(data)
    if batch:
        rows = [row for row in rows if row["batch"] == batch]
        assert rows, "Unknown batch"
    looks = looks if looks is not None else (1 if batch else manifest["analysis_looks"])
    assert looks >= 1
    blocks = {}
    for item in manifest["batches"]:
        for task in item["tasks"]:
            schedule = task["schedule"]
            blocks[item["name"], task["task"]] = (len(schedule) // 2, sum(job["auth"] == "api" for job in schedule[::2]))
    paired = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for row in rows:
        paired[row["task"], row["model"], row["effort"]][row["batch"]][row["repeat"]][row["auth"]] = row
    order = lambda key: (key[0] != "portfolio", key[1], ["low", "medium", "high"].index(key[2]))
    results, groups = [], []
    for key in sorted(paired, key=order):
        result = {"task": key[0], "model": key[1], "effort": key[2]}
        for metric in METRICS:
            permutations = [distribution(list(pairs.values()), metric, *blocks[name, key[0]])
                            for name, pairs in paired[key].items()]
            observed = sum(item[0] for item in permutations)
            sample = [row for row in rows if (row["task"], row["model"], row["effort"]) == key]
            result[metric] = {"api_mean": statistics.mean(row[metric] for row in sample if row["auth"] == "api"),
                             "chatgpt_mean": statistics.mean(row[metric] for row in sample if row["auth"] == "chatgpt"),
                             "difference": observed / (len(sample) // 2),
                             "p": tail_probability([item[1] for item in permutations], observed)}
        results.append(result)
        for auth in ["api", "chatgpt"]:
            sample = [row for row in rows if (row["task"], row["model"], row["effort"], row["auth"]) == (*key, auth)]
            group = {"task": key[0], "model": key[1], "effort": key[2], "auth": auth, "responses": len(sample),
                     "correct": sum(row["correct"] for row in sample), "zero_reasoning": sum(row["reasoning_tokens"] == 0 for row in sample)}
            for field in NUMERIC:
                values = [row[field] for row in sample]
                group[field] = None if any(value is None for value in values) else {
                    "mean": statistics.mean(values), "median": statistics.median(values), "min": min(values), "max": max(values)}
            groups.append(group)
    for metric in METRICS:
        for row, p in zip(results, holm([result[metric]["p"] for result in results])):
            row[metric]["holm_metric"] = p
            row[metric]["holm_metric_looks"] = min(1., p * looks)
    adjusted = holm([row[metric]["p"] for row in results for metric in METRICS])
    for index, row in enumerate(results):
        for position, metric in enumerate(METRICS):
            p = adjusted[index * 3 + position]
            row[metric]["holm_all"] = p
            row[metric]["holm_all_looks"] = min(1., p * looks)
    output.mkdir(parents=True, exist_ok=True)
    columns = ["id", "batch", "task", "number", "repeat", "model", "effort", "auth", *NUMERIC, "correct", "score", "max_score", "answer", "sent_body_sha256"]
    with (output / "runs.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    # Output includes reasoning; cached reads/writes are zero in this release.
    assert all(row["cached_input_tokens"] == row["cache_write_input_tokens"] == 0 for row in rows), "Use cache-aware pricing for other datasets."
    cost = sum((row["input_tokens"] * RATES[row["model"]]["input"] + row["output_tokens"] * RATES[row["model"]]["output"]) / 1e6
               for row in rows if row["auth"] == "api")
    write_json(output / "summary.json", {"responses": len(rows), "estimated_api_cost_usd": cost, "groups": groups})
    write_json(output / "significance.json", {"metrics": METRICS, "conditions": len(results), "looks": looks, "results": results})
    counts = {metric: sum(row[metric]["holm_all_looks"] < .05 for row in results) for metric in METRICS}
    lines = ["# Published experiment results", "", f"{len(rows)} responses. Exact paired tests; Holm correction over "
             f"{len(results) * 3} comparisons with a {looks}-look factor. Significant at 5%: "
             f"{counts['reasoning_tokens']} reasoning-token differences, {counts['correct']} accuracy differences, "
             f"{counts['seconds']} client-latency differences.", "",
             "Means below are reported reasoning tokens. Correctness is exact project selection or the four bookstore decisions; explanation prose is not graded.", "",
             "| Task | Model | Level | API tokens | ChatGPT tokens | API correct | ChatGPT correct | API seconds | ChatGPT seconds |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for index in range(0, len(groups), 2):
        a, b = groups[index:index + 2]
        lines.append(f"| {a['task']} | {a['model']} | {a['effort']} | {a['reasoning_tokens']['mean']:.2f} | {b['reasoning_tokens']['mean']:.2f} | "
                     f"{a['correct']}/{a['responses']} | {b['correct']}/{b['responses']} | {a['seconds']['mean']:.2f} | {b['seconds']['mean']:.2f} |")
    lines += ["", f"API charge estimate: **${cost:.4f}**, calculated from measured input and output tokens. "
              "Output already includes reasoning; cache reads and writes are zero. "
              "[Recorded Standard pricing](https://developers.openai.com/api/docs/pricing): Luna $0.10/$0.50 and Sol 6.1 $2/$10 per million input/output tokens. "
              "This is not a verified invoice.", "", "## Statistical comparisons", "",
              "Raw p-values and corrections are exploratory for the original and pooled study. The extension rules were frozen before its collection. "
              "The factor of two conservatively accounts for examining significance at ten and twenty pairs. "
              "Randomization weights retain the first/second order balance separately within each task/batch. "
              "The interpretation assumes no carryover between adjacent calls. Nonsignificance does not establish equivalence. "
              "These two prompts do not establish a general capability difference or a hidden server cause.", ""]
    for metric in METRICS:
        lines += [f"### {metric}", "", "| Task | Model | Level | API − ChatGPT | Raw p | Metric-family correction + looks | All-outcomes correction + looks |",
                  "|---|---|---|---:|---:|---:|---:|"]
        for row in results:
            value = row[metric]
            lines.append(f"| {row['task']} | {row['model']} | {row['effort']} | {value['difference']:.3f} | {value['p']:.6g} | "
                         f"{value['holm_metric_looks']:.6g} | {value['holm_all_looks']:.6g} |")
        lines.append("")
    lines += ["[All responses](runs.csv) · [Group statistics](summary.json) · [Exact p-values](significance.json)"]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    print(f"Analyzed {len(rows)} public records; API estimate ${cost:.4f}. {counts}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path, default=ROOT / "data/2026-10-05")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/generated")
    parser.add_argument("--batch", help="Analyze only one public batch")
    parser.add_argument("--looks", type=int, help="Override the manifest's number of significance looks")
    args = parser.parse_args()
    analyze(args.data, args.output, args.batch, args.looks)
