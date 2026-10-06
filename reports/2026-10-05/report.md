# Published experiment results

480 responses. Exact paired tests; Holm correction over 36 comparisons with a 2-look factor. Significant at 5%: 4 reasoning-token differences, 0 accuracy differences, 8 client-latency differences.

Means below are reported reasoning tokens. Correctness is exact project selection or the four bookstore decisions; explanation prose is not graded.

| Task | Model | Level | API tokens | ChatGPT tokens | API correct | ChatGPT correct | API seconds | ChatGPT seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|
| portfolio | gpt-6-luna | low | 205.45 | 138.55 | 16/20 | 6/20 | 4.16 | 5.50 |
| portfolio | gpt-6-luna | medium | 290.50 | 226.80 | 18/20 | 19/20 | 5.41 | 6.34 |
| portfolio | gpt-6-luna | high | 311.40 | 267.00 | 17/20 | 17/20 | 5.25 | 8.01 |
| portfolio | gpt-6.1-sol | low | 105.80 | 100.75 | 19/20 | 20/20 | 4.84 | 6.97 |
| portfolio | gpt-6.1-sol | medium | 112.25 | 111.35 | 20/20 | 20/20 | 5.09 | 6.73 |
| portfolio | gpt-6.1-sol | high | 135.95 | 130.95 | 20/20 | 20/20 | 5.43 | 7.78 |
| bookstore | gpt-6-luna | low | 75.50 | 0.00 | 20/20 | 20/20 | 2.98 | 3.99 |
| bookstore | gpt-6-luna | medium | 99.05 | 6.05 | 20/20 | 20/20 | 5.54 | 4.02 |
| bookstore | gpt-6-luna | high | 139.05 | 83.20 | 20/20 | 20/20 | 3.85 | 5.49 |
| bookstore | gpt-6.1-sol | low | 0.00 | 0.00 | 20/20 | 20/20 | 3.94 | 6.29 |
| bookstore | gpt-6.1-sol | medium | 3.05 | 0.00 | 20/20 | 20/20 | 4.32 | 6.21 |
| bookstore | gpt-6.1-sol | high | 226.75 | 135.25 | 20/20 | 20/20 | 9.42 | 10.42 |

API charge estimate: **$0.3225**, calculated from measured input and output tokens. Output already includes reasoning; cache reads and writes are zero. [Recorded Standard pricing](https://developers.openai.com/api/docs/pricing): Luna $0.10/$0.50 and Sol 6.1 $2/$10 per million input/output tokens. This is not a verified invoice.

## Statistical comparisons

Raw p-values and corrections are exploratory for the original and pooled study. The extension rules were frozen before its collection. The factor of two conservatively accounts for examining significance at ten and twenty pairs. Randomization weights retain the first/second order balance separately within each task/batch. The interpretation assumes no carryover between adjacent calls. Nonsignificance does not establish equivalence. These two prompts do not establish a general capability difference or a hidden server cause.

### reasoning_tokens

| Task | Model | Level | API − ChatGPT | Raw p | Metric-family correction + looks | All-outcomes correction + looks |
|---|---|---|---:|---:|---:|---:|
| portfolio | gpt-6-luna | low | 66.900 | 0.0112086 | 0.179338 | 0.515597 |
| portfolio | gpt-6-luna | medium | 63.700 | 0.0301713 | 0.422399 | 1 |
| portfolio | gpt-6-luna | high | 44.400 | 0.113226 | 1 | 1 |
| portfolio | gpt-6.1-sol | low | 5.050 | 0.170342 | 1 | 1 |
| portfolio | gpt-6.1-sol | medium | 0.900 | 0.768022 | 1 | 1 |
| portfolio | gpt-6.1-sol | high | 5.000 | 0.366319 | 1 | 1 |
| bookstore | gpt-6-luna | low | 75.500 | 1.953e-06 | 4.2966e-05 | 0.00013671 |
| bookstore | gpt-6-luna | medium | 93.000 | 1.60425e-06 | 3.8502e-05 | 0.000115506 |
| bookstore | gpt-6-luna | high | 55.850 | 3.19427e-05 | 0.000574969 | 0.00166102 |
| bookstore | gpt-6.1-sol | low | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6.1-sol | medium | 3.050 | 1 | 1 | 1 |
| bookstore | gpt-6.1-sol | high | 91.500 | 4.30974e-06 | 8.61948e-05 | 0.000249965 |

### correct

| Task | Model | Level | API − ChatGPT | Raw p | Metric-family correction + looks | All-outcomes correction + looks |
|---|---|---|---:|---:|---:|---:|
| portfolio | gpt-6-luna | low | 0.500 | 0.00641184 | 0.153884 | 0.307769 |
| portfolio | gpt-6-luna | medium | -0.050 | 1 | 1 | 1 |
| portfolio | gpt-6-luna | high | 0.000 | 1 | 1 | 1 |
| portfolio | gpt-6.1-sol | low | -0.050 | 1 | 1 | 1 |
| portfolio | gpt-6.1-sol | medium | 0.000 | 1 | 1 | 1 |
| portfolio | gpt-6.1-sol | high | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6-luna | low | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6-luna | medium | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6-luna | high | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6.1-sol | low | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6.1-sol | medium | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6.1-sol | high | 0.000 | 1 | 1 | 1 |

### seconds

| Task | Model | Level | API − ChatGPT | Raw p | Metric-family correction + looks | All-outcomes correction + looks |
|---|---|---|---:|---:|---:|---:|
| portfolio | gpt-6-luna | low | -1.346 | 0.0610724 | 0.244289 | 1 |
| portfolio | gpt-6-luna | medium | -0.929 | 0.0305258 | 0.183155 | 1 |
| portfolio | gpt-6-luna | high | -2.756 | 7.66392e-05 | 0.000766392 | 0.00383196 |
| portfolio | gpt-6.1-sol | low | -2.127 | 1.02532e-05 | 0.000143545 | 0.000574181 |
| portfolio | gpt-6.1-sol | medium | -1.640 | 2.11262e-06 | 4.68719e-05 | 0.00013671 |
| portfolio | gpt-6.1-sol | high | -2.347 | 3.9905e-06 | 6.3848e-05 | 0.00023943 |
| bookstore | gpt-6-luna | low | -1.006 | 1.953e-06 | 4.68719e-05 | 0.00013671 |
| bookstore | gpt-6-luna | medium | 1.524 | 0.99957 | 1 | 1 |
| bookstore | gpt-6-luna | high | -1.636 | 2.19712e-06 | 4.68719e-05 | 0.00013671 |
| bookstore | gpt-6.1-sol | low | -2.348 | 1.953e-06 | 4.68719e-05 | 0.00013671 |
| bookstore | gpt-6.1-sol | medium | -1.889 | 2.07506e-05 | 0.000249007 | 0.00112053 |
| bookstore | gpt-6.1-sol | high | -1.009 | 0.0213742 | 0.170993 | 0.940464 |

[All responses](runs.csv) · [Group statistics](summary.json) · [Exact p-values](significance.json)
