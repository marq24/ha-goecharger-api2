---
id: R016
date: 2026-10-29
category: INT
probability: 3
impact: 4
residual_probability: 2
residual_impact: 3
strategy: mitigate
status: open
owner:
review: release
---
# R016: WebSocket interface is not officially documented

## Risk description

If go-e changes firmware or cloud, then the reverse-engineered WebSocket login or message format breaks without warning, which means all users in the preferred mode (with password) no longer receive data.

## Finding in detail

**Finding.** The preferred data path (WebSocket) is not officially documented: the official go-e documentation has no WebSocket document, and the README calls it "(undocumented)" (line 136). Login procedure and messages are reverse engineered.

**Effect.** A firmware or cloud change by go-e can break it without warning. The README already mentions connection problems with firmware 60.2 and a race with the go-e app during the update from 60.3 to 60.4.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 4 | 12 | medium |
| Residual risk after the countermeasure | 2 | 3 | 6 | medium |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Watch firmware changes by go-e, secure the login with tests (the fakes do not detect a change by go-e) and check whether a fallback to HTTP is possible on failure. Proposal.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

[Docs] Listing of the official documentation repository (cloud, http, mqtt, modbus, ocpp and others, no WebSocket); README lines 31, 38 to 42 and 136.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
