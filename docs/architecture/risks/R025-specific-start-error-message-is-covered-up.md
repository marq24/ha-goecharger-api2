---
id: R025
date: 2026-10-29
category: ARCH
probability: 3
impact: 1
residual_probability: 1
residual_impact: 1
strategy: mitigate
status: fixed
owner:
review: release
---
# R025: Specific start error message is covered up

## Risk description

If no device data is available at start, then `except BaseException` replaces the specific message with the general WebSocket message, which means users see an unsuitable error message.

## Finding in detail

**Finding.** `async_setup_entry`: the message "could not fetch essential information" is created inside a `try` and immediately replaced by the general WebSocket message by `except BaseException`.

**Effect.** Users see an unsuitable error message.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 1 | 3 | low |
| Residual risk after the countermeasure | 1 | 1 | 1 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

The specific `ConfigEntryNotReady` message is kept (`eb5da46`).

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

`eb5da46`. Since `eb5da46` the specific `ConfigEntryNotReady` message is kept.

## Evidence

*Evidence at the time of the finding (not today's state)*

Shown in a test (`known_bug`).  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
