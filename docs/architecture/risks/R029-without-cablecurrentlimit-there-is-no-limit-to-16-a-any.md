---
id: R029
date: 2026-10-29
category: INT
probability: 3
impact: 2
residual_probability: 2
residual_impact: 2
strategy: mitigate
status: open
owner:
review: release
---
# R029: Without `cableCurrentLimit` there is no limit to 16 A any more

## Risk description

If `cll` has content but no `cableCurrentLimit`, then since `98af3e0` the integration sets no 16 A limit and does not check `adi`, which means sliders allow higher values although an adapter might be attached.

## Finding in detail

**Finding.** `98af3e0`: if `cableCurrentLimit` is missing in `cll`, there is no longer a limit to 16 A and `adi` is no longer checked; Core devices without the key were limited to be safe before.

**Effect.** Sliders allow higher values; the charger limits an adapter itself. The assumption "only Flex has the key" is not proven.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 2 | 6 | medium |
| Residual risk after the countermeasure | 2 | 2 | 4 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Check read-only on a charger which firmware delivers `cableCurrentLimit` and prove or disprove the assumption "Flex devices only"; the documentation and changelogs say nothing about it. The charger limits an adapter itself, which reduces the impact.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

Read from the diff, behaviour recorded in a test.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
