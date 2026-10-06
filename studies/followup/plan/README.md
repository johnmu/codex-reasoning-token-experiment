# A fixed follow-up to the first 480 responses

This plan was published before collecting any follow-up answers. It was prompted
by the accuracy gap on the project task, which did not pass the original study's
corrected threshold. The follow-up covers every original condition, rather than
collecting only the most promising one.

The [frozen plan and schedules](schedule.json) record
the original commit, data hash, executable hash and twelve request hashes.

## What we will collect

- Both original tasks: project selection and bookstore diagnosis.
- Both original models: Luna 6 and Sol 6.1.
- Low, Medium and High thinking levels.
- Twenty additional responses per task/model/level/sign-in.
- 480 new responses: 240 API and 240 ChatGPT Pro.
- The original native Codex executable and byte-identical model payloads.
- Fresh processes and sessions, paired requests and seed 61206.

Within each task, 60 pairs use the API first and 60 use ChatGPT first. We retain
all answers and attempts. A runtime or audit error stops the collection for
inspection; it does not trigger an automatic retry. We will not change the
sample size based on interim correctness or p-values.

## How we will evaluate it

The primary analysis uses **only the new batch**, so earlier results cannot
make a failed replication appear successful. We compare reported reasoning
tokens, correctness and client latency in each of the twelve conditions.
The test is the original exact, two-sided paired randomization test, preserving
the task-level balance of which sign-in went first. Holm correction covers all
36 comparisons, with one final look and a 5% threshold.

We will also report **pooled accuracy** across the original two batches and the
new batch. This is an exploratory secondary analysis. Its exact test preserves
the separate order-balance constraints of all three batches. We use a
conservative Bonferroni factor of 36 outcomes times three significance looks.
This accounts for the prior searches and repeated examination; we will not
describe a pooled finding as an independent replication.

Reasoning tokens and latency from the new batch remain available regardless of
the accuracy result. No significant finding would establish a hidden backend
cause or a general difference in model capability.

## Reproduce this collection

After following the [setup guide](../../../docs/reproduce.md):

```sh
python3 -m experiment run --benchmark both --repeats 20 --seed 61206
python3 -m experiment run --benchmark both --repeats 20 --seed 61206 --execute --output output/raw/confirmation-new
python3 -m experiment audit output/raw/confirmation-new
```

The first command previews the schedule. The second makes paid API calls and
uses subscription allowance. Expected API cost is about $0.32 based on the
original measured usage and [Standard API pricing](https://developers.openai.com/api/docs/pricing);
the actual usage can differ. Raw captures stay private and will be exported
through the existing allowlisted public-data workflow.
