# Help determine why the counts differ

The measured finding is a difference in **reported** reasoning-token usage for
some prompt/model/effort conditions. It does not establish hidden weights,
intentional degradation, quantization, a fixed token budget or a general quality gap.

## What the current evidence addresses

| Possibility | Current evidence | Useful follow-up |
|---|---|---|
| Client supplied different context or tools | Actual generating bytes and fixed protocol headers match in all 480 completed pairs; tools/history are absent | Reproduce the strict control first; run an unmodified-client baseline separately |
| UI omitted a thinking summary | We read server usage, then independently compare native usage | Compare usage with event/item presence; never infer tokens from visible prose |
| Client added cumulative snapshots repeatedly | Final native snapshots match all six server counts | Retain every update; distinguish cumulative totals from increments |
| Wrong outgoing model or effort | Sent fields and server echoes match; reroutes/tool calls cause a stop | Keep strict checks; include incompatibility/fallback errors rather than substituting |
| Mid-thread effort update was ignored | One fresh single-turn session per response; no configuration updates or continuation | Test updates in a separately labeled multi-turn study |
| Cache, compaction or warmup explains it | All read/write cache counters were zero, no history/compaction, warmup consumed locally | Compare unchanged native prewarming separately, without pooling results |
| Server counter semantics differ by route | Client/server agreement cannot validate the service's underlying accounting definition | Ask OpenAI whether reasoning counters are equivalent and for safe corroborating metadata |
| Serving defaults, revisions, adaptive effort or account policy differ | These remain unknown despite equal declared inputs/labels | Replicate across accounts, plans, dates and regions; record safe metadata and controls |

## Suggested reproductions

1. Run the eight-response smoke, inspect raw verification, then precommit the
   full sample size. Export and analyze every completed answer.
2. Repeat the existing prompts with independent credentials and the same
   executable on each route. Record OS, Python, binary hash, dependency version,
   subscription plan, date and any managed policy you can safely disclose.
3. Repeat on another date. Retain each dataset separately before combining;
   do not keep adding responses until a p-value crosses a threshold.
4. Add new tasks with graded reference answers, under a new dataset/version.
   The bookstore task has a correctness ceiling here, limiting quality inference.
5. Test a separate native-request arm with `--native-requests --capture`.
   Its inputs may differ by route, so it answers a different question.

One change at a time is easiest to interpret. Keep output caps, verbosity,
reasoning mode, tools, instructions and transport explicit. Record omitted
defaults. A subscription named Pro is not the API's `reasoning.mode="pro"`.

## Questions for OpenAI

- Are identical model/effort labels intended to have equivalent semantics on
  the API and ChatGPT-authenticated Codex endpoint?
- Are the two routes' reported reasoning counters defined identically?
- Can account policy, server-added instructions or revision selection change
  the effective behavior while the returned labels stay the same?
- Which nonsensitive fields can identify an effective serving profile?

These questions overlap with [issue #49757](https://github.com/openai/codex/issues/49757).
As of the related-work review, that report has no maintainer explanation.

Use [CONTRIBUTING.md](../CONTRIBUTING.md) to submit a privacy-checked reproduction
or a negative result. Mechanism claims need evidence beyond differing means.
