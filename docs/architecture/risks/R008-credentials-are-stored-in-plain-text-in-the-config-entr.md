---
id: R008
date: 2026-10-27
category: SEC
probability: 2
impact: 3
residual_probability: 2
residual_impact: 3
strategy: accept
status: note
owner:
review: release
---
# R008: Credentials are stored in plain text in the config entry

## Risk description

If someone gets access to the HA configuration or a backup, then password and cloud token are readable in plain text, which means they can control the device or the cloud account.

## Finding in detail

**Finding.** Password and cloud token are stored unencrypted in `config_entry.data` (property of Home Assistant). The password field uses a password selector in the config flow. The integration offers no diagnostics download and sets no `extra_state_attributes` with credentials; since `5328e74` and `8cb62b2` the device identifiers no longer contain the token.

**Effect.** Whoever can read the HA configuration or a backup can read the credentials.

**Second finding: debug log.** With the log level DEBUG, `ws_connect()` writes the first and the last three characters of the hashed WebSocket password to the log (`pygoecharger_ha/__init__.py`, line 896), and the authentication answer of the charger (line 946). Debug logs are often attached to issues. Whether the authentication answer holds anything secret was not checked.

Both were reported to the maintainer before this documentation was written; he agreed that this is a risk.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 2 | 3 | 6 | medium |
| Residual risk after the countermeasure | 2 | 3 | 6 | medium |

Risk strategy: **Accept**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Home Assistant provides no vault; that part is accepted and lies with Home Assistant. For the debug log: do not log any part of the hash, only the hash type, and do not log the authentication answer in full. Proposal, not implemented; no test covers the log output.

## Status and history

<!-- risk:status -->
Accepted (note)
<!-- /risk:status -->

Assessment reviewed on 2026-10-30 after the independent review and kept: the independent review found that password and token are plain text in the config entry and that the token was in the device identifier before `5328e74`; both support the existing A 3.

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] `config_flow.py` and `__init__.py` read; no `diagnostics.py`, no credentials in `extra_state_attributes` (searched). [Code] Lines 896 and 946 of `pygoecharger_ha/__init__.py` at `main` (`e6ee0c3`) read. [Docs] Home Assistant stores config entries in `.storage/core.config_entries` in plain text.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
