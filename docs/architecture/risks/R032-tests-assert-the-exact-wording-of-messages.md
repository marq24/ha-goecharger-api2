---
id: R032
date: 2026-10-30
category: QA
probability: 3
impact: 2
residual_probability: 2
residual_impact: 1
strategy: mitigate
status: open
owner:
review: release
---
# R032: Tests assert the exact wording of messages

## Risk description

If the maintainer rewords an error message, then tests that assert its exact wording fail without any change in behaviour, which leads to noise in the review and to the temptation to edit the expected text until the test is green.

## Finding in detail

**Finding.** Nine of the eleven uses of `match=` in `tests/integration` match a message text and two match an exception class name (`test_coordinator_failures.py:43` and `:129`); the message texts are, for example `match="disabled or invalid"`, `match="ClientConnectionError while writing amp"` or `match="The Websocket could not be started"` (`test_bridge.py`, `test_coordinator_failures.py`, `test_coordinator_errors.py`, `test_services_and_setup.py`). The guide `writing-good-tests` (which I fetched and read myself) calls a test that only an intentional wording decision can fail a *change detector*: it fires on a redesign and sleeps through bugs.

**Effect.** When the maintainer changed messages in `eb5da46` and `4702213`, two tests failed although the behaviour was the one he wanted; he sent the new expected texts in issue #172 (2026-10-29), and the tests were adapted.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 3 | 2 | 6 | medium |
| Residual risk after the countermeasure | 2 | 1 | 2 | low |

Risk strategy: **Mitigate**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Assert the exception type and a stable part (a key, a translation key, a value that the behaviour depends on). Keep an exact text only where the text is the contract the user reads, and say so in the docstring. Proposal, to be discussed with the maintainer; not implemented.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] `grep -rn "match=" tests/integration` at `agents-md`: 11 uses, 9 of them message texts and 2 class names. [Docs] `writing-good-tests` of the Superpowers project, principle "No change detectors". The two adapted tests are `test_with_an_empty_registry_no_charger_can_be_chosen` and `test_unknown_language_falls_back_to_english_texts`. Not discussed with the maintainer yet.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
