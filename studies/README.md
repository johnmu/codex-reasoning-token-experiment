# Results and evidence

We collected 960 completed responses across the same two tasks, two models and
three thinking levels. Each study has its own results, data and source snapshots.
Both were collected on October 5, 2026.

| Study | What it contains | Start here |
|---|---|---|
| Initial comparison | Two batches of 240 responses; 20 responses per sign-in in each condition | [Study overview](initial/README.md) · [Results](initial/results/report.md) |
| Follow-up | Another 480 completed responses; standalone comparisons and pooled accuracy at 40 per sign-in | [Study overview](followup/README.md) · [Results](followup/results/report.md) |

The same four bookstore reasoning-token gaps passed correction in both studies.
The pooled Luna Low project accuracy gap passed the planned conservative
correction (35/40 API versus 18/40 subscription, p = 0.0083). The follow-up alone
did not pass its accuracy correction. The pooled result remains exploratory.

The follow-up required 482 attempts, including two preserved subscription
capacity failures and documented manual continuations. Its statistics describe
completed responses. See the [amendments](followup/plan/amendments.md).

## Check the evidence

From the repository root, with Python 3.12 or later:

```sh
python3 -m experiment verify
python3 -m experiment analyze
```

The first command checks both datasets and their archived source hashes. The
second regenerates the follow-up and pooled accuracy report in
`output/reports/followup/`. Neither command needs credentials or makes model calls.
For only the initial study, use `python3 -m experiment analyze-study`.

The [protocol](../docs/protocol.md) explains the comparison. To collect a new
study, follow the [run guide](../docs/reproduce.md) and [contribution guide](../CONTRIBUTING.md).
