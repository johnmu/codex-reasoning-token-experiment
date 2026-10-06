# What this experiment controls

The comparison is API-key versus ChatGPT sign-in **inside the same native Codex
client**. It is not a comparison with the ordinary ChatGPT website conversation.
These controls apply to both [published studies](../studies/README.md).
The measured study used one credential per route, on one machine on October 5,
2026. The subscription plan was Pro; returned reasoning mode was standard.

## Design

| Factor | Values |
|---|---|
| Task | Choose exactly three of six projects; diagnose a bookstore concurrency incident |
| Model | `gpt-6-luna`, `gpt-6.1-sol` |
| Effort | `low`, `medium`, `high` |
| Authentication | API key, ChatGPT |
| Batches | Initial: ten per arm with seed 61204, then ten with 61205; follow-up: twenty with 61206 |

Each batch runs portfolio then bookstore as separate task blocks. Within a task,
matched pairs are shuffled and adjacent. Each initial task block has sixty
pairs, with thirty API first. Each follow-up task block has 120 pairs, with
sixty API first. Each response starts a new process and ephemeral thread
in an empty workspace. Client and native executable hashes are saved before the block.

The server-side alias revision, effective budget, account routing and weights
cannot be pinned or established from the returned model/effort labels.

## Exact intervention

Read `experiment/src/identical.py`: it defines every model-input field explicitly.
The request has one user message, neutral instructions, the selected effort,
low text verbosity, no tools, no history, no continuation and `store=false`.
The client-supplied service tier is `default`. Requested encrypted reasoning is
kept opaque during inference and omitted from the public export.

The loopback TLS proxy:

1. Leaves the native authenticated endpoint and credentials in place.
2. Retains authentication/account and WebSocket transport headers; replaces
   other native headers with the three fixed protocol headers.
3. Handles an optional `generate:false` prefix prewarm locally with synthetic
   zero-usage acknowledgements **to the client**, never upstream. These are
   marked separately and excluded from actual response usage and latency.
4. Replaces exactly one generating message with the frozen bytes. Extra
   generations and HTTP fallback are blocked and make the attempt ineligible.
5. Streams real incoming server messages unchanged. It never fabricates an
   inference answer or substitutes server usage.

Authentication headers, destinations and transport nonces necessarily differ:

| Sign-in | Native destination |
|---|---|
| API | `api.openai.com/v1/responses` |
| ChatGPT | `chatgpt.com/backend-api/codex/responses` |

This is a controlled request intervention, distinct from unmodified Codex
behavior. The experimental comparison changes endpoint and account context
together; it cannot isolate an individual serving mechanism.

## Measurements and auditing

Retain input, cached-read, cache-write, output, reasoning and total tokens;
answer, correctness, failures, and client/proxy total and first-answer latency.
Output includes reasoning; do not add reasoning again when calculating cost.
Missing telemetry remains unavailable rather than becoming zero.

The raw audit compares all six actual server counters with the final native
cumulative snapshot and the recorded row. Replacing snapshots avoids double
counting repeated notifications. It verifies request bytes/headers, model and
effort echoes, server/native answers, frozen source, schedule and unique IDs.

Incorrect completed answers are retained. The project answer is exhaustively
checked against all twenty triples; only five are feasible. The bookstore rubric
scores four predefined decisions and does not score explanatory prose. Neither
reference answer is sent to a model. All 480 measured responses were eligible;
there were no retries, failures, cached reads or cache writes in these initial
batches. The follow-up added 480 completed responses, with two capacity failures
and disclosed manual continuations. Its [amendments](../studies/followup/plan/amendments.md)
explain the interruptions and completed-response scope.

Client latency starts at turn submission and excludes proxy/process startup.
Wire latency starts at the forwarded generating request. Both include proxy
overhead; these are not direct measurements of internal compute time.

## Statistical scope

In the initial study, ten pairs were inspected before authorizing ten more. First-batch and pooled
tests are exploratory; extension rules were fixed before collecting batch two.
Two-sided exact randomization tests preserve the 30/60 order balance separately
inside each task/batch. The two independent batch distributions are combined
without a normal approximation. This interpretation assumes no carryover.

Holm correction is shown within each of the twelve metric comparisons and
across all 36 reasoning/accuracy/latency comparisons. Pooled corrected p-values
are multiplied by two for the two significance looks. This is a conservative
sensitivity adjustment, not a preregistered sequential study. Nonsignificance
does not establish equivalence. Repeated responses sample variability on these
two prompts, not a population of coding tasks or accounts.

The [follow-up plan](../studies/followup/plan/README.md) specified one final look
with Holm correction over 36 new-batch comparisons. Its secondary pooled accuracy
analysis combines three order-balanced batch blocks and uses a conservative
factor of 36 outcomes times three significance looks. That pooled analysis
remains exploratory; the runtime deviations also limit confirmation claims.

References: [OpenAI app-server](https://learn.chatgpt.com/docs/app-server),
[Responses WebSockets](https://developers.openai.com/api/docs/guides/websocket-mode),
[reasoning controls](https://developers.openai.com/api/docs/guides/reasoning),
[paired permutations](https://arxiv.org/abs/2205.01416),
[Holm and paired accuracy comparisons](https://pmc.ncbi.nlm.nih.gov/articles/PMC2902578/).
