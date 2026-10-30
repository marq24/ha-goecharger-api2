---
id: R005
date: 2026-10-27
category: ARCH
probability: 1
impact: 3
residual_probability: 1
residual_impact: 1
strategy: mitigate
status: fixed
owner:
review: release
---
# R005: `pgrid` without a finiteness check

## Risk description

If `set_pv_data` is called with `NaN` or `inf` as `pgrid`, then the value is sent unchecked, which means invalid JSON goes to the charger.

## Finding in detail

**Finding.** `set_pv_data` checks `pgrid` only with `isinstance(Number)` (`service.py:59`), but `ppv` and `pakku` for finiteness.

**Effect.** `NaN` or `inf` as `pgrid` can go to the charger as invalid JSON.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 1 | 3 | 3 | low |
| Residual risk after the countermeasure | 1 | 1 | 1 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

`pgrid` is checked for finiteness like `ppv` and `pakku` (`eb5da46`). The blueprint checks anyway.

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

`eb5da46`. Since `eb5da46` `set_pv_data` also checks `pgrid` for finiteness.

## Evidence

*Evidence at the time of the finding (not today's state)*

Read from the code. Low practical relevance because the blueprint checks.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
