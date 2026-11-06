---
id: R033
date: 2026-10-30
category: ARCH
probability: 2
impact: 2
residual_probability: 1
residual_impact: 2
strategy: mitigate
status: open
owner:
review: release
---
# R033: The 16 A limiter reads over HTTP also in WebSocket mode

## Risk description

If a charger can only be reached over WebSocket, then the 16 A limiter reads its data over HTTP, which means the read fails and the limiter does not work for that charger.

## Finding in detail

**Finding.** `check_and_write_to_16a` calls `bridge._read_filtered_data` (`__init__.py`, line 265), the HTTP path. The other callers use `_read_filtered_data_from_ws_source` when the WebSocket mode is active. The README (line 138) says that for some wallboxes, for example the Fronius Wattpilot, WebSocket is the only way.

**Effect.** [Inference] On such a charger the limiter read fails and is only logged; the limiter then neither detects a 16 A cable nor writes a limit. Not tried on a device.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 2 | 4 | low |
| Residual risk after the countermeasure | 1 | 2 | 2 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Read through the same path as the rest of the coordinator (WebSocket source in WebSocket mode). Proposal, not implemented; see also [R010](R010-check-and-write-to-16a-accesses-private-members.md).

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] `__init__.py` line 265 and the callers of `_read_filtered_data_from_ws_source` read; README line 138. [Inference] The effect on a WebSocket-only charger was not tried.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
