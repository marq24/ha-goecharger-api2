---
id: R030
date: 2026-10-29
category: ARCH
probability: 3
impact: 3
residual_probability: 1
residual_impact: 3
strategy: mitigate
status: fixed
owner:
review: release
---
# R030: Max Ampere is reset at every restart

## Risk description

If Home Assistant or the integration restarts, then according to the maintainer the integration resets the maximum current, which means a configured value is lost and the limit no longer applies until it is set again.

## Finding in detail

**Finding.** According to the maintainer (issue #176) the integration resets the maximum current (Max Ampere) at every restart. This happens only when `limit_to16a` is true: then `check_and_write_to_16a` writes 16 to every `ama` or `amp` value above 16 (`__init__.py`, `const.py`).

**Effect.** A previously set value is lost; the limit then no longer applies until it is set again.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 3 | 9 | medium |
| Residual risk after the countermeasure | 1 | 3 | 3 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

The maintainer changed the detection in `4c7207c` ("alternate handling of `cableCurrentLimit`"): with `cll` content but without `cableCurrentLimit` the limit to 16 A is no longer set. That change is the cause of [R029](R029-without-cablecurrentlimit-there-is-no-limit-to-16-a-any.md). A test that restarts with a 32 A charger and keeps the value is still missing.

**Residual risk (W 1, A 3, as assessed from the start).** The limiter stays on for chargers that really are limited to 16 A. If the detection is wrong ([R029](R029-without-cablecurrentlimit-there-is-no-limit-to-16-a-any.md), [R033](R033-16-a-limiter-reads-over-http-also-in-websocket-mode.md)), the user charges slower than possible. This is accepted for the case of a really limited charger; the other cases are tracked in [R029](R029-without-cablecurrentlimit-there-is-no-limit-to-16-a-any.md) and [R033](R033-16-a-limiter-reads-over-http-also-in-websocket-mode.md).

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

Fixed for the reporter in `4c7207c` (2026-10-28); the reporter wrote "Working ;)" on 2026-10-29. Issue #176 is still open. The original assessment (W 3, A 3) is kept. Not reproduced by us and not checked on a real device.

## Evidence

*Evidence at the time of the finding (not today's state)*

Statement of the maintainer, **not** replayed by us and no test for it. Whether it comes from the 16 A limiter ([R029](R029-without-cablecurrentlimit-there-is-no-limit-to-16-a-any.md)) or from taking over values at start is open.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
