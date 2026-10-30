---
id: R006
date: 2026-10-27
category: ARCH
probability: 3
impact: 2
residual_probability: 1
residual_impact: 2
strategy: mitigate
status: open
owner:
review: release
---
# R006: No `unique_id` in the config flow

## Risk description

If a user sets up the same charger a second time, then `_abort_if_unique_id_configured()` does not take effect because no `unique_id` is ever set, which means duplicate entries and duplicate entities are created.

## Finding in detail

**Finding.** `_abort_if_unique_id_configured()` is called, but no `unique_id` is set anywhere in the config flow (`async_set_unique_id` does not occur).

**Effect.** No protection against devices created twice.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 2 | 6 | medium |
| Residual risk after the countermeasure | 1 | 2 | 2 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Call `async_set_unique_id` with the serial number in the config flow. Proposal, not implemented.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

Read from the code (grep). Effect not demonstrated.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
