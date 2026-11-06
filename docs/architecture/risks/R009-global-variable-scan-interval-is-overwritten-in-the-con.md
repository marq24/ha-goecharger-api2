---
id: R009
date: 2026-10-27
category: MAINT
probability: 2
impact: 1
residual_probability: 1
residual_impact: 1
strategy: mitigate
status: open
owner:
review: release
---
# R009: Global variable `SCAN_INTERVAL` is overwritten in the constructor

## Risk description

If several entries with different intervals are set up, then every constructor overwrites the global variable, which means the last value set applies as the default.

## Finding in detail

**Finding.** `SCAN_INTERVAL` is a module-level default (10 s) that the coordinator constructor assigns for each entry (`__init__.py`, constructor and the two places that use it). The defaults are not consistent: 10 s for the module, 5 s for the constructor argument, 30 or 120 s in the config flow (`config_flow.py:79` and `:88`).

**Effect.** With several entries the last value set is the global default. Nothing else in the integration reads the global `SCAN_INTERVAL`; each coordinator uses the interval it has just set for itself, so there is no wrong interval today. The risk is a future reader of the global.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 1 | 2 | low |
| Residual risk after the countermeasure | 1 | 1 | 1 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Keep the interval per coordinator instead of globally. Proposal, not implemented.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

Reassessment 2026-10-30 (independent review, open risk): impact A 2 → 1 and residual impact A 2 → 1 (W unchanged: 2 and 1). Reason: a search over the integration finds no other reader of the global, so a wrong value has no effect today. Original assessment: W 2, A 2, residual W 1, A 2.

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] Searched all uses of `SCAN_INTERVAL` in `custom_components/goecharger_api2`: the definition, the assignment in the constructor and the uses right after it. No other reader.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
