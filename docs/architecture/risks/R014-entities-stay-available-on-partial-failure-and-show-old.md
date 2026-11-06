---
id: R014
date: 2026-10-27
category: ARCH
probability: 3
impact: 3
residual_probability: 2
residual_impact: 3
strategy: mitigate
status: open
owner:
review: release
---
# R014: Entities stay `available` on partial failure and show old values

## Risk description

If the device partly fails, then the data stays and the entities remain `available` as long as the last update succeeded, which means users and automations take old values for current.

## Finding in detail

**Finding.** `available` follows `last_update_success`. A failed HTTP read raises `UpdateFailed`, so the entities become unavailable at once. While a WebSocket is connected, during the two minute error pause and while a restart is planned, `_async_update_data` returns the stored data as a success.

**Effect.** In these three situations the user sees old values as current.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 3 | 9 | medium |
| Residual risk after the countermeasure | 2 | 3 | 6 | medium |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Mark the data as stale when the WebSocket has delivered nothing for a defined time, and during the error pause. Proposal, not implemented; there is no test for it.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

Assessment reviewed on 2026-10-30 after the independent review and kept: the review named three situations in which stored data counts as success (WebSocket connected, error pause, planned restart), which supports W 3 and A 3. The WebSocket-loss path (watchdog in `__init__.py`, around line 515) was not read in full.

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] `available` = `last_update_success`; the three branches that return stored data read in `_async_update_data`. [Inference] How long a connected WebSocket can stay silent was not measured.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
