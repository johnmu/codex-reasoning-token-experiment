# Shared configuration

| File | Purpose |
|---|---|
| [settings.json](settings.json) | Default models, thinking levels, shuffle seed and timeout |
| [controlled.toml](controlled.toml) | Native client configuration copied into each isolated login home |
| [base-instructions.txt](base-instructions.txt) | Neutral instructions included in the identical model request |

Collection arguments can select repeats, seed, model or effort. The actual
settings and generated schedule are frozen beside each new collection.
Both sign-ins use the same input configuration; requested model/effort support
and exact generating bytes are checked before results are accepted.

See the [run guide](../../docs/reproduce.md) and [request definition](../src/identical.py).
