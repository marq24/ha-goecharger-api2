---
id: R026
date: 2026-10-29
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
# R026: Rejected value stays in the display

## Risk description

If the charger rejects a write command in WebSocket mode, then the integration has already taken the requested value into `coordinator.data`, which means Home Assistant shows the rejected value until the device reports the key again.

## Finding in detail

**Finding.** After `03b0fc3`, writing in WebSocket mode stores the requested value in `coordinator.data` at once.

**Effect.** If the charger rejects (only a warning in the log), HA shows the rejected value until the device reports the key again.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 2 | 6 | medium |
| Residual risk after the countermeasure | 1 | 2 | 2 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Take over the value only after the acknowledgement or reset it on rejection; `require_ack` exists since PR #177 but is used only for `tcl` and `stop_charging`. Proposal. Today's behaviour is recorded in a test.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

Derived from the code, behaviour recorded in a test.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
