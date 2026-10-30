---
id: R010
date: 2026-10-27
category: MAINT
probability: 3
impact: 1
residual_probability: 1
residual_impact: 1
strategy: mitigate
status: open
owner:
review: release
---
# R010: `check_and_write_to_16a` accesses private members

## Risk description

If the bridge is restructured internally, then `check_and_write_to_16a` breaks because, as a module-level function, it calls the private method `bridge._read_filtered_data`, which means the 16 A limiter fails; the error is logged by the surrounding `except Exception`, but the limit is not applied.

## Finding in detail

**Finding.** `check_and_write_to_16a`: function with `@staticmethod` at module level, also private access to `bridge._read_filtered_data`.

**Effect.** Maintainability.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 1 | 3 | low |
| Residual risk after the countermeasure | 1 | 1 | 1 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Move the function into the coordinator and use a public bridge method. Proposal, not implemented.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] Read from `__init__.py` (call of `bridge._read_filtered_data` inside the function). See also [R033](R033-16-a-limiter-reads-over-http-also-in-websocket-mode.md).

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
