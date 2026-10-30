---
id: R002
date: 2026-10-27
category: ARCH
probability: 3
impact: 3
residual_probability: 1
residual_impact: 3
strategy: mitigate
status: fixed
owner:
review: release
---
# R002: Multi-charger registry incomplete

## Risk description

If several go-eChargers are set up in one HA instance and an entry is reloaded, then the second charger is missing from the registry or the old coordinator stays registered, which means `configid` does not work for the second charger or writes go through a separate bridge.

## Finding in detail

**Finding.** Multi-charger: the registry `_COORDINATOR_PER_CONFIGENTRYID_MAP` is filled only in the constructor of `GoeChargerApiV2Service`. The constructor runs only if the service is not yet registered, so only for the first charger. A second charger is missing from the registry, `configid=<second>` leads to `KeyError`. If the first entry is unloaded, its coordinator stays in the registry.

**Effect.** The documented multi-charger operation via `configid` does not work for the second charger.

**Addendum to R002:** this is a **regression** from commit `5328e74` ("housekeeping of tasks"). Before, a `GoeChargerApiV2Service` was always created per charger entry and entered its coordinator into the registry, so `configid` worked for every charger. Since `5328e74` the service is only created for the first charger. In addition, after an entry is reloaded (for example by the automatic restart logic after more than 5 connection errors), with several chargers the **old** coordinator stays in the registry; the service then writes through a separate bridge. Read from the diff and the code, not replayed.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 3 | 9 | medium |
| Residual risk after the countermeasure | 1 | 3 | 3 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

The registry is maintained for every charger, a reload replaces the coordinator (`03b0fc3`). That no charger is guessed without `configid` is decided in ADR-0010 (`4702213`).

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

`03b0fc3`, ADR-0010 (`4702213`). The registry is maintained for every charger, reloading replaces the old coordinator. The changing default charger has been decided through ADR-0010 since `4702213` (no default with several chargers).

## Evidence

*Evidence at the time of the finding (not today's state)*

Read from the code (`service.py:17,33,41`, `__init__.py:153`ff). **Not replayed.**  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
