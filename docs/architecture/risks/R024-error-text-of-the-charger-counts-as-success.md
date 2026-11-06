---
id: R024
date: 2026-10-29
category: ARCH
probability: 2
impact: 3
residual_probability: 1
residual_impact: 3
strategy: mitigate
status: fixed
owner:
review: release
---
# R024: Error text of the charger counts as success

## Risk description

If the charger answers a write command with an error text instead of `true`, then `_write_values_int` evaluates the answer only for "truthy", which means rejections (also for `ids`) are reported as success.

## Finding in detail

**Finding.** `_write_values_int` checks the answer of the charger for the key only for "true". According to `http-en.md` the value can be `true` or an **error text**. The code treats a text as success.

**Effect.** Rejections by the charger (also for `ids`) would be reported as success.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 3 | 6 | medium |
| Residual risk after the countermeasure | 1 | 3 | 3 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

The test is green on `main` at `9e7d62a`; which change caused this was not traced.

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

(commit not traced). The test `test_write_rejected_by_charger_returns_err` is green on `9e7d62a`; I did not trace when exactly the answer with an error text is evaluated.

## Evidence

*Evidence at the time of the finding (not today's state)*

Derived from code and documentation, shown in a test with a fake (`known_bug`). **Not** checked on a device.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
