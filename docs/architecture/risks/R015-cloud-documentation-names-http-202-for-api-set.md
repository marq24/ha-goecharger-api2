---
id: R015
date: 2026-10-29
category: INT
probability: 2
impact: 3
residual_probability: 1
residual_impact: 1
strategy: accept
status: settled
owner:
review: release
---
# R015: Cloud documentation names HTTP 202 for `/api/set`

## Risk description

If the cloud answered `/api/set` with 202 instead of 200, then the code would treat the success as an error, which would mean write commands in cloud polling are logged as failed.

## Finding in detail

**Finding.** According to the cloud documentation `/api/set` answers with **HTTP 202** on success. `_write_values_int` evaluates only `200` (and `500` with content), everything else counts as an error (`failed with http-status …`, return `{}`).

**Effect.** If the cloud really sends 202, write commands in cloud polling would be logged as errors despite success, and `handle_write_result` reports "could not write". On the WebSocket path this is not affected.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 3 | 6 | medium |
| Residual risk after the countermeasure | 1 | 1 | 1 | low |

Risk strategy: **Accept**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

None. The maintainer confirmed on 2026-10-29 in issue #172 that the real cloud answers 200 and the documentation is wrong. The test expects 200.

## Status and history

<!-- risk:status -->
Closed (settled, not a defect)
<!-- /risk:status -->

Maintainer, Issue #172.

The residual impact is lower than the original one because the code handles the answer the cloud really sends (200, maintainer in issue #172); only the documentation is wrong. The original assessment is kept because the risk is settled.

## Evidence

*Evidence at the time of the finding (not today's state)*

Documentation and code read. **Settled on 2026-10-29 by the maintainer (issue #172): the cloud answers with HTTP 200, the documentation is wrong. Not a defect in the code.** Not checked by us against the real cloud.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
