# Reasoning-token experiment

The experiment compares the exact same pinned native Codex executable with API-key and
ChatGPT authentication. Keep model identities and client settings fixed.

- Do not make model calls while designing or running offline checks.
- Live runs must be explicitly requested and use the generated schedule.
- Never copy or print credentials. Authentication belongs in isolated homes;
  preserve the user's normal Codex login and configuration.
- Preserve raw evidence and all failed attempts. Never silently retry a run.
- Missing reasoning-token telemetry is missing, never zero.
- Freeze prompts, reference answers, configuration, and schedule before collection.
- Grade reference answers locally. Do not expose solutions to tested models.
- Keep Ultra and other multi-agent experiments separate from the primary study.
- Report unavailable model/effort combinations; do not substitute models.
- Keep credentials, CA private keys, full local captures and account/session identity out of Git. Public data is an allowlisted projection with the original request bytes and measured fields.
- Preserve historical source snapshots and data. Documentation or harness cleanup must not rewrite a measured collection.
- Offline verification must not authenticate, start model turns or make provider requests.
