# Published experiment results

480 responses. Exact paired tests; Holm correction over 36 comparisons with a 1-look factor. Significant at 5%: 4 reasoning-token differences, 0 accuracy differences, 1 client-latency differences.

Means below are reported reasoning tokens. Correctness is exact project selection or the four bookstore decisions; explanation prose is not graded.

| Task | Model | Level | API tokens | ChatGPT tokens | API correct | ChatGPT correct | API seconds | ChatGPT seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|
| portfolio | gpt-6-luna | low | 248.50 | 189.85 | 19/20 | 12/20 | 5.47 | 5.88 |
| portfolio | gpt-6-luna | medium | 294.75 | 231.95 | 18/20 | 14/20 | 5.53 | 8.00 |
| portfolio | gpt-6-luna | high | 311.50 | 261.65 | 13/20 | 18/20 | 5.58 | 8.25 |
| portfolio | gpt-6.1-sol | low | 103.10 | 101.60 | 20/20 | 20/20 | 5.45 | 5.52 |
| portfolio | gpt-6.1-sol | medium | 109.90 | 106.75 | 20/20 | 20/20 | 4.46 | 5.42 |
| portfolio | gpt-6.1-sol | high | 143.25 | 127.65 | 20/20 | 20/20 | 5.87 | 6.00 |
| bookstore | gpt-6-luna | low | 61.60 | 0.00 | 20/20 | 20/20 | 3.51 | 3.61 |
| bookstore | gpt-6-luna | medium | 93.55 | 0.00 | 20/20 | 20/20 | 3.14 | 4.07 |
| bookstore | gpt-6-luna | high | 158.00 | 87.20 | 20/20 | 20/20 | 4.03 | 5.32 |
| bookstore | gpt-6.1-sol | low | 0.00 | 0.00 | 20/20 | 20/20 | 4.99 | 5.06 |
| bookstore | gpt-6.1-sol | medium | 4.15 | 0.00 | 20/20 | 20/20 | 4.18 | 5.06 |
| bookstore | gpt-6.1-sol | high | 206.60 | 142.15 | 20/20 | 20/20 | 9.28 | 8.93 |

API charge estimate: **$0.3186**, calculated from measured input and output tokens. Output already includes reasoning; cache reads and writes are zero. [Recorded Standard pricing](https://developers.openai.com/api/docs/pricing): Luna $0.10/$0.50 and Sol 6.1 $2/$10 per million input/output tokens. This is not a verified invoice.

## Statistical comparisons

Raw p-values and corrections are exploratory for the original and pooled study. The extension rules were frozen before its collection. This analysis uses a significance-look factor of 1. Randomization weights retain the first/second order balance separately within each task/batch. The interpretation assumes no carryover between adjacent calls. Nonsignificance does not establish equivalence. These two prompts do not establish a general capability difference or a hidden server cause.

### reasoning_tokens

| Task | Model | Level | API − ChatGPT | Raw p | Metric-family correction + looks | All-outcomes correction + looks |
|---|---|---|---:|---:|---:|---:|
| portfolio | gpt-6-luna | low | 58.650 | 0.0118912 | 0.0832386 | 0.297281 |
| portfolio | gpt-6-luna | medium | 62.800 | 0.023005 | 0.13803 | 0.529116 |
| portfolio | gpt-6-luna | high | 49.850 | 0.142708 | 0.71354 | 1 |
| portfolio | gpt-6.1-sol | low | 1.500 | 0.577033 | 1 | 1 |
| portfolio | gpt-6.1-sol | medium | 3.150 | 0.265323 | 1 | 1 |
| portfolio | gpt-6.1-sol | high | 15.600 | 0.00171425 | 0.013714 | 0.0531418 |
| bookstore | gpt-6-luna | low | 61.600 | 8.2722e-06 | 9.09942e-05 | 0.000289527 |
| bookstore | gpt-6-luna | medium | 93.550 | 2.08853e-06 | 2.50623e-05 | 7.51869e-05 |
| bookstore | gpt-6-luna | high | 70.800 | 1.00426e-05 | 0.000100426 | 0.000341447 |
| bookstore | gpt-6.1-sol | low | 0.000 | 1 | 1 | 1 |
| bookstore | gpt-6.1-sol | medium | 4.150 | 1 | 1 | 1 |
| bookstore | gpt-6.1-sol | high | 64.450 | 0.000214235 | 0.00192812 | 0.00706977 |

### correct

| Task | Model | Level | API − ChatGPT | Raw p | Metric-family correction + looks | All-outcomes correction + looks |
|---|---|---|---:|---:|---:|---:|
| portfolio | gpt-6-luna | low | 0.350 | 0.0154764 | 0.185717 | 0.371434 |
| portfolio | gpt-6-luna | medium | 0.200 | 0.290244 | 1 | 1 |
| portfolio | gpt-6-luna | high | -0.250 | 0.181515 | 1 | 1 |
| portfolio | gpt-6.1-sol | low | 0.000 | 1 | 1 | 1 |
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
| portfolio | gpt-6-luna | low | -0.409 | 0.568355 | 1 | 1 |
| portfolio | gpt-6-luna | medium | -2.464 | 0.00850872 | 0.059561 | 0.221227 |
| portfolio | gpt-6-luna | high | -2.673 | 0.0067443 | 0.0539544 | 0.182096 |
| portfolio | gpt-6.1-sol | low | -0.071 | 0.704327 | 1 | 1 |
| portfolio | gpt-6.1-sol | medium | -0.969 | 0.00124556 | 0.0149467 | 0.0398579 |
| portfolio | gpt-6.1-sol | high | -0.134 | 0.66585 | 1 | 1 |
| bookstore | gpt-6-luna | low | -0.098 | 0.590021 | 1 | 1 |
| bookstore | gpt-6-luna | medium | -0.926 | 0.00254161 | 0.0278209 | 0.0758751 |
| bookstore | gpt-6-luna | high | -1.290 | 0.00377813 | 0.0340032 | 0.105788 |
| bookstore | gpt-6.1-sol | low | -0.070 | 0.668978 | 1 | 1 |
| bookstore | gpt-6.1-sol | medium | -0.880 | 0.00252917 | 0.0278209 | 0.0758751 |
| bookstore | gpt-6.1-sol | high | 0.358 | 0.397554 | 1 | 1 |

[All responses](runs.csv) · [Group statistics](summary.json) · [Exact p-values](significance.json)
