# Historical recovery utilities

These two scripts were used to continue the interrupted October 5 follow-up
and assemble its completed responses without changing the stopped collections.
Their contents are preserved from the published study implementation.

- [continue_followup.py](continue_followup.py) matched completed segments to the
  original schedule and recorded each capacity failure before manual continuation.
- [assemble_followup.py](assemble_followup.py) copied completed evidence into an
  audited view, preserving source versions and the original raw segments.

They depend on the original private captures and repository layout. For a
historical replay, use the corresponding recorded source/commit. The current
experiment entry point is described in the [code guide](../../../experiment/README.md).
The [amendments](../plan/amendments.md) explain why these utilities were needed.
