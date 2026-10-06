"""Public-data privacy boundaries, independent evidence checks and exact statistics."""
import hashlib
import json
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from common import ROOT, native_codex, write_json
from export_public import extract, TOKEN_NAMES
from public_audit import verify
from paired_statistics import distribution, tail_probability, holm
from check_public import findings
from analyze import analyze

DATA = ROOT / "data/2026-10-05"


class PublicTests(unittest.TestCase):
    def test_published_data_and_recomputed_results(self):
        with tempfile.TemporaryDirectory() as name:
            analyze(DATA, Path(name))
            summary = json.loads((Path(name) / "summary.json").read_text())
            self.assertEqual(summary["responses"], 480)
            self.assertAlmostEqual(summary["estimated_api_cost_usd"], .3224745)
            stats = json.loads((Path(name) / "significance.json").read_text())
            luna = next(row for row in stats["results"] if (row["task"], row["model"], row["effort"]) == ("bookstore", "gpt-6-luna", "medium"))
            self.assertAlmostEqual(luna["reasoning_tokens"]["holm_all_looks"], .0001155058726456348)

    def test_altered_usage_and_extra_private_fields_are_rejected(self):
        for change in ["counts", "private"]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as name:
                folder = Path(name) / "data"
                shutil.copytree(DATA, folder)
                path = folder / "records.jsonl"
                rows = [json.loads(line) for line in path.read_text().splitlines()]
                if change == "counts":
                    rows[0]["server"]["counts"]["reasoning_tokens"] += 1
                else:
                    rows[0]["server"]["encrypted_content"] = "opaque"
                path.write_text("".join(json.dumps(row) + "\n" for row in rows))
                manifest = json.loads((folder / "manifest.json").read_text())
                manifest["records_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                write_json(folder / "manifest.json", manifest)
                with self.assertRaises(AssertionError):
                    verify(folder)

    def test_export_omits_unselected_native_context_and_opaque_response_fields(self):
        row = json.loads((DATA / "records.jsonl").read_text().splitlines()[0])
        private = "private-" + "value-" + "for-export-test"
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name) / row["task"]
            folder.mkdir()
            number = row["number"]
            (folder / f"request-{row['model']}-{row['effort']}.json").write_text(row["sent_request_text"])
            usage = {"input_tokens": row["input_tokens"], "output_tokens": row["output_tokens"], "total_tokens": row["total_tokens"],
                     "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                     "output_tokens_details": {"reasoning_tokens": row["reasoning_tokens"]}}
            response = {"model": row["model"], "status": "completed", "reasoning": row["server"]["reasoning"], "usage": usage,
                        "output": [{"type": "reasoning", "encrypted_content": private}], "metadata": {"account": private}}
            wire = [{"kind": "native_original_message", "body": {"instructions": private}},
                    {"kind": "controlled_headers", "headers": row["protocol_headers"]},
                    {"kind": "message", "direction": "out", "text": row["sent_request_text"], "body": json.loads(row["sent_request_text"]),
                     "host": row["endpoint"]["host"], "path": row["endpoint"]["path"], "utc": row["started_utc"]},
                    {"kind": "message", "direction": "in", "body": {"type": "response.completed", "response": response}, "utc": row["completed_utc"]},
                    {"kind": "message", "direction": "in", "body": {"type": "response.output_text.done", "text": row["answer"]}}]
            native = [{"method": "thread/started", "params": {"private": private}},
                      {"method": "thread/tokenUsage/updated", "params": {"tokenUsage": {"total": {key: row[field] for field, key in TOKEN_NAMES.items()}}}},
                      {"method": "item/completed", "params": {"item": {"type": "agentMessage", "text": row["answer"]}}}]
            for suffix, events in [("wire", wire), ("events", native)]:
                (folder / f"{number:02d}-{suffix}.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events))
            exported = extract(folder, row, "test-batch")
            self.assertNotIn(private, json.dumps(exported))
            self.assertEqual(exported["server"]["counts"]["reasoning_tokens"], row["reasoning_tokens"])

    def test_exact_twenty_pair_probability_and_holm(self):
        pairs = [{"api": {"number": 2*i+1, "tokens": 1}, "chatgpt": {"number": 2*i+2, "tokens": 0}} for i in range(10)]
        observed, weights = distribution(pairs, "tokens", 60, 30)
        expected = 2 * (math.comb(50, 20) / math.comb(60, 30)) ** 2
        self.assertAlmostEqual(tail_probability([weights, weights], observed * 2), expected)
        self.assertEqual(tail_probability([{0: 1}], 0), 1)
        self.assertEqual(holm([.01, .02, .5]), [.03, .04, .5])

    def test_launchers_are_rejected_and_native_executable_is_resolved(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "codex"
            path.write_bytes(b"#!/bin/sh\n")
            with self.assertRaises(RuntimeError):
                native_codex(str(path))
            path.write_bytes(b"\x7fELF")
            self.assertEqual(native_codex(str(path)), str(path.resolve()))

    def test_public_check_reports_categories_without_secret_values(self):
        secret = "sk-" + "not-a-real-key-" + "x" * 40
        self.assertIn("API-key-like value", findings("data/secret.json", secret.encode()))
        self.assertIn("private file", findings(".local/auth.json", b"{}"))
        self.assertEqual(findings("README.md", b"Bearer $OPENAI_API_KEY"), [])
