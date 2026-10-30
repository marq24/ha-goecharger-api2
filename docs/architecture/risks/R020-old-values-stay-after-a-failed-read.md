---
id: R020
date: 2026-10-29
category: ARCH
probability: 3
impact: 3
residual_probability: 2
residual_impact: 3
strategy: accept
status: settled
owner:
review: release
---
# R020: Old values stay after a failed read

## Risk description

If a charger goes offline in cloud mode, then `read_all_states`, `read_all_config` and `read_versions` do not overwrite the state on an empty answer and the error counter is reset, which means the entities keep showing the last values as valid.

## Finding in detail

**Finding.** Since `5328e74`, `read_all_states`, `read_all_config` and `read_versions` overwrite the stored state only if the answer is not empty (`if ret is not None and len(ret) > 0 …`). Before, the state was cleared on an error. `_read_filtered_data` returns `{}` for every status except 200/400 (for example cloud 403 or 404 when offline).

**Effect.** The coordinator keeps the last values and reports success. A charger that went offline keeps showing its last values in cloud mode. In addition `_async_update_data` resets the error counter because the `ChainMap` of the old values is not empty.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 3 | 9 | medium |
| Residual risk after the countermeasure | 2 | 3 | 6 | medium |

Risk strategy: **Accept**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

None. The maintainer confirmed in issue #173 (2026-10-27) that this is intended: stale data is better than losing all previously available information when a communication error occurs. Today's behaviour is recorded as a characterisation (`test_failed_full_read_keeps_the_previous_states`). Remaining effect: a charger that went offline keeps showing its last values in cloud mode; see also [R014](R014-entities-stay-available-on-partial-failure-and-show-old.md).

## Status and history

<!-- risk:status -->
Closed (settled, not a defect)
<!-- /risk:status -->

Intended behaviour, confirmed by the maintainer in issue #173 (2026-10-27).

## Evidence

*Evidence at the time of the finding (not today's state)*

Derived from diff and code, **not tested**. Whether the display really stays "frozen" depends on what HA does with an unchanged `last_update_success`.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
