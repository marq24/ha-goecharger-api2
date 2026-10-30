---
id: R027
date: 2026-10-29
category: ARCH
probability: 5
impact: 1
residual_probability: 1
residual_impact: 1
strategy: mitigate
status: fixed
owner:
review: release
---
# R027: False `ERROR` after a successful multiple write

## Risk description

If the user changes the vehicle type in WebSocket mode, then `write_multiple_values_to_keys` returns `{}` and `handle_write_result` skips only `None`, which means a false `ERROR` appears in the log after every successful selection.

## Finding in detail

**Finding.** `write_multiple_values_to_keys` returns `{}` in WebSocket mode; `handle_write_result` skips only `None`.

**Effect.** After every successful vehicle selection a false `ERROR` appears in the log ("could not write multiple value").

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 5 | 1 | 5 | low |
| Residual risk after the countermeasure | 1 | 1 | 1 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

`handle_write_result` also skips an empty result in WebSocket mode (`9e7d62a`).

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

`9e7d62a`. Since `9e7d62a` `handle_write_result` also skips an empty result in WebSocket mode.

## Evidence

*Evidence at the time of the finding (not today's state)*

Shown in a test (`known_bug`).  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
