"""Create a plain CSV and paired comparison; no model calls or statistical claims."""
import argparse
import csv
import difflib
import json
import statistics
from pathlib import Path

from common import ROOT, read_json, snapshot_file


def average(runs, key):
    values = [run.get(key) for run in runs]
    if not values or any(value is None for value in values):
        return "—"
    return f"{statistics.mean(values):.1f}"


def summarize(directory):
    manifest = read_json(directory / "manifest.json")
    path = directory / "runs.json"
    runs = read_json(path) if path.exists() else []
    columns = ["number", "repeat", "model", "effort", "auth", "status", "eligible",
               "reasoning_tokens", "input_tokens", "cached_input_tokens",
               "cache_write_input_tokens", "output_tokens", "total_tokens", "seconds",
               "first_text_seconds", "wire_first_text_seconds", "wire_seconds",
               "sent_model", "sent_effort", "server_model", "server_declared_effort", "wire_host", "wire_path",
               "identical_request_verified", "sent_body_sha256",
               "correct", "score", "max_score", "flags", "error", "thread_id", "turn_id"]
    with (directory / "runs.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(runs)
    repeats = manifest["settings"].get("repeats", 1)
    lines = ["# Reasoning-token comparison", "",
             f"Codex: {manifest['codex_version']}", "",
             f"Retained attempts: {len(runs)}; originally planned: {len(manifest['schedule'])}", "",
             "Positive delta means ChatGPT sign-in used more reported reasoning tokens.", "",
             "| Repeat | Model | Effort | API tokens | ChatGPT tokens | Delta | Correct API / ChatGPT |",
             "|---:|---|---|---:|---:|---:|---|"]
    display = lambda value: "—" if value is None else str(value)
    for model in manifest["settings"]["models"]:
        for effort in manifest["settings"]["efforts"]:
            for repeat in range(1, repeats + 1):
                pair = {run["auth"]: run for run in runs
                        if run["model"] == model and run["effort"] == effort
                        and run.get("repeat", 1) == repeat}
                api, chatgpt = pair.get("api", {}), pair.get("chatgpt", {})
                a, b = api.get("reasoning_tokens"), chatgpt.get("reasoning_tokens")
                matched = api.get("eligible") and chatgpt.get("eligible")
                delta = b - a if matched else None
                correct = f"{display(api.get('correct'))} / {display(chatgpt.get('correct'))}"
                lines.append(f"| {repeat} | {model} | {effort} | {display(a)} | {display(b)} | {display(delta)} | {correct} |")
    lines += ["", "## Summary", "",
              "| Model | Effort | Sign-in | Eligible / planned | Correct / eligible | Mean reasoning | Median reasoning | Range | Mean input | Mean cached input | Mean seconds |",
              "|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|"]
    for model in manifest["settings"]["models"]:
        for effort in manifest["settings"]["efforts"]:
            for auth in ["api", "chatgpt"]:
                valid = [run for run in runs if run["model"] == model and run["effort"] == effort
                         and run["auth"] == auth and run.get("eligible")]
                tokens = [run["reasoning_tokens"] for run in valid]
                median = f"{statistics.median(tokens):.1f}" if tokens else "—"
                span = f"{min(tokens)}–{max(tokens)}" if tokens else "—"
                correct = sum(bool(run.get("correct")) for run in valid)
                lines.append(f"| {model} | {effort} | {auth} | {len(valid)}/{repeats} | {correct}/{len(valid)} | "
                             f"{average(valid, 'reasoning_tokens')} | {median} | {span} | "
                             f"{average(valid, 'input_tokens')} | {average(valid, 'cached_input_tokens')} | "
                             f"{average(valid, 'seconds')} |")
    lines += ["", "Repeated trials on one fixed prompt describe this prompt and these sessions. They do not establish a difference across other tasks. Exact server revisions, hidden context, and backend settings are unknown. Cache warmth may vary across responses.", "",
              "Missing values remain missing. Flagged and failed attempts stay in the CSV and raw logs. "
              "A pair has no calculated delta unless both selected responses are eligible; any explicit replacement "
              "is documented below. Incorrect completed answers stay in the comparison."]
    for run in runs:
        if not run.get("eligible"):
            lines.append(f"\n- Attempt {run['number']}: {run.get('flags', [])} {run.get('error', '')}")
    continuation_path = directory / "continuation-plan.json"
    if continuation_path.exists():
        plan = read_json(continuation_path)
        lines += ["", "## Interrupted collection", "", plan["reason"], "",
                  f"The untouched scheduled attempts were completed first. Attempt {plan['replacement_attempt']} "
                  f"was an explicitly recorded replacement for attempt {plan['replacement_for_attempt']}. "
                  "The failed attempt remains in the raw logs and CSV with missing token counts. "
                  "No failed response was converted to a zero-token response. "
                  "The continuation's manifest and source snapshot are retained in the adjacent continuation folder."]
    if manifest["settings"].get("capture"):
        identical = manifest['settings'].get('identical')
        method = ("The MITM replaces the generating message with the same frozen, stateless request bytes for both sign-ins. "
                  "It fixes the non-authentication protocol headers and strips native tool descriptions, session metadata, "
                  "and response history. Codex's optional prefix warmup is acknowledged locally and is never sent upstream. "
                  "Actual model responses are forwarded unchanged. Native authentication and destination are preserved."
                  if identical else
                  "The local MITM records decoded HTTP/WebSocket bodies at Codex's actual chosen destination. "
                  "It does not override provider URLs, model catalogues, or request bodies.")
        lines += ["", "## Network capture and latency", "",
                  method + " Headers are redacted "
                  "except for a small allowlist of protocol metadata. Only the experiment child trusts the local CA; "
                  "system trust and normal sign-ins are unchanged. The proxy adds overhead to these latency measurements.", "",
                  "Time to first text means the first nonempty final-answer text delta, excluding private reasoning. "
                  "Client latency starts immediately before turn/start and ends at turn/completed. Wire latency "
                  "starts at the generating request observed by the proxy and ends at response.completed. "
                  "Process/proxy startup is outside both timings. All token columns and answers remain in runs.json and runs.csv.", "",
                  "| Attempt | Sign-in | Sent model / effort | Server model / declared effort | First text client (s) | Client total (s) | First text wire (s) | Wire total (s) |",
                  "|---:|---|---|---|---:|---:|---:|---:|"]
        if identical:
            verified = sum(bool(r.get('identical_request_verified')) for r in runs)
            lines[lines.index("## Network capture and latency") + 2:lines.index("## Network capture and latency") + 2] = [
                f"**Identical-body checks passed: {verified}/{len(runs)} retained attempts.** "
                "Every accepted attempt must match its frozen request byte for byte. Authentication/account headers, "
                "native endpoint, and WebSocket handshake nonce necessarily differ; these are not model-payload differences.", ""]
        seconds = lambda value: "—" if value is None else f"{value:.3f}"
        for run in runs:
            lines.append(f"| {run['number']} | {run['auth']} | {run.get('sent_model', '—')} / {run.get('sent_effort', '—')} | "
                         f"{run.get('server_model', '—')} / {run.get('server_declared_effort', '—')} | "
                         f"{seconds(run.get('first_text_seconds'))} | {seconds(run.get('seconds'))} | "
                         f"{seconds(run.get('wire_first_text_seconds'))} | {seconds(run.get('wire_seconds'))} |")
        if identical:
            for name, digest in manifest.get('request_body_sha256', {}).items():
                lines += ["", f"Frozen body: [{name}]({name}); SHA-256 `{digest}`."]
        lines += ["", "### Token details", "",
                  "Output tokens include reasoning tokens. Cached reads and cache writes are input details; "
                  "these columns must not be added to total tokens.", "",
                  "| Attempt | Sign-in | Input | Cached input | Cache-write input | Output | Reasoning | Total | Decision points |",
                  "|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
        for run in runs:
            values = [display(run.get(key)) for key in ['input_tokens', 'cached_input_tokens',
                      'cache_write_input_tokens', 'output_tokens', 'reasoning_tokens', 'total_tokens', 'score']]
            lines.append(f"| {run['number']} | {run['auth']} | " + ' | '.join(values) + ' |')
        lines += ["", "### Request body differences", "",
                  "Each diff compares the complete outgoing JSON message sequence, including non-generating prefix requests. "
                  "No fields, IDs, or path strings are normalized away. Different host/path/header metadata is retained in the wire logs.", ""]
        for repeat in range(1, repeats + 1):
            for model in manifest['settings']['models']:
                for effort in manifest['settings']['efforts']:
                    pair = {r['auth']: r for r in runs if r.get('repeat', 1) == repeat
                            and r['model'] == model and r['effort'] == effort}
                    if set(pair) != {'api', 'chatgpt'}:
                        continue
                    bodies = {}
                    for auth, run in pair.items():
                        path = directory / f"{run['number']:02d}-wire.jsonl"
                        events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
                        bodies[auth] = [e['body'] for e in events if e.get('direction') == 'out' and e.get('body') is not None]
                        (directory / f"{run['number']:02d}-requests.json").write_text(json.dumps(bodies[auth], indent=2) + '\n')
                        replies = [e['body'] for e in events if e.get('direction') == 'in' and e.get('body') is not None]
                        (directory / f"{run['number']:02d}-responses.json").write_text(json.dumps(replies, indent=2) + '\n')
                    diff = ''.join(difflib.unified_diff(
                        json.dumps(bodies['api'], indent=2, sort_keys=True).splitlines(True),
                        json.dumps(bodies['chatgpt'], indent=2, sort_keys=True).splitlines(True),
                        fromfile='api', tofile='chatgpt'))
                    name = f"pair-{repeat:02d}-{model}-{effort}-requests.diff"
                    (directory / name).write_text(diff or 'Outgoing JSON message sequences are identical.\n')
                    lines.append(f"- Repeat {repeat}, {model}, {effort}: [{name}]({name})")
    if manifest["settings"].get("benchmark") == "bookstore":
        benchmark = snapshot_file(directory, 'experiment/tasks/bookstore/rubric.json', 'benchmarks/bookstore/rubric.json').parent
        rubric = read_json(benchmark / "rubric.json")
        lines += ["", "## Incident decisions", "", rubric["scoring"], "",
                  "Both sign-ins used the corrected image-generation control. The original portfolio collection "
                  "used the earlier control, so a comparison between those prompts also changes that control. "
                  "The source snapshots preserve the collection code and controls. Configuration equality does "
                  "not prove identical full context or actual backend reasoning budgets.", "",
                  "| Sign-in | Decision points / possible | All four correct / eligible |",
                  "|---|---:|---:|"]
        for auth in ["api", "chatgpt"]:
            valid = [run for run in runs if run["auth"] == auth and run.get("eligible")]
            points = sum(run["score"] for run in valid)
            possible = sum(run["max_score"] for run in valid)
            correct = sum(run["correct"] for run in valid)
            lines.append(f"| {auth} | {points}/{possible} | {correct}/{len(valid)} |")
        lines += ["", "## Exact prompt", "", (benchmark / "prompt.txt").read_text().strip(),
                  "", "## Frozen answer rubric", "", "```json", json.dumps(rubric, indent=2), "```",
                  "", "## Answers for review", "",
                  "These explanations are retained verbatim and have not been scored for factual completeness or caveats."]
        for run in runs:
            lines += ["", f"### Attempt {run['number']}: {run['auth']} (repeat {run.get('repeat', 1)})",
                      "", "```json", run.get("answer", ""), "```"]
    notes = directory / "collection-notes.md"
    if notes.exists():
        lines[2:2] = [notes.read_text().strip(), ""]
    (directory / "report.md").write_text("\n".join(lines) + "\n")
    print(directory / "report.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "output/raw/initial")
    directory = parser.parse_args().directory
    tasks = [directory / "portfolio", directory / "bookstore"] if (directory / "plan.json").exists() else [directory]
    for task in tasks:
        summarize(task)
