# Run the experiment yourself

[Back to the overview](../README.md)

This guide takes you from setup to a small test, then to a full batch and a
shareable dataset. Run the commands from the repository's root directory.

If you only want to check our published numbers, you can skip the account setup:

```sh
python3 scripts/public_audit.py
python3 scripts/analyze.py
```

To analyze just the additional batch:

```sh
python3 scripts/analyze.py --batch batch-2 --output reports/generated/batch-2
```

## Before you start

You will need Python 3.12 or later, Codex, an API key, a ChatGPT account with
access to the selected models, and a working operating-system credential store.
The live capture also needs mitmproxy, installed below.

Our tested setup was macOS 27 on Apple Silicon, Python 3.14.7, mitmproxy 12.2.1
and the desktop app's native `codex-cli 0.160.0`. Live runs on Linux, Windows and
other Codex builds have not been verified here.

On macOS, the harness detects the desktop's native executable. For another
installation, set `EXPERIMENT_CODEX` to the absolute path of the native Codex
executable, or pass `--codex` to setup and collection. Use the same executable
for both sign-ins. Shell/npm launchers are rejected because hashing a launcher
does not identify the underlying binary.

The run records the version and binary hash and checks that both accounts
support the selected models and thinking levels. It stops if they are unavailable.

## 1. Install the capture dependency

```sh
python3 -m venv .local/capture-venv
.local/capture-venv/bin/python -m pip install -r requirements-capture.txt
```

On Windows, use `.local/capture-venv/Scripts/python.exe` for the second command.

## 2. Set up the two sign-ins

```sh
python3 scripts/setup.py prepare
python3 scripts/setup.py login chatgpt
python3 scripts/setup.py login api
```

API login asks for a hidden key. Both logins use separate experiment homes and
the OS credential store, preserving your normal Codex login. The capture proxy's
certificate is trusted only by the experiment's child process; system trust is
unchanged. See the [official OpenAI authentication documentation](https://learn.chatgpt.com/docs/auth).

## 3. Check access and preview the schedule

These commands check sign-ins and model access, then display the planned calls.
They do not ask a model to answer anything:

```sh
python3 scripts/run.py --benchmark both --check
python3 scripts/run.py --benchmark both --repeats 10 --seed 61204
```

Before collecting, choose your sample size and analysis. Keep it fixed while
the run is underway. The [protocol](PROTOCOL.md) describes our two tasks,
thinking levels, pair ordering and measurements.

## 4. Start with a small test

This makes eight responses: one for each task/model/sign-in combination at
Medium. **Four calls use your paid API account; four use subscription allowance.**

```sh
python3 scripts/run.py --benchmark both --effort medium --execute --output results/smoke-new
python3 scripts/audit.py results/smoke-new
```

Inspect any audit failure before continuing. The runner retains the attempt
and stops rather than automatically retrying it.

## 5. Collect a full batch

One full batch has ten responses per task/model/level/sign-in: **240 responses,
including 120 paid API calls**.

```sh
python3 scripts/run.py --benchmark both --repeats 10 --seed 61204 --execute --output results/batch-new
python3 scripts/audit.py results/batch-new
python3 scripts/summarize.py results/batch-new
```

Use a new output folder for every collection. Incorrect completed answers stay
in the comparison. Errors and failed checks are retained, and missing telemetry
is not converted to zero.

Our two batches used seeds 61204 and 61205. Their API charges were estimated at
$0.1633 and $0.1591 from measured usage. Those figures are historical results;
the fifteen-minute response timeout does not cap spending.

## 6. Analyze and share the results

Full captures can include private native context. Export the measured fields
before sharing:

```sh
python3 scripts/export_public.py --collection results/batch-new --output data/my-reproduction
python3 scripts/analyze.py data/my-reproduction --output reports/generated/my-reproduction
```

The exporter verifies the original evidence, keeps the actual sent payloads,
answers, counters and latency, and removes private fields. It currently expects
the two public tasks and the known neutral request format. See the
[data guide](../data/2026-10-05/README.md) and [contribution guide](../CONTRIBUTING.md).

For two batches, pass `--collection` twice. Use `--looks` to record the number
of significance checks your study has made; our published study used two.
Keep individual batch reports as well as a combined analysis. Avoid repeatedly
adding samples until a p-value crosses a threshold.

## Where to look in the code

| File | What it does |
|---|---|
| `prompt.txt`, `benchmarks/bookstore/prompt.txt` | Define the two tasks |
| `settings.json`, `config/` | Select models, levels, seed and neutral instructions |
| `scripts/identical.py` | Define the complete model request and equality checks |
| `scripts/run.py` | Schedule pairs, check access, collect and grade |
| `scripts/codex_client.py` | Talk to the native Codex process |
| `scripts/capture.py`, `scripts/capture_addon.py` | Start the local proxy and record messages |
| `scripts/identical_addon.py` | Forward the controlled request and handle local prefix acknowledgements |
| `scripts/audit.py`, `scripts/export_public.py`, `scripts/public_audit.py` | Verify raw evidence, export and recheck public data |
| `scripts/analyze.py`, `scripts/paired_statistics.py` | Produce summaries and statistical comparisons |

Collection is sequential. The controller and analysis use Python's standard
library; mitmproxy is the declared live-capture dependency. The original measured
source is preserved in `data/2026-10-05/source/`.

To run the offline tests:

```sh
python3 -m unittest discover -s tests -q
```
