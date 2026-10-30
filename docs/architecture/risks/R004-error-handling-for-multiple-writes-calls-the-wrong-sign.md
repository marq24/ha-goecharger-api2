---
id: R004
date: 2026-10-27
category: ARCH
probability: 2
impact: 2
residual_probability: 1
residual_impact: 2
strategy: mitigate
status: fixed
owner:
review: release
---
# R004: Error handling for multiple writes calls the wrong signature

## Risk description

If the connection drops during a multiple write (vehicle selection `ct`), then `_handle_client_connection_error` is called with one argument instead of two, which means a `TypeError` replaces the clean error handling.

## Finding in detail

**Finding.** `async_write_multiple_keys`: `_handle_client_connection_error` is called with one argument instead of two (`__init__.py:674`).

**Effect.** `TypeError` instead of clean error handling when the connection drops during writing (affects the vehicle selection `ct`).

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 2 | 4 | low |
| Residual risk after the countermeasure | 1 | 2 | 2 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

The call now has two arguments (`03b0fc3`).

## Status and history

<!-- risk:status -->
Closed (fixed)
<!-- /risk:status -->

`03b0fc3`. The call now has two arguments.

## Evidence

*Evidence at the time of the finding (not today's state)*

Replayed in a test. Still in `main`.  

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
