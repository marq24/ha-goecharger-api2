---
id: R001
date: 2026-10-27
category: ARCH
probability: 3
impact: 4
residual_probability: 1
residual_impact: 4
strategy: mitigate
status: fixed
owner:
review: release
---
# R001: stop_charging locks the charger after a write error

## Risk description

If the service `stop_charging` is called in WebSocket mode, then an uncaught `TypeError` after the first write (`frc=1`) leaves the flag `_stop_in_progress` set and `frc=0` is never sent, which means the user cannot charge any more and further stop requests are rejected with "already in progress". A failed or unconfirmed unlock after the wait is tracked as [R031](R031-stop-charging-does-not-check-the-unlock-and-may-report.md).

## Finding in detail

**Finding.** `stop_charging` in WebSocket mode: `write_value_to_key` returns `None`, then `Tag.FRC.key in resp` raises `TypeError`; only `ValueError` is caught. `frc=1` is set, `frc=0` is never sent, `_stop_in_progress` stays `True`.

**Effect.** The charger stays locked until someone resets `frc` by hand.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 4 | 12 | medium |
| Residual risk after the countermeasure | 1 | 4 | 4 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

A `finally` always resets the flag, both writes require an acknowledgement (`require_ack`). Done in `03b0fc3`, `9e7d62a` and `d876dfd`.

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

`03b0fc3`, `9e7d62a`. The `TypeError` in WebSocket mode is gone (`write_value_to_key` returns `{key: value}`), `_stop_in_progress` is reset in a `finally` since `9e7d62a`. Both tests are green.

## Evidence

*Evidence at the time of the finding (not today's state)*

Replayed in a test. **Not** checked on a real device. Still in `main`.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
