# The 480-response follow-up

This adds twenty completed responses per sign-in to every original task/model/
thinking-level combination. Together, the original and follow-up datasets contain
960 completed responses, or forty per sign-in in each condition.

The [fixed plan](../../docs/CONFIRMATION_PLAN.md) was published before collection.
Two ChatGPT-sign-in requests on the project task returned a server-capacity
error. Collection stopped for inspection each time, and manual continuations
were documented before resuming. The original stopped collections remain
unchanged locally. There were **482 attempts: 240 API and 242 subscription**.
See the [amendment](../../docs/CONFIRMATION_AMENDMENT.md) and
[failure records](runtime-errors.json).

## What is included

- `records.jsonl`: all 480 completed answers, grades, server/native counters,
  latency and actual sent request text.
- `requests/`: twelve exact request files, unchanged from the original study.
- `manifest.json`: schedules, settings, client hash, account types/plans,
  source hashes, segment provenance and the failure-file hash.
- `runtime-errors.json`: both failed attempts, their service error codes and
  evidence hashes. Unavailable answers and reasoning counts are `null`.
- `source/`: unchanged measured source snapshots, including separate versions
  for each task and collection segment. Historical README files are omitted.

This is an allowlisted projection, rather than full native or network logs.
Credentials, account/session identifiers, private native context, local paths,
authentication headers and opaque encrypted reasoning are omitted. Answers,
request bytes, counters and latency are preserved. Completed record numbers
refer to slots in the original schedule; segment provenance maps those slots
back to the unchanged raw records. The source archives preserve each segment's
actual files; the request-generation and grading code was identical throughout.
Assembly metadata also records the collection's separately retained failures;
both occurred on the project task.

All 962 attempts across the original study and follow-up have distinct native
thread and turn identifiers, verified locally before export. The published
identifiers are anonymous. Raw-log hashes are commitments; omitted private
logs cannot be reconstructed from this projection.

## Check the results

Run these from the repository root with Python 3.12 or later. They make no model
calls and require no credentials:

```sh
python3 scripts/public_audit.py data/confirmation-2026-10-05
python3 scripts/analyze_followup.py data/confirmation-2026-10-05 --output reports/generated/followup
```

The new batch uses the planned exact paired tests and Holm correction over
36 outcomes, with one final look. The pooled accuracy analysis retains the
three separate batch/order constraints and uses a conservative factor of
36 outcomes times three significance looks. It remains exploratory.

These comparisons describe completed responses, rather than overall service
availability per attempt. The interruptions limit interpretation as confirmation
of the original study. The [published report](../../reports/confirmation-2026-10-05/report.md)
includes both the standalone and pooled results; its
[CSV](../../reports/confirmation-2026-10-05/new-batch/runs.csv) contains the new
answers, token counts and timings.
