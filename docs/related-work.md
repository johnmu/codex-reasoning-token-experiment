# Related reports and contrasting evidence

Reviewed October 5, 2026. **Other people have reported similar token behavior,
but the cause has not been established.** Two particularly close comparisons
are below. Other reports concern different mechanisms and are not pooled with
our data. Issue status is a snapshot, not a guarantee that an issue remains open.

## Closest comparisons

### Codex issue #49757: Astra, Enterprise sign-in versus the public API

[#49757](https://github.com/openai/codex/issues/49757), opened September 30,
reports sixty synthetic TTL-cache reviews: ten requests per route at each of
Low/Medium/High. It used direct Python HTTP/SSE replay, not a native Codex turn.
The Enterprise and API bodies matched byte for byte; model/effort echoes matched
and cached input was zero. Reported median reasoning counts were:

| Level | Enterprise Codex | Public API |
|---|---:|---:|
| Low | 51.5 | 48.5 |
| Medium | 60 | 135 |
| High | 141.5 | 696 |

This is the strongest related auth/endpoint measurement found. Important
differences: Astra rather than Luna/Sol, Enterprise rather than Pro, direct
replay rather than native-client interception, and API samples collected after
the Enterprise samples. Its body explicitly leaves internal serving semantics
and output quality unresolved. It was open with no comments when checked.

### Luna report: subscription zeros, higher gateway API counts

[This Luna comparison](https://www.reddit.com/r/codex/comments/1wptlvk/gpt6_luna_in_codex_does_zero_reasoning_high/)
reports six game-planning prompts, roughly 13–16K input tokens, with repeated
Low/Medium and one High run per prompt. Its median API/subscription reasoning
counts were 455/0, 3015/0 and 6954/2985, respectively.

The author describes disabled tools, matching system/user text and counters from
Codex/API usage. Crucially, the API arm used **OpenCode Zen**, not OpenAI's public
endpoint, and did not demonstrate equality of full outgoing payloads. This is
a close symptom match, with gateway/client confounds that our experiment avoids.
The same discussion links benchmarks where Medium is not always zero.

## Related mechanisms that must be distinguished

| Primary source | Evidence or report | Relationship to this experiment |
|---|---|---|
| [#32724](https://github.com/openai/codex/issues/32724) | Subscription effort-profile stability/transparency request, including a link to a claimed server tuning announcement | Relevant question; not a controlled auth comparison or proof of our cause |
| [#47843](https://github.com/openai/codex/issues/47843) | Pro-account Luna/Sol tests comparing request-level High with a mid-thread configuration update; Luna update cases remained at zero | Measured effort-update issue; our fresh single-turn requests have no update/continuation |
| [#28113](https://github.com/openai/codex/issues/28113) | Enterprise CLI startup reportedly ignores configured effort | Supports checking the actual sent effort; our wire audit does that |
| [#10746](https://github.com/openai/codex/issues/10746) | API-key JSON output reportedly omits reasoning items while ChatGPT login exposes them | Visibility rather than token allocation; [an OpenAI account acknowledged a bug](https://github.com/openai/codex/issues/10746#issuecomment-3854936840), not the cause of this study |
| [#38160](https://github.com/openai/codex/issues/38160) | Empty thinking UI despite nonzero server reasoning usage and opaque reasoning items | Reinforces measuring counters rather than visible summaries |
| [#29353](https://github.com/openai/codex/issues/29353), [#30364](https://github.com/openai/codex/issues/30364) | Older GPT-5.5 reports of fixed counts near 516/1034/1552, sometimes with incorrect answers; the aggregate issue was closed when checked | Historical threshold behavior, different models/tasks; no proof that the same mechanism explains current route differences |
| [Independent reproduction project](https://github.com/NickalasLight/codex-reasoning-bug-516-token) | Benchmark retests and contributor evidence improved after instruction changes, while aggregate mean counts stayed similar and clustering persisted | Useful experimental design precedent; the proposed workaround was not a universal fix |
| [#46632](https://github.com/openai/codex/issues/46632), [#47015](https://github.com/openai/codex/issues/47015) | Requested Astra reportedly returned Luna metadata, including official-client traces and separate adapter-mediated evidence | Model-label mismatch is distinct; our accepted responses require matching outgoing and returned model IDs |
| [Developer Community UI/model report](https://community.openai.com/t/codex-windows-app-displays-gpt-6-astra-but-actually-requests-gpt-6-luna-ui-effective-model-mismatch/1403393) | UI names Astra while captured outgoing requests and responses name Luna | Client label mismatch, distinguishable by our sent-payload checks |
| [#39767](https://github.com/openai/codex/issues/39767), [#49026](https://github.com/openai/codex/issues/49026) | Historical reasoning estimates reportedly double-counted for automatic compaction | Long-thread context accounting; our stateless single-turn study has no compaction and compares real server/native counters |

These are reports, not blanket confirmation of each proposed explanation.
Several model-substitution reports share cross-links and related traces; count
them as a report family rather than automatically treating every link as an
independent replication. The visibility acknowledgement does not confirm a
reasoning-budget defect.

## Contrasting or limiting evidence

The pinned [bug-hunt benchmark's first CSV](https://raw.githubusercontent.com/phuryn/bug-hunt-bench/d774ef1/results/repo1-metrics.csv)
and [second CSV](https://raw.githubusercontent.com/phuryn/bug-hunt-bench/d774ef1/results/repo2-metrics.csv)
mark Luna 6 runs as ChatGPT-account authenticated. Low reports zero on both
repositories, but Medium reports **1549 and 1551 total reasoning tokens**.
These are whole benchmark totals, not per-response measurements, and there is
no matched API arm. They contradict a universal claim that subscription Luna
Medium always reports zero, while remaining compatible with task dependence.

[Takashi Hatada's first-hand route comparison](https://tech.hatada.jp/en/posts/same-task-subscription-vs-api)
used the same Codex tool, prompt and reasoning depth to review a public PWA with
Luna 5.6 and Astra 6. The author reported similar findings within a model across
routes, with differences between models. Most conditions had one run; one API
Astra condition was repeated. Separate reasoning counts and full payload
equality were not demonstrated, and tool-driven input totals differed. It is
useful contrasting quality evidence, not a refutation of our token measurements.

## Search scope and limitations

The search covered the public Codex tracker, issue comments, broader GitHub
reports, Reddit, OpenAI Developer Community, a firsthand comparison blog and
published benchmark receipts. Nine logged tracker queries produced **334 distinct
matching links**, including many unrelated usage, UI, capacity and accounting
issues. Broad queries were capped at fifty; focused phrase/model/endpoint
queries and direct cross-links narrowed the relevant reports. See
[the query log and issue status snapshots](search-log.json).

This is a systematic broad search, not an exhaustive inventory of every forum
or comment. The closest reports above were read directly, not inferred only
from search snippets. We found no public maintainer explanation resolving
#49757 and no evidence that establishes the internal cause of our Luna/Sol
measurements. General complaints about weaker answers, missing summaries,
quota depletion or quantization are insufficient on their own.

The next useful contribution is an independently audited same-client,
same-payload reproduction, including a negative result, across another account
or date. Follow [the investigation plan](investigation.md).
