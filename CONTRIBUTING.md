# Contribute a reproduction

Both reproductions and negative results are useful. Preserve the published
October 5 dataset; add a new folder for your run.

Before collecting, record your model IDs, thinking levels, tasks, sample size,
seed and statistical comparisons. Start with the small test in the
[setup and run guide](docs/reproduce.md). Keep
every attempt and report any failure or incompatibility. Never silently rerun,
replace failed trials or select the most favorable answers.

For the primary comparison, use the same native binary for both isolated
sign-ins and leave the generating payload unchanged. A different prompt,
transport, provider, tool context or multi-turn protocol is a new study; label it.

## What to submit

- CLI version and native binary hash, OS/architecture, Python and mitmproxy.
- Model/effort support, subscription plan, collection date and safe policy context.
- Exact tasks, instructions, payloads, schedule and predeclared sample size.
- Public export containing all counts, answers and latency, plus audit output.
- Batch-level summaries, analysis method and correction scope.
- Any code changes, failures, missing telemetry and departures from the protocol.

Use the [run guide's export command](docs/reproduce.md#6-analyze-and-share-the-results). The exporter requires the two
public tasks and known neutral payload; modified private prompts require a
separate reviewed export. Full captures and private native logs remain ignored.

Do not submit keys, cookies, login files, account IDs, CA private keys, encrypted
reasoning, personal paths or private repository context. The export is an
allowlisted projection; inspect its answers as well as the metadata.

Offline checks before submitting:

```sh
python3 -B -m unittest discover -s tests -q
python3 -B -m experiment verify studies/my-reproduction/data
git add studies/my-reproduction/data
python3 -B -m experiment check-public --staged
```

All CI checks are offline and need no login. The privacy checker reports file
names and categories, never matching values. It is a guard against accidental
disclosure rather than a guarantee for arbitrary datasets.
