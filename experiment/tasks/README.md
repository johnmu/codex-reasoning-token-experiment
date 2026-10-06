# The two tasks

| Task | Prompt | Local reference |
|---|---|---|
| Project selection | [portfolio/prompt.txt](portfolio/prompt.txt) | [Problem](portfolio/problem.json) · [Expected answer](portfolio/expected.json) |
| Bookstore incident | [bookstore/prompt.txt](bookstore/prompt.txt) | [Decision rubric](bookstore/rubric.json) |

The project task asks for exactly three projects under several constraints.
The reference is checked exhaustively against all twenty triples. The bookstore
task asks for a diagnosis and fixes; four predefined decisions are graded,
while explanation prose is retained without a quality score.

Both prompts are fixed inputs. Reference answers are used locally and are not
sent to either model route. The [protocol](../../docs/protocol.md) describes the
controls; the [studies](../../studies/README.md) preserve the measured versions.
