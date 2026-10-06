# One server-capacity failure during the follow-up

The follow-up stopped at scheduled response 101: portfolio, Luna 6, Medium,
ChatGPT sign-in, repeat 8. The first 100 responses completed. The failed request
passed the byte-equality check, but the server returned `server_is_overloaded`.
Codex reported `serverOverloaded` and did not retry. No answer or reasoning-token
count was available; missing telemetry is not a zero-token response.

The original failed collection is preserved unchanged. Before continuing, we
recorded the failure and its evidence hashes in the
[failure record](../plans/confirmation-capacity-error.json). We are making one
documented manual retry of that scheduled response, then following the remaining
original schedule. The first 100 successful responses will not be rerun.
No interim correctness totals or p-values were inspected to make this decision.

This is a runtime deviation from the [original fixed plan](CONFIRMATION_PLAN.md).
If collection completes, the dataset will contain 480 completed responses from
481 attempts, including one separately reported subscription-route failure.
The planned statistical tests will describe **completed, audited responses**.
They will not measure overall success per attempt or establish equal availability
between access methods. The manual retry and collection interruption must be
considered when interpreting this follow-up; it is not a flawless execution of
the original schedule.

The prompts, requested models, efforts, client binary, pair order, sample size
of completed responses and statistical corrections remain as recorded. There
is no automatic retry loop. A further error will stop collection for inspection.
