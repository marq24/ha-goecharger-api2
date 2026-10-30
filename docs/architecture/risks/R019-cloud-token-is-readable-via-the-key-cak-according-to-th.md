---
id: R019
date: 2026-10-29
category: SEC
probability: 2
impact: 4
residual_probability: 2
residual_impact: 3
strategy: mitigate
status: open
owner:
review: release
---
# R019: Cloud token is readable via the key `cak` according to the documentation

## Risk description

If the key `cak` is readable locally without login, then anyone on the network can read the cloud token, which means protecting the token in the config entry has only limited effect.

## Finding in detail

**Finding.** The cloud API documentation (`cloudapi-en.md`, lines 13 and 15) says the cloud token is readable via the key `cak`. The key also appears in the WebSocket data (debug log in issue #176).

**Effect.** A measure of the integration to protect the token only in the config entry would then be only partly effective. I did not check whether `cak` is readable locally without login.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 4 | 8 | medium |
| Residual risk after the countermeasure | 2 | 3 | 6 | medium |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Check whether `cak` is readable locally without login (read-only, on the device); depending on the result document it or advise the user to protect local access. Not checked.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

[Docs] `cloudapi-en.md` lines 13 and 15; `cak` is not listed in `apikeys-en.md`. [Code] The integration does not request `cak` itself. Not checked on a device.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
