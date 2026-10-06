# Run and understand the experiment

All current commands use one entry point from the repository root:

```sh
python3 -m experiment --help
```

You need only Python 3.12 or later to verify and analyze the published data.
Live collection also needs Codex, both sign-ins and mitmproxy. The
[setup guide](../docs/reproduce.md) walks through those steps.

## Commands

| Command | Purpose |
|---|---|
| `verify [dataset ...]` | Check both published datasets, or specific public datasets |
| `analyze` | Regenerate the fixed follow-up and pooled accuracy results |
| `analyze-study [dataset]` | Analyze one study; defaults to the initial study |
| `setup prepare` / `setup login api` / `setup login chatgpt` | Prepare isolated homes or sign in |
| `run` | Preview a collection; `--execute` starts model calls |
| `audit <collection>` | Check private raw captures against the frozen requests |
| `summarize <collection>` | Summarize private raw captures |
| `export --collection … --output …` | Produce an allowlisted public dataset |
| `check-public [--staged]` | Scan Git's publication files for private information |

Use `python3 -m experiment <command> --help` for options. Generated reports and
new raw collections go under the ignored `output/` directory. Isolated sign-ins
and the capture environment live under the ignored `.local/` directory.

## Where the code and inputs live

| Location | What to look for |
|---|---|
| [tasks/](tasks/) | Both prompts and their locally checked reference answers |
| [config/](config/) | Models, thinking levels, seed, client settings and neutral instructions |
| [src/identical.py](src/identical.py) | Every model-request field and the equality checks |
| [src/run.py](src/run.py) | Pair schedule, collection, grading and stop-on-error behavior |
| [src/codex_client.py](src/codex_client.py) | Native Codex JSON-line protocol adapter |
| [src/capture.py](src/capture.py) and its addons | Local proxy and unchanged server-response capture |
| [src/audit.py](src/audit.py), [src/export_public.py](src/export_public.py), [src/public_audit.py](src/public_audit.py) | Raw verification, public export and public-data verification |
| [src/analyze.py](src/analyze.py), [src/analyze_followup.py](src/analyze_followup.py), [src/paired_statistics.py](src/paired_statistics.py) | Descriptive and exact statistical calculations |

The command entry point only dispatches to these modules. Collection is
sequential. Analysis and orchestration use the standard library; the live
capture dependency is pinned in [requirements.txt](requirements.txt).

The immutable measured source lives inside each [study's data](../studies/README.md),
separate from the current runnable code. Moving current files does not alter
the recorded prompts, request bytes, measurements, plans or source hashes.
