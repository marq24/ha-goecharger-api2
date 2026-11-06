---
id: R031
date: 2026-10-30
category: ARCH
probability: 2
impact: 4
residual_probability: 1
residual_impact: 4
strategy: mitigate
status: open
owner:
review: release
---
# R031: stop_charging does not check the unlock and may report success

## Risk description

If the unlock write (`frc=0`) after the five minute lock fails or is not confirmed, then `stop_charging` leaves `frc=1` set and, when the answer is empty, still reports `success`, which means the charger stays locked until someone resets `frc` by hand.

## Finding in detail

**Finding.** In `service.py` (line 118) the result of the second write `async_write_key(Tag.FRC.key, 0, require_ack=True)` is not checked. On the HTTP path a non-200 answer returns `{}` and a rejection returns `{"err": ...}`; on the WebSocket path an unconfirmed write returns `{}`. `handle_write_result` only logs, and the service returns `success`. A `ValueError` is caught further down and returned as an error, but `frc` stays `1`.

[R001](R001-stop-charging-locks-the-charger-after-a-write-error.md) (fixed) covers the flag `_stop_in_progress`, which a `finally` resets; the unlock itself is this risk.

**Effect.** The user may not be able to charge after a stop request, and the automation that called the service is told that all went well. [Inference] If Home Assistant cancels the service call during the 300 s sleep, the unlock is skipped as well.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 4 | 8 | medium |
| Residual risk after the countermeasure | 1 | 4 | 4 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Check that the answer of the unlock write contains `frc`; retry once and return an error if it does not. Proposal, not implemented.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] Read from `service.py` at `main` (`e6ee0c3`) by an independent review and checked again. No test covers a failed or unconfirmed unlock: the tests for `stop_charging` check that the flag is reset, not that `frc` is set back. Not tried on a real charger.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
