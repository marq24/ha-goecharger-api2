---
id: R023
date: 2026-10-29
category: INT
probability: 3
impact: 3
residual_probability: 2
residual_impact: 3
strategy: mitigate
status: open
owner:
review: release
---
# R023: Blueprint in `main` has no zero-value branch for invalid measurements

## Risk description

If a sensor of the PV blueprint fails during the day, then the blueprint skips the delivery instead of sending zero values, which means the moving averages of the wallbox stand still and charging from the grid may happen unintentionally.

## Finding in detail

**Finding.** The blueprint version in `main` (PR #171 by MrCodeLabs; the maintainer then changed it by hand in `30adcbd`, "manually merged PR #174", which is closed) does **not** contain the extensions of the version of PR #171 as its author submitted it: on invalid measurements the day's delivery is **skipped** (no zero value), on a wrong target selection `stop` with `error: true` every 5 seconds, `mode: single` without `max_exceeded: silent`, no grace period. The extensions are proposed in the fork branch `proposal/invalid-data-policy`. The behaviour is stated in the blueprint text as a deliberate decision ("does not clear its previous averages").

**Effect.** If a sensor fails during the day, the moving averages of the wallbox stand still. [Inference] Unwanted charging from the grid is then possible. "Send zero values" would avoid this risk.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 3 | 9 | medium |
| Residual risk after the countermeasure | 2 | 3 | 6 | medium |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

The behaviour is described in the blueprint as a deliberate decision. An option "send zero values" would be the countermeasure. Proposal.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

Source code read.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
