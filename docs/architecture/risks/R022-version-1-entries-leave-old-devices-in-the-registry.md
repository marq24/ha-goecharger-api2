---
id: R022
date: 2026-10-29
category: MAINT
probability: 1
impact: 1
residual_probability: 1
residual_impact: 1
strategy: accept
status: open
owner:
review: release
---
# R022: Version 1 entries leave old devices in the registry

## Risk description

If a version 1 entry is migrated directly to 2.1, then the migration skips deleting the devices and the clean-up function no longer exists, which means old devices with the earlier identifier stay in the registry.

## Finding in detail

**Finding.** Entries with version 1 are migrated directly to 2.1 and skip deleting the devices. The old clean-up function `check_device_registry` was removed.

**Effect.** Old devices with the earlier identifier (which contained the token for cloud entries) stay in the registry there. Very rare edge case.

## Assessment

<!-- risk:assessment -->
| | W | A | Score (W × A) | |
|---|---|---|---|---|
| Assessment | 1 | 1 | 1 | low |
| Residual risk after the countermeasure | 1 | 1 | 1 | low |

Risk strategy: **Accept**. Scale: W 1 (very unlikely) to 5 (very likely), A 1 (low) to 5 (severe); score 1 to 5 low, 6 to 12 medium, 15 and above high.
<!-- /risk:assessment -->

## Countermeasure

Accepted: very rare edge case.

## Status and history

<!-- risk:status -->
Open
<!-- /risk:status -->

Assessment reviewed on 2026-10-30 after the independent review and kept: a token in the local registry can only be read with access to the Home Assistant configuration (see [R008](R008-credentials-are-stored-in-plain-text-in-the-config-entr.md)) and the case is a rare edge, so A 1 stays. The review considered A 1 questionable because of the token.

## Evidence

*Evidence at the time of the finding (not today's state)*

[Code] Read from the diff; the identifier format before and after is in the migration function of `__init__.py`.

## Note on the assessment

W, A, strategy and residual risk are **assessments** by the author of this documentation (with AI assistance) [Inference]. They are not measured and not agreed with the maintainer. The risk owner should confirm or change them.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the register](README.md)
