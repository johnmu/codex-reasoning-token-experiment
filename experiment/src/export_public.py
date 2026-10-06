"""Export audited local captures into an allowlisted public dataset. No model calls."""
import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from audit import audit
from common import ROOT, read_json, write_json
from identical import payload, PROTOCOL_HEADERS

TOKEN_NAMES = {"input_tokens": "inputTokens", "output_tokens": "outputTokens",
               "total_tokens": "totalTokens", "reasoning_tokens": "reasoningOutputTokens",
               "cached_input_tokens": "cachedInputTokens", "cache_write_input_tokens": "cacheWriteInputTokens"}
LATENCY = ["seconds", "first_text_seconds", "wire_seconds", "wire_first_text_seconds"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def extract(folder, row, batch):
    """Select measured fields; never copy native context, headers or opaque items."""
    number = row["number"]
    wire_path, native_path = folder / f"{number:02d}-wire.jsonl", folder / f"{number:02d}-events.jsonl"
    wire, native = read_lines(wire_path), read_lines(native_path)
    sent = next(event for event in wire if event.get("direction") == "out")
    completed = next(event for event in wire if event.get("direction") == "in"
                     and (event.get("body") or {}).get("type") == "response.completed")
    response = completed["body"]["response"]
    usage = response["usage"]
    server_counts = {"input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"],
                     "total_tokens": usage["total_tokens"],
                     "reasoning_tokens": usage["output_tokens_details"]["reasoning_tokens"],
                     "cached_input_tokens": usage["input_tokens_details"]["cached_tokens"],
                     "cache_write_input_tokens": usage["input_tokens_details"]["cache_write_tokens"]}
    native_usage = [event["params"]["tokenUsage"]["total"] for event in native
                    if event.get("method") == "thread/tokenUsage/updated"][-1]
    native_answers = [event["params"]["item"]["text"] for event in native if event.get("method") == "item/completed"
                      and event["params"]["item"].get("type") == "agentMessage"]
    assert len(native_answers) == 1 and native_answers[0] == row["answer"]
    headers = next(event["headers"] for event in wire if event["kind"] == "controlled_headers")
    task = folder.name
    prompt = (ROOT / ("experiment/tasks/portfolio/prompt.txt" if task == "portfolio" else "experiment/tasks/bookstore/prompt.txt")).read_text()
    expected = payload(prompt, (ROOT / "experiment/config/base-instructions.txt").read_text(), row["model"], row["effort"])
    # Export only these public tasks with the entire expected neutral payload.
    assert json.loads(sent["text"]) == expected
    assert sent["text"].encode() == (folder / f"request-{row['model']}-{row['effort']}.json").read_bytes()
    assert headers == PROTOCOL_HEADERS
    server_answer = "".join(event["body"]["text"] for event in wire if event.get("direction") == "in"
                            and (event.get("body") or {}).get("type") == "response.output_text.done")
    assert server_answer == row["answer"]
    event_types = Counter(event["body"]["type"] for event in wire if event.get("kind") == "message"
                          and event.get("direction") == "in" and isinstance(event.get("body"), dict))
    return {"id": f"{batch}-{task}-{number:03d}", "batch": batch, "task": task,
            **{key: row[key] for key in ["number", "model", "effort", "repeat", "auth", "status", "eligible", "correct", "answer"]},
            "score": row.get("score"), "max_score": row.get("max_score"),
            **{key: row[key] for key in TOKEN_NAMES}, **{key: row[key] for key in LATENCY},
            "sent_body_sha256": row["sent_body_sha256"], "sent_request_text": sent["text"],
            "protocol_headers": headers, "endpoint": {"host": sent["host"], "path": sent["path"]},
            "started_utc": sent["utc"], "completed_utc": completed["utc"],
            "server": {"model": response["model"], "status": response["status"],
                "reasoning": {key: response["reasoning"].get(key) for key in ["context", "effort", "mode", "summary"]},
                "service_tier": response.get("service_tier"),
                "max_output_tokens": response.get("max_output_tokens"),
                "temperature": response.get("temperature"), "top_p": response.get("top_p"),
                "counts": server_counts, "answer": server_answer,
                "completed_output_types": [item["type"] for item in response["output"]],
                "event_type_counts": dict(event_types)},
            "native": {"counts": {key: native_usage[name] for key, name in TOKEN_NAMES.items()}, "answer": native_answers[0]},
            "source_log_sha256": {"wire": digest(wire_path), "native": digest(native_path)}}


def export(collections, output, looks=1):
    records, batches, threads, turns, requests, sources = [], [], set(), set(), {}, []
    for index, collection in enumerate(collections, 1):
        batch = f"batch-{index}"
        tasks = []
        for task in ["portfolio", "bookstore"]:
            folder = collection / task
            audit_result = audit(folder)  # Independently verify the original evidence first.
            manifest = read_json(folder / "manifest.json")
            rows = read_json(folder / "runs.json")
            for row in rows:
                assert row["thread_id"] not in threads and row["turn_id"] not in turns
                threads.add(row["thread_id"])
                turns.add(row["turn_id"])
                records.append(extract(folder, row, batch))
            for name in manifest["request_body_sha256"]:
                key = f"{task}/{name}"
                contents = (folder / name).read_bytes()
                assert key not in requests or requests[key] == contents
                requests[key] = contents
            accounts = read_json(folder / "sign-ins.json")
            tasks.append({"task": task, "settings": manifest["settings"], "schedule": manifest["schedule"],
                          "codex_version": manifest["codex_version"], "codex_sha256": manifest["codex_sha256"],
                          "account_types_and_plans": {auth: {key: value.get(key) for key in ["type", "plan"]}
                                                      for auth, value in accounts.items()},
                          "request_body_sha256": manifest["request_body_sha256"],
                          "source_sha256": {name: value for name, value in manifest["source_sha256"].items() if Path(name).name != "README.md"},
                          "original_raw_audit_passed": audit_result["passed"],
                          "original_manifest_sha256": digest(folder / "manifest.json")})
            sources.append((folder, batch, task))
        batches.append({"name": batch, "tasks": tasks})
    # Fail rather than export any record with a mismatched or missing count.
    for row in records:
        assert all(type(row[key]) is int and row[key] == row["native"]["counts"][key] == row["server"]["counts"][key]
                   for key in TOKEN_NAMES)
    output.mkdir(parents=True, exist_ok=False)
    for name, contents in requests.items():
        destination = output / "requests" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(contents)
    # Historical authored source is copied unchanged; no native binary or login files.
    for folder, batch, task in sources:
        manifest = read_json(folder / "manifest.json")
        for name in manifest["source_sha256"]:
            if Path(name).name == "README.md":
                continue
            destination = output / "source" / batch / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            contents = (folder / "source" / name).read_bytes()
            if destination.exists():
                assert destination.read_bytes() == contents
            else:
                destination.write_bytes(contents)
    (output / "records.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
    write_json(output / "manifest.json", {"format_version": 1, "batches": batches, "responses": len(records),
        "original_unique_threads": len(threads), "original_unique_turns": len(turns), "analysis_looks": looks,
        "scope": "Allowlisted projection of original audited captures; not unmodified full wire/native logs.",
        "omitted": ["credentials and account identifiers", "thread/turn/response identifiers", "local paths and native context",
                    "HTTP authentication/transport headers", "encrypted reasoning and unrelated response metadata"],
        "records_sha256": digest(output / "records.jsonl")})
    from public_audit import verify
    verify(output)
    print(f"Exported {len(records)} audited responses to {output}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--looks", type=int, default=1, help="Number of significance looks (published study: 2)")
    args = parser.parse_args()
    if args.looks < 1:
        parser.error("--looks must be positive")
    export(args.collection, args.output, args.looks)
