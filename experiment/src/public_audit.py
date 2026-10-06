"""Verify the publishable evidence without credentials, a native binary or network."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from common import read_json, ROOT
from identical import PROTOCOL_HEADERS, payload
from run import is_correct
from bookstore import grade

COUNTS = ["input_tokens", "output_tokens", "total_tokens", "reasoning_tokens", "cached_input_tokens", "cache_write_input_tokens"]
FIELDS = {"id", "batch", "task", "number", "model", "effort", "repeat", "auth", "status", "eligible", "correct", "answer",
          "score", "max_score", *COUNTS, "seconds", "first_text_seconds", "wire_seconds", "wire_first_text_seconds",
          "sent_body_sha256", "sent_request_text", "protocol_headers", "endpoint", "started_utc", "completed_utc",
          "server", "native", "source_log_sha256"}
SERVER_FIELDS = {"model", "status", "reasoning", "service_tier", "max_output_tokens", "temperature", "top_p",
                 "counts", "answer", "completed_output_types", "event_type_counts"}


def verify(directory):
    manifest = read_json(directory / "manifest.json")
    contents = (directory / "records.jsonl").read_bytes()
    assert hashlib.sha256(contents).hexdigest() == manifest["records_sha256"]
    records = [json.loads(line) for line in contents.decode().splitlines()]
    assert len(records) == manifest["responses"]
    assert len({row["id"] for row in records}) == len(records)
    binary_hashes = set()
    planned = {}
    for batch in manifest["batches"]:
        for task in batch["tasks"]:
            binary_hashes.add(task["codex_sha256"])
            for name, expected in task["source_sha256"].items():
                assert hashlib.sha256((directory / "source" / batch["name"] / name).read_bytes()).hexdigest() == expected
            for number, job in enumerate(task["schedule"], 1):
                planned[batch["name"], task["task"], number] = job
    assert len(binary_hashes) == 1 and len(planned) == len(records)
    pairs = {}
    for row in records:
        assert set(row) == FIELDS and set(row["server"]) == SERVER_FIELDS
        assert set(row["native"]) == {"counts", "answer"}
        assert set(row["server"]["reasoning"]) == {"context", "effort", "mode", "summary"}
        assert set(row["server"]["counts"]) == set(row["native"]["counts"]) == set(COUNTS)
        assert set(row["endpoint"]) == {"host", "path"}
        expected_endpoint = {"host": "api.openai.com", "path": "/v1/responses"} if row["auth"] == "api" else {
            "host": "chatgpt.com", "path": "/backend-api/codex/responses"}
        assert row["endpoint"] == expected_endpoint
        assert row["eligible"] and row["status"] == row["server"]["status"] == "completed"
        assert row["server"]["model"] == row["model"]
        assert row["server"]["reasoning"]["effort"] == row["effort"]
        assert all(row[key] == value for key, value in planned[row["batch"], row["task"], row["number"]].items())
        request = row["sent_request_text"].encode()
        assert hashlib.sha256(request).hexdigest() == row["sent_body_sha256"]
        assert request == (directory / "requests" / row["task"] / f"request-{row['model']}-{row['effort']}.json").read_bytes()
        prompt = (ROOT / ("experiment/tasks/portfolio/prompt.txt" if row["task"] == "portfolio" else "experiment/tasks/bookstore/prompt.txt")).read_text()
        assert json.loads(request) == payload(prompt, (ROOT / "experiment/config/base-instructions.txt").read_text(), row["model"], row["effort"])
        assert row["protocol_headers"] == PROTOCOL_HEADERS
        assert row["answer"] == row["native"]["answer"] == row["server"]["answer"]
        for key in COUNTS:
            assert type(row[key]) is int and row[key] >= 0
            assert row[key] == row["server"]["counts"][key] == row["native"]["counts"][key]
        assert row["total_tokens"] == row["input_tokens"] + row["output_tokens"]
        assert row["reasoning_tokens"] <= row["output_tokens"]
        if row["task"] == "portfolio":
            correct = is_correct(row["answer"], read_json(ROOT / "experiment/tasks/portfolio/expected.json"))
        else:
            graded = grade(row["answer"], read_json(ROOT / "experiment/tasks/bookstore/rubric.json"))
            assert graded["score"] == row["score"]
            correct = graded["correct"]
        assert correct == row["correct"]
        key = row["batch"], row["task"], row["model"], row["effort"], row["repeat"]
        pairs.setdefault(key, []).append(row)
    for pair in pairs.values():
        assert len(pair) == 2 and {row["auth"] for row in pair} == {"api", "chatgpt"}
        assert pair[0]["sent_request_text"] == pair[1]["sent_request_text"]
    print(f"Public evidence verified: {len(records)} responses, {len(pairs)} matched pairs.")
    return records, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="*", type=Path, help="Public dataset folders; defaults to both published studies")
    args = parser.parse_args()
    for directory in args.directories or [ROOT / 'studies/initial/data', ROOT / 'studies/followup/data']:
        verify(directory)
