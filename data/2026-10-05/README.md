# Public evidence: October 5, 2026

This dataset contains all 480 responses in the two full controlled batches.
Early pilots, rejected prompts, failed prototypes and unmodified-request
diagnostics are retained locally and are not pooled into this release.

- `records.jsonl`: one anonymous record per measured response, including the
  actual sent request text, server/native counts and answers, four latencies,
  endpoint, event-type counts and safe returned parameter metadata.
- `manifest.json`: schedules, seeds, settings, CLI version/native hash, plan
  type, source hashes, original audit outcome and data checksum.
- `requests/`: twelve frozen payload files, unchanged across sign-ins/batches.
- `source/batch-1/` and `source/batch-2/`: unchanged measured source and task
  snapshots. The older runner lacks the later optional `--seed` argument.

The public record is an **allowlisted projection**, not a complete verbatim
wire or native transcript. Credentials, account and runtime IDs, local paths,
native pre-proxy context, HTTP authentication/transport headers, opaque
reasoning and unrelated metadata are excluded. Answers, counters, latencies
and actual generating bytes are unchanged. Anonymous record IDs replace
runtime correlation IDs. Original log SHA-256 values are commitments to the
retained private logs, not proof that those unavailable logs can be reconstructed.

`scripts/export_public.py` independently audits originals before selection.
`scripts/public_audit.py` rechecks the shared request bytes, schedule, source
hashes, all six counter readings, answers and grading from this projection.
The exporter verified 480 distinct original thread and turn IDs. Public
consumers can check anonymous record uniqueness, not inspect the omitted IDs.

Reproduce without a login or network:

```sh
python3 -B scripts/public_audit.py data/2026-10-05
python3 -B scripts/analyze.py data/2026-10-05 --output reports/generated
```

Analysis defaults to both batches and a two-look adjustment. Select `--batch
batch-1` or `--batch batch-2` for a ten-pair analysis with one look.

The Python, macOS and dependency versions are described in the
[setup and run guide](../../docs/REPRODUCE.md#before-you-start).
Exact native binary version/hash and account **type/plan only** are in the
manifest. The binary and credential store are not distributed.
