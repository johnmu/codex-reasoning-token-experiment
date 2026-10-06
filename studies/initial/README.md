# Initial comparison: 480 responses

This study combined two 240-response batches, using seeds 61204 and 61205.
Each task/model/thinking-level/sign-in condition has twenty responses.
All completed, with no failures or retries.

Four bookstore reasoning-token differences passed the all-outcomes correction
and two-look adjustment. No accuracy difference passed that threshold. Every
bookstore decision set was correct, so the task could reveal token-use differences
but provided little evidence about answer quality.

| To inspect… | Open |
|---|---|
| Results and statistics | [Report](results/report.md) |
| Every answer, token count and timing | [Responses CSV](results/runs.csv) |
| Group statistics and exact p-values | [Summary](results/summary.json) · [Significance](results/significance.json) |
| Data format and privacy scope | [Data guide](data/README.md) |
| Request bytes, schedules and original source | [Data](data/) |

To regenerate only this study:

```sh
python3 -m experiment verify studies/initial/data
python3 -m experiment analyze-study
```

The report is written to `output/reports/initial/report.md`.
Continue to the [follow-up study](../followup/README.md), or return to
[all studies](../README.md).
