# Same model. Same prompt. 16× more reasoning tokens through the API?

On our bookstore task, Luna 6 at Medium reported an average of **99.05 reasoning
tokens through the API versus 6.05 through ChatGPT Pro sign-in**—about **16× more**.
Both sign-ins got every decision correct.

We used the same Codex client, requested model and thinking level, with
**byte-identical model input** for each matched pair. Yet the reported reasoning
usage differed sharply between API-key and subscription access.

Why do the counts diverge when the model requests match? We're sharing the
code, answers and measurements so others can reproduce the comparison and help
explain the discrepancy.

Both sign-ins use **Codex**; this compares API access with subscription access
inside the same client.

## What we found

We collected **480 responses** to two tasks: choosing projects within a budget,
and diagnosing duplicate emails from a bookstore. We tested Luna 6 and Sol 6.1
at Low, Medium and High, with 20 responses for each task, model, level and sign-in.

The clearest differences were on the bookstore task:

| Model | Thinking level | API key | ChatGPT Pro sign-in |
|---|---|---:|---:|
| Luna 6 | Low | 75.50 | 0.00 |
| Luna 6 | Medium | 99.05 | 6.05 |
| Luna 6 | High | 139.05 | 83.20 |
| Sol 6.1 | High | 226.75 | 135.25 |

These are **average reported reasoning tokens per response**, with 20 responses
per sign-in in each row. All four differences remained statistically significant
after accounting for multiple comparisons and the second round of testing.

More tokens did not automatically mean a better answer. All 240 bookstore
decision sets were correct. On the project task, Luna Low scored 16/20 through
the API and 6/20 through subscription sign-in, but that accuracy difference did
not pass the corrected statistical threshold.

We still don't know why the counts differ. This study used two fixed prompts,
one API credential and one Pro account. Independent runs are needed to find
out how widely the discrepancy occurs and what causes it.

[Read the full results and statistics](reports/2026-10-05/report.md) ·
[Browse all answers, token counts and timings](reports/2026-10-05/runs.csv)

## How we made the comparison

Each response starts a fresh Codex session. A local proxy makes sure each pair
sends exactly the same model input, byte for byte, through the same client.
Authentication and the service endpoint differ between the two sign-ins.

We record the server's answers and usage counts, then check them against
Codex's own records. Incorrect answers stay in the dataset. The proxy leaves
real server responses unchanged.

The counts describe reported usage; they don't reveal the model's internal
reasoning budget. The [full protocol](docs/PROTOCOL.md) explains the controls,
proxy behavior and limits of the comparison.

## Check our numbers

You can recompute the published results locally with Python 3.12 or later.
This uses the included data and makes no model calls:

```sh
python3 scripts/public_audit.py
python3 scripts/analyze.py
```

The generated report will be in `reports/generated/report.md`.
The [data guide](data/2026-10-05/README.md) explains what is included and which
private fields were removed.

## Run it yourself or help investigate

Independent reproductions would tell us much more, including runs that find
no difference. Different accounts, plans and collection dates are especially
useful.

| If you want to… | Start here |
|---|---|
| Repeat the experiment with your accounts | [Setup and run guide](docs/REPRODUCE.md) |
| Explore possible explanations | [Investigation plan](docs/INVESTIGATION.md) |
| Compare this with other people's reports | [Related reports and contrasting evidence](docs/RELATED_WORK.md) |
| Share a reproduction or improve the code | [Contributing](CONTRIBUTING.md) |

Other people have reported similar behavior. [Codex issue #49757](https://github.com/openai/codex/issues/49757)
compares Astra through Enterprise sign-in and the public API. Our related-work
review also covers a Luna report, effort-setting bugs and studies with different
results. They offer useful leads, but none establishes the cause of our findings.

For a first look at the code, start with the
[request definition](scripts/identical.py) and the [collection loop](scripts/run.py).
The repository includes the measured source snapshots and uses the [MIT license](LICENSE).
