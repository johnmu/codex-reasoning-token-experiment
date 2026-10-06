# Follow-up: another 480 completed responses

The follow-up added twenty responses per sign-in to every original condition,
using seed 61206. Its schedule and statistical rules were published before
collection. It required 482 attempts because two subscription requests returned
a capacity error; both failures and manual continuations are disclosed.

The same four reasoning-token gaps passed correction again. No accuracy
comparison in the new batch alone passed correction. When all three batches
are combined, Luna Low project accuracy is 35/40 API versus 18/40 subscription,
with corrected p = 0.0083. That pooled result remains exploratory.

| To inspect… | Open |
|---|---|
| New-batch and pooled findings | [Report](results/report.md) |
| All twelve new-batch comparisons | [Detailed results](results/new-batch/report.md) |
| Every new answer, token count and timing | [Responses CSV](results/new-batch/runs.csv) |
| Exact pooled accuracy calculations | [Pooled accuracy](results/pooled-accuracy.json) |
| Data format, provenance and failures | [Data guide](data/README.md) · [Failure records](data/runtime-errors.json) |
| Plan, frozen schedule and deviations | [Plan](plan/README.md) · [Schedule](plan/schedule.json) · [Amendments](plan/amendments.md) |

To check this study and regenerate its analysis:

```sh
python3 -m experiment verify studies/followup/data
python3 -m experiment analyze
```

The report is written to `output/reports/followup/report.md`.
The [recovery archive](recovery/README.md) contains the study-specific utilities
used after the capacity failures. Return to [all studies](../README.md).
