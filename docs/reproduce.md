# Run the experiment yourself

[Back to the overview](../README.md)

This guide takes you from setup to a small test, then to a full batch and a
shareable dataset. Run the commands from the repository's root directory.

If you only want to check our published numbers, you can skip the account setup:

```sh
python3 -m experiment verify
python3 -m experiment analyze
```

To analyze just the second batch of the initial study:

```sh
python3 -m experiment analyze-study --batch batch-2 --output output/reports/initial/batch-2
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
.local/capture-venv/bin/python -m pip install -r experiment/requirements.txt
```

On Windows, use `.local/capture-venv/Scripts/python.exe` for the second command.

## 2. Set up the two sign-ins

```sh
python3 -m experiment setup prepare
python3 -m experiment setup login chatgpt
python3 -m experiment setup login api
```

API login asks for a hidden key. Both logins use separate experiment homes and
the OS credential store, preserving your normal Codex login. The capture proxy's
certificate is trusted only by the experiment's child process; system trust is
unchanged. See the [official OpenAI authentication documentation](https://learn.chatgpt.com/docs/auth).

## 3. Check access and preview the schedule

These commands check sign-ins and model access, then display the planned calls.
They do not ask a model to answer anything:

```sh
python3 -m experiment run --benchmark both --check
python3 -m experiment run --benchmark both --repeats 10 --seed 61204
```

Before collecting, choose your sample size and analysis. Keep it fixed while
the run is underway. The [protocol](protocol.md) describes our two tasks,
thinking levels, pair ordering and measurements.

## 4. Start with a small test

This makes eight responses: one for each task/model/sign-in combination at
Medium. **Four calls use your paid API account; four use subscription allowance.**

```sh
python3 -m experiment run --benchmark both --effort medium --execute --output output/raw/smoke-new
python3 -m experiment audit output/raw/smoke-new
```

Inspect any audit failure before continuing. The runner retains the attempt
and stops rather than automatically retrying it.

## 5. Collect a full batch

One full batch has ten responses per task/model/level/sign-in: **240 responses,
including 120 paid API calls**.

```sh
python3 -m experiment run --benchmark both --repeats 10 --seed 61204 --execute --output output/raw/batch-new
python3 -m experiment audit output/raw/batch-new
python3 -m experiment summarize output/raw/batch-new
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
python3 -m experiment export --collection output/raw/batch-new --output studies/my-reproduction/data
python3 -m experiment analyze-study studies/my-reproduction/data --output output/reports/my-reproduction
```

The exporter verifies the original evidence, keeps the actual sent payloads,
answers, counters and latency, and removes private fields. It currently expects
the two public tasks and the known neutral request format. See the
[data guide](../studies/initial/data/README.md) and [contribution guide](../CONTRIBUTING.md).

For two batches, pass `--collection` twice. Use `--looks` to record the number
of significance checks your study has made; our published study used two.
Keep individual batch reports as well as a combined analysis. Avoid repeatedly
adding samples until a p-value crosses a threshold.

For command options and implementation details, see the
[experiment code guide](../experiment/README.md). The [study index](../studies/README.md)
links the published data, results and immutable source snapshots.
