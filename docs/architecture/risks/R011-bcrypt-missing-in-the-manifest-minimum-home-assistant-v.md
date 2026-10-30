---
id: R011
date: 2026-10-27
category: INT
probability: 3
impact: 3
residual_probability: 1
residual_impact: 3
strategy: mitigate
status: open
owner:
review: release
---
# R011: `bcrypt` missing in the manifest, minimum Home Assistant version unclear

## Risk description

If the integration is installed on an older Home Assistant or without an available `bcrypt`, then dependencies or APIs are missing, which means installation or start fails.

## Finding in detail

**Finding.** Missing dependency in the manifest (`bcrypt`), minimum HA version unclear (`hacs.json` 2023.8.0 versus newer APIs used).

**Effect.** Installation errors on older systems possible.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 3 | 9 | medium |
| Residual risk after the countermeasure | 1 | 3 | 3 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Add `bcrypt` to the manifest, check the minimum version and adjust `hacs.json`. Proposal, not implemented. The tests run with the newest version only.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

Read from code and manifest. I did not check whether `bcrypt` is supplied by HA.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
