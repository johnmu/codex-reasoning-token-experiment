"""Check either task's frozen source, identical requests, answers and token counts.

This is an offline audit. It reads evidence and writes audit.json; no model calls.
"""
import argparse
import hashlib
import json
import statistics
from pathlib import Path
from common import snapshot_file


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(directory):
    manifest = read(directory / "manifest.json")
    runs = read(directory / "runs.json")
    headers = read(directory / "request-headers.json")
    assert digest(directory / "request-headers.json") == manifest["protocol_headers_sha256"]
    for name, expected in manifest["source_sha256"].items():
        assert digest(directory / "source" / name) == expected, name
    # A shared results folder can be audited on a machine without the Mac binary.
    binary = Path(manifest["codex_path"])
    binary_matches = digest(binary) == manifest["codex_sha256"] if binary.is_file() else None
    assert len(runs) == len(manifest["schedule"])
    assert len({r["thread_id"] for r in runs}) == len(runs)
    assert len({r["turn_id"] for r in runs}) == len(runs)
    response_ids, verified = set(), []
    for run, planned in zip(runs, manifest["schedule"]):
        number = run["number"]
        assert all(run[k] == v for k, v in planned.items()), number
        body_file = directory / f"request-{run['model']}-{run['effort']}.json"
        expected = body_file.read_bytes()
        assert digest(body_file) == manifest["request_body_sha256"][body_file.name]
        events = [json.loads(line) for line in
                  (directory / f"{number:02d}-wire.jsonl").read_text().splitlines()]
        sent = [e for e in events if e.get("direction") == "out"]
        assert len(sent) == 1 and sent[0]["text"].encode() == expected, number
        assert sent[0]["body"] == json.loads(expected), number
        assert sent[0]["body"]["model"] == run["model"]
        assert sent[0]["body"]["reasoning"]["effort"] == run["effort"]
        assert sent[0]["body"]["tools"] == []
        controlled = [e for e in events if e["kind"] == "controlled_headers"]
        assert len(controlled) == 1 and controlled[0]["headers"] == headers, number
        assert not any(e["kind"] == "blocked_request" for e in events), number
        completed = [e for e in events if e.get("direction") == "in"
                     and (e.get("body") or {}).get("type") == "response.completed"]
        assert len(completed) == 1, number
        response = completed[0]["body"]["response"]
        assert response["id"] not in response_ids
        response_ids.add(response["id"])
        assert response["status"] == "completed" and response["error"] is None
        assert response["model"] == run["model"]
        assert response["reasoning"]["effort"] == run["effort"]
        usage = response["usage"]
        counts = {"input_tokens": usage["input_tokens"],
                  "output_tokens": usage["output_tokens"],
                  "total_tokens": usage["total_tokens"],
                  "reasoning_tokens": usage["output_tokens_details"]["reasoning_tokens"],
                  "cached_input_tokens": usage["input_tokens_details"]["cached_tokens"],
                  "cache_write_input_tokens": usage["input_tokens_details"]["cache_write_tokens"]}
        native = [json.loads(line) for line in
                  (directory / f"{number:02d}-events.jsonl").read_text().splitlines()]
        last_usage = [e["params"]["tokenUsage"]["total"] for e in native
                      if e.get("method") == "thread/tokenUsage/updated"][-1]
        native_names = {"input_tokens": "inputTokens", "output_tokens": "outputTokens",
                        "total_tokens": "totalTokens", "reasoning_tokens": "reasoningOutputTokens",
                        "cached_input_tokens": "cachedInputTokens",
                        "cache_write_input_tokens": "cacheWriteInputTokens"}
        for name, count in counts.items():
            assert type(count) is int and count >= 0
            assert run[name] == count == last_usage[native_names[name]], (number, name)
        assert counts["total_tokens"] == counts["input_tokens"] + counts["output_tokens"]
        assert counts["reasoning_tokens"] <= counts["output_tokens"]
        answers = [e["body"]["text"] for e in events if e.get("direction") == "in"
                   and (e.get("body") or {}).get("type") == "response.output_text.done"]
        assert "".join(answers) == run["answer"] == run["server_answer"], number
        assert run["eligible"] and not run["flags"] and run["identical_request_verified"]
        assert run["sent_body_sha256"] == digest(body_file)
        if run["first_text_seconds"] is not None:
            assert 0 <= run["first_text_seconds"] <= run["seconds"]
        if run["wire_first_text_seconds"] is not None:
            assert 0 <= run["wire_first_text_seconds"] <= run["wire_seconds"]
        try:
            answer = json.loads(run["answer"])
        except ValueError:
            answer = None  # Malformed answers are incorrect, not missing attempts.
        if manifest["settings"]["benchmark"] == "bookstore":
            rubric = read(snapshot_file(directory, 'experiment/tasks/bookstore/rubric.json', 'benchmarks/bookstore/rubric.json'))
            decisions = answer if isinstance(answer, dict) else {}
            score = sum(decisions.get(name) == value for name, value in rubric["expected_decisions"].items())
            correct = score == len(rubric["expected_decisions"])
            assert score == run["score"]
        else:
            expected_answer = read(snapshot_file(directory, 'experiment/tasks/portfolio/expected.json', 'expected.json'))
            correct = json.dumps(answer, sort_keys=True) == json.dumps(expected_answer, sort_keys=True)
        assert correct == run["correct"]
        for event in events:
            for name, value in event.get("headers", {}).items():
                if name.lower() in {"authorization", "cookie", "set-cookie", "chatgpt-account-id"}:
                    assert value == "[redacted]", (number, name)
        verified.append({"number": number, "auth": run["auth"],
                         "body_sha256": run["sent_body_sha256"],
                         "server_reasoning": response["reasoning"],
                         "server_output_types": [item["type"] for item in response["output"]],
                         "counts": counts})
    summary = {}
    for auth in ["api", "chatgpt"]:
        rows = [r for r in runs if r["auth"] == auth]
        summary[auth] = {"responses": len(rows), "correct": sum(r["correct"] for r in rows),
                         "reasoning_counts": [r["reasoning_tokens"] for r in rows]}
        for key in ["reasoning_tokens", "input_tokens", "cached_input_tokens", "output_tokens",
                    "cache_write_input_tokens", "total_tokens", "seconds", "first_text_seconds",
                    "wire_seconds", "wire_first_text_seconds"]:
            values = [r.get(key) for r in rows]
            if any(value is None for value in values):
                summary[auth][key] = None
                continue
            summary[auth][key] = {"mean": statistics.mean(values),
                                  "median": statistics.median(values),
                                  "min": min(values), "max": max(values)}
    result = {"passed": True, "attempts": len(runs), "verified": verified,
              "request_body_sha256": manifest["request_body_sha256"], "summary": summary,
              "current_binary_matches_manifest": binary_matches,
              "internal_model_revision_and_budget_verified": False}
    print(f"Audit passed: {len(runs)} identical requests; raw server and native token counts match.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    directory = parser.parse_args().directory
    tasks = [directory / "portfolio", directory / "bookstore"] if (directory / "plan.json").exists() else [directory]
    for task in tasks:
        result = audit(task)
        (task / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
