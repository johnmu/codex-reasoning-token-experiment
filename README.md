# Same model. Same prompt. 32× more reasoning tokens through the API?

On our bookstore task, Luna 6 at Medium reported an average of **96.30 reasoning
tokens through the API versus 3.025 through ChatGPT Pro sign-in**—about **32× more**
across 40 completed responses per sign-in. Both sign-ins got every decision correct.

We used the same Codex client, requested model and thinking level, with
**byte-identical model input** for each matched pair. Yet the reported reasoning
usage differed sharply between API-key and subscription access.

Why do the counts diverge when the model requests match? We're sharing the
code, answers and measurements so others can reproduce the comparison and help
explain the discrepancy.

Both sign-ins use **Codex**; this compares API access with subscription access
inside the same client.

[Read the studies](studies/README.md) · [Repeat the experiment](docs/reproduce.md) ·
[Explore the code](experiment/README.md)

## What we found

We collected **960 completed responses** to two tasks: choosing projects within a budget,
and diagnosing duplicate emails from a bookstore. We tested Luna 6 and Sol 6.1
at Low, Medium and High, with 40 responses for each task, model, level and sign-in.
The original 480 responses were followed by a fixed, separately analyzed batch
of another 480.

The clearest differences were on the bookstore task:

| Model | Thinking level | API key | ChatGPT Pro sign-in |
|---|---|---:|---:|
| Luna 6 | Low | 68.550 | 0.000 |
| Luna 6 | Medium | 96.300 | 3.025 |
| Luna 6 | High | 148.525 | 85.200 |
| Sol 6.1 | High | 216.675 | 138.700 |

These are **average reported reasoning tokens per response**, with 40 completed
responses per sign-in in each row. These same four differences passed the
multiple-comparison correction in both the original study and the follow-up.

More tokens did not automatically mean a better answer. All 480 bookstore
decision sets were correct. On the project task, Luna Low scored **35/40 through
the API and 18/40 through subscription sign-in** across the full dataset.
That pooled accuracy difference passed the planned conservative correction
(p = 0.0083), but it remains exploratory. The new batch alone scored 19/20
versus 12/20 and did not pass its correction (p = 0.371).

The follow-up also encountered two subscription-route capacity failures. We
preserved both, documented manual continuations, and completed the original
schedule. The statistics above describe completed responses; the
[runtime amendment](studies/followup/plan/amendments.md) explains the interruptions.

We still don't know why the counts differ. This study used two fixed prompts,
one API credential and one Pro account. Independent runs are needed to find
out how widely the discrepancy occurs and what causes it.

[Read the follow-up and pooled accuracy results](studies/followup/results/report.md) ·
[Original results](studies/initial/results/report.md)

## How we made the comparison

Each response starts a fresh Codex session. A local proxy makes sure each pair
sends exactly the same model input, byte for byte, through the same client.
Authentication and the service endpoint differ between the two sign-ins.

We record the server's answers and usage counts, then check them against
Codex's own records. Incorrect answers stay in the dataset. The proxy leaves
real server responses unchanged.

The counts describe reported usage; they don't reveal the model's internal
reasoning budget. The [full protocol](docs/protocol.md) explains the controls,
proxy behavior and limits of the comparison.

## Check our numbers

You can recompute the published results locally with Python 3.12 or later.
This uses the included data and makes no model calls:

```sh
python3 -m experiment verify
python3 -m experiment analyze
```

The generated report will be in `output/reports/followup/report.md`.
The [study index](studies/README.md) links the published reports, answer tables,
data guides, and recorded plans.

## Run it yourself or help investigate

Independent reproductions would tell us much more, including runs that find
no difference. Different accounts, plans and collection dates are especially
useful.

| If you want to… | Start here |
|---|---|
| Browse the results and evidence | [Studies](studies/README.md) |
| Repeat the experiment with your accounts | [Setup and run guide](docs/reproduce.md) |
| Explore possible explanations | [Investigation plan](docs/investigation.md) |
| Compare this with other people's reports | [Related reports and contrasting evidence](docs/related-work.md) |
| Understand or change the runner | [Experiment code guide](experiment/README.md) |
| Share a reproduction or improve the code | [Contributing](CONTRIBUTING.md) |

Other people have reported similar behavior. [Codex issue #49757](https://github.com/openai/codex/issues/49757)
compares Astra through Enterprise sign-in and the public API. Our related-work
review also covers a Luna report, effort-setting bugs and studies with different
results. They offer useful leads, but none establishes the cause of our findings.

The repository uses the [MIT license](LICENSE).
