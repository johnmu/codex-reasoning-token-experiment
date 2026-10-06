# Results of the fixed 480-response follow-up

[Plan published before collection](../../docs/CONFIRMATION_PLAN.md). The original 480 responses are unchanged; this batch adds 480 new responses.

## New batch: completed-response comparison

This batch required 482 attempts. 2 subscription requests failed with a server-capacity error and were manually repeated after inspection. [The runtime amendment](../../docs/CONFIRMATION_AMENDMENT.md) and [failure evidence](../../data/confirmation-2026-10-05/runtime-errors.json) disclose the interruptions. These statistics describe completed responses and do not measure availability per attempt. The deviations limit interpretation as confirmation of the original study.

The exact paired tests use only the new answers. Holm correction covers all 36 task/model/level/outcome comparisons, with one final look.

| Outcome | Differences significant at 5% |
|---|---:|
| reasoning_tokens | 4 |
| correct | 0 |
| seconds | 1 |

[New-batch answers, token counts, latency and statistics](new-batch/report.md)

## Pooled accuracy: exploratory

Each row includes 40 responses per sign-in from all three batches. The exact test retains each batch’s order constraints. The planned conservative correction is 36 outcomes × 3 significance looks. This pooled analysis is not independent confirmation.

| Task | Model | Level | API correct | ChatGPT correct | Raw p | Corrected p |
|---|---|---|---:|---:|---:|---:|
| bookstore | gpt-6-luna | high | 40/40 | 40/40 | 1 | 1 |
| bookstore | gpt-6-luna | low | 40/40 | 40/40 | 1 | 1 |
| bookstore | gpt-6-luna | medium | 40/40 | 40/40 | 1 | 1 |
| bookstore | gpt-6.1-sol | high | 40/40 | 40/40 | 1 | 1 |
| bookstore | gpt-6.1-sol | low | 40/40 | 40/40 | 1 | 1 |
| bookstore | gpt-6.1-sol | medium | 40/40 | 40/40 | 1 | 1 |
| portfolio | gpt-6-luna | high | 30/40 | 35/40 | 0.29879 | 1 |
| portfolio | gpt-6-luna | low | 35/40 | 18/40 | 7.65571e-05 | 0.00826817 |
| portfolio | gpt-6-luna | medium | 36/40 | 33/40 | 0.548826 | 1 |
| portfolio | gpt-6.1-sol | high | 40/40 | 40/40 | 1 | 1 |
| portfolio | gpt-6.1-sol | low | 39/40 | 40/40 | 1 | 1 |
| portfolio | gpt-6.1-sol | medium | 40/40 | 40/40 | 1 | 1 |

[Exact pooled accuracy results](pooled-accuracy.json). These two fixed tasks do not establish a general capability difference or the cause of any discrepancy.
