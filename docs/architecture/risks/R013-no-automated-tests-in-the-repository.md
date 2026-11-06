---
id: R013
date: 2026-10-27
category: QA
probability: 4
impact: 3
residual_probability: 2
residual_impact: 3
strategy: mitigate
status: superseded
owner:
review: release
---
# R013: No automated tests in the repository

## Risk description

If code is changed or restructured, then an automatic check is missing, which means regressions are noticed only by users.

## Finding in detail

**Finding.** No tests in the repo (superseded: since PR #178 they are in `tests/integration`).

**Effect.** Regressions are found only by users.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 4 | 3 | 12 | medium |
| Residual risk after the countermeasure | 2 | 3 | 6 | medium |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

The regression tests have been in the repository since PR #178 and have run on push and pull request since PR #179 (ADR-0011). They check with fakes, not on the device, so a residual risk remains.

## Status and history

<!-- risk:status -->
Closed (superseded)
<!-- /risk:status -->

PR #178, #179.

## Evidence

*Evidence at the time of the finding (not today's state)*

[Docs] PR #178 ("let's add the tests to main") was merged on 2026-10-29 at 18:23 UTC and PR #179 (CI) at 20:17 UTC.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
