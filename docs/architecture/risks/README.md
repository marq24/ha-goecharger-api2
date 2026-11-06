# Risk register: `ha-goecharger-api2`

All known risks and technical debt of the integration, **one document per risk** (like the architecture decisions in [`adr/`](../adr/README.md)). The register belongs to the [arc42 documentation](../arc42-ha-goecharger-api2.md) (chapter 11).

| | |
|---|---|
| **State** | 2026-10-30, `main` at `e6ee0c3` |
| **Origin** | A comparison of code, documentation and tests, written with AI assistance (Claude Code) and reviewed by a human. None of it was checked on a real charger unless explicitly noted. |
| **Date recorded** | The day the risk entered this documentation. For [R015](R015-cloud-documentation-names-http-202-for-api-set.md) to [R023](R023-blueprint-in-main-has-no-zero-value-branch-for-invalid.md) the exact day was not traced; 2026-10-29 is the day they were added to the register. |

## How the risks are assessed

Each document states the risk as "If [cause], then [event], which leads to [impact]", gives probability W and impact A (1 to 5), the score W × A, the strategy (mitigate, accept, avoid, transfer), a countermeasure and the residual risk. **W, A and strategy are assessments, not measurements.** A risk owner has not been named; the maintainer should set one. Review: with every new release.

**Changing an assessment.** The first assessment of a closed risk (fixed, settled, superseded) is never changed. What was done and which residual risk remains, accepted or not, is written under "Countermeasure" and "Status and history", and the residual W and A carry it. An open risk may be reassessed when new facts justify it. The old values, the new values and the reason are then recorded under "Status and history" with the date (entry "Reassessment"); an assessment is never overwritten without that entry. A risk is not inflated: close it and record what remains as a new risk.

Score bands: 1 to 5 low, 6 to 12 medium, 15 and above high.

## Open risks (heat map)

Current, open risks and notes only (colour by score W × A: 🟩 low, 🟨 medium, 🟥 high).

<!-- risk:heatmap-current -->
| W \ A | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | 🟩 [R007](R007-readme-and-code-state-different-read-intervals-for-the.md) | 🟨  | 🟥  | 🟥  | 🟥  |
| **4** | 🟩  | 🟨  | 🟨  | 🟥  | 🟥  |
| **3** | 🟩 [R010](R010-check-and-write-to-16a-accesses-private-members.md) | 🟨 [R006](R006-no-unique-id-in-the-config-flow.md), [R012](R012-customfriendlynameentity-overrides-a-private-ha-method.md), [R017](R017-cloud-data-can-be-up-to-30-seconds-old.md), [R026](R026-rejected-value-stays-in-the-display.md), [R029](R029-without-cablecurrentlimit-there-is-no-limit-to-16-a-any.md), [R032](R032-tests-assert-the-exact-wording-of-messages.md) | 🟨 [R011](R011-bcrypt-missing-in-the-manifest-minimum-home-assistant-v.md), [R014](R014-entities-stay-available-on-partial-failure-and-show-old.md), [R023](R023-blueprint-in-main-has-no-zero-value-branch-for-invalid.md) | 🟨 [R016](R016-websocket-interface-is-not-officially-documented.md) | 🟥  |
| **2** | 🟩 [R009](R009-global-variable-scan-interval-is-overwritten-in-the-con.md), [R018](R018-negative-ppv-standby-cannot-be-set.md) | 🟩 [R033](R033-16-a-limiter-reads-over-http-also-in-websocket-mode.md) | 🟨 [R008](R008-credentials-are-stored-in-plain-text-in-the-config-entr.md), [R021](R021-migration-from-2-0-to-2-1-deletes-all-devices.md) | 🟨 [R019](R019-cloud-token-is-readable-via-the-key-cak-according-to-th.md), [R031](R031-stop-charging-does-not-check-the-unlock-and-may-report.md) | 🟨  |
| **1** | 🟩 [R022](R022-version-1-entries-leave-old-devices-in-the-registry.md) | 🟩  | 🟩  | 🟩  | 🟩  |
<!-- /risk:heatmap-current -->

## After the countermeasures (residual risk)

The same open risks with their residual risk once the countermeasure is in place.

<!-- risk:heatmap-residual -->
| W \ A | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | 🟩  | 🟨  | 🟥  | 🟥  | 🟥  |
| **4** | 🟩  | 🟨  | 🟨  | 🟥  | 🟥  |
| **3** | 🟩  | 🟨  | 🟨  | 🟨  | 🟥  |
| **2** | 🟩 [R018](R018-negative-ppv-standby-cannot-be-set.md), [R032](R032-tests-assert-the-exact-wording-of-messages.md) | 🟩 [R012](R012-customfriendlynameentity-overrides-a-private-ha-method.md), [R029](R029-without-cablecurrentlimit-there-is-no-limit-to-16-a-any.md) | 🟨 [R008](R008-credentials-are-stored-in-plain-text-in-the-config-entr.md), [R014](R014-entities-stay-available-on-partial-failure-and-show-old.md), [R016](R016-websocket-interface-is-not-officially-documented.md), [R019](R019-cloud-token-is-readable-via-the-key-cak-according-to-th.md), [R023](R023-blueprint-in-main-has-no-zero-value-branch-for-invalid.md) | 🟨  | 🟨  |
| **1** | 🟩 [R007](R007-readme-and-code-state-different-read-intervals-for-the.md), [R009](R009-global-variable-scan-interval-is-overwritten-in-the-con.md), [R010](R010-check-and-write-to-16a-accesses-private-members.md), [R022](R022-version-1-entries-leave-old-devices-in-the-registry.md) | 🟩 [R006](R006-no-unique-id-in-the-config-flow.md), [R017](R017-cloud-data-can-be-up-to-30-seconds-old.md), [R026](R026-rejected-value-stays-in-the-display.md), [R033](R033-16-a-limiter-reads-over-http-also-in-websocket-mode.md) | 🟩 [R011](R011-bcrypt-missing-in-the-manifest-minimum-home-assistant-v.md), [R021](R021-migration-from-2-0-to-2-1-deletes-all-devices.md) | 🟩 [R031](R031-stop-charging-does-not-check-the-unlock-and-may-report.md) | 🟩  |
<!-- /risk:heatmap-residual -->

## All risks

<!-- risk:table -->
| ID | Title | Category | W | A | Score | Strategy | Status |
|---|---|---|---|---|---|---|---|
| [R001](R001-stop-charging-locks-the-charger-after-a-write-error.md) | stop_charging locks the charger after a write error | Technology / architecture | 3 | 4 | 12 (medium) | Mitigate | Closed (fixed) |
| [R002](R002-multi-charger-registry-incomplete.md) | Multi-charger registry incomplete | Technology / architecture | 3 | 3 | 9 (medium) | Mitigate | Closed (fixed) |
| [R003](R003-active-charger-counter-with-controller-entries.md) | Active charger counter with controller entries | Technology / architecture | 2 | 3 | 6 (medium) | Mitigate | Closed (fixed) |
| [R004](R004-error-handling-for-multiple-writes-calls-the-wrong-sign.md) | Error handling for multiple writes calls the wrong signature | Technology / architecture | 2 | 2 | 4 (low) | Mitigate | Closed (fixed) |
| [R005](R005-pgrid-without-a-finiteness-check.md) | `pgrid` without a finiteness check | Technology / architecture | 1 | 3 | 3 (low) | Mitigate | Closed (fixed) |
| [R006](R006-no-unique-id-in-the-config-flow.md) | No `unique_id` in the config flow | Technology / architecture | 3 | 2 | 6 (medium) | Mitigate | Open |
| [R007](R007-readme-and-code-state-different-read-intervals-for-the.md) | README and code state different read intervals for the configuration | Documentation | 5 | 1 | 5 (low) | Mitigate | Open |
| [R008](R008-credentials-are-stored-in-plain-text-in-the-config-entr.md) | Credentials are stored in plain text in the config entry | Security & privacy | 2 | 3 | 6 (medium) | Accept | Accepted (note) |
| [R009](R009-global-variable-scan-interval-is-overwritten-in-the-con.md) | Global variable `SCAN_INTERVAL` is overwritten in the constructor | Maintainability | 2 | 1 | 2 (low) | Mitigate | Open |
| [R010](R010-check-and-write-to-16a-accesses-private-members.md) | `check_and_write_to_16a` accesses private members | Maintainability | 3 | 1 | 3 (low) | Mitigate | Open |
| [R011](R011-bcrypt-missing-in-the-manifest-minimum-home-assistant-v.md) | `bcrypt` missing in the manifest, minimum Home Assistant version unclear | Integration / third party | 3 | 3 | 9 (medium) | Mitigate | Open |
| [R012](R012-customfriendlynameentity-overrides-a-private-ha-method.md) | `CustomFriendlyNameEntity` overrides a private HA method | Integration / third party | 3 | 2 | 6 (medium) | Mitigate | Open |
| [R013](R013-no-automated-tests-in-the-repository.md) | No automated tests in the repository | Quality / testing | 4 | 3 | 12 (medium) | Mitigate | Closed (superseded) |
| [R014](R014-entities-stay-available-on-partial-failure-and-show-old.md) | Entities stay `available` on partial failure and show old values | Technology / architecture | 3 | 3 | 9 (medium) | Mitigate | Open |
| [R015](R015-cloud-documentation-names-http-202-for-api-set.md) | Cloud documentation names HTTP 202 for `/api/set` | Integration / third party | 2 | 3 | 6 (medium) | Accept | Closed (settled, not a defect) |
| [R016](R016-websocket-interface-is-not-officially-documented.md) | WebSocket interface is not officially documented | Integration / third party | 3 | 4 | 12 (medium) | Mitigate | Open |
| [R017](R017-cloud-data-can-be-up-to-30-seconds-old.md) | Cloud data can be up to 30 seconds old | Integration / third party | 3 | 2 | 6 (medium) | Mitigate | Open |
| [R018](R018-negative-ppv-standby-cannot-be-set.md) | Negative `ppv` (standby) cannot be set | Integration / third party | 2 | 1 | 2 (low) | Accept | Open |
| [R019](R019-cloud-token-is-readable-via-the-key-cak-according-to-th.md) | Cloud token is readable via the key `cak` according to the documentation | Security & privacy | 2 | 4 | 8 (medium) | Mitigate | Open |
| [R020](R020-old-values-stay-after-a-failed-read.md) | Old values stay after a failed read | Technology / architecture | 3 | 3 | 9 (medium) | Accept | Closed (settled, not a defect) |
| [R021](R021-migration-from-2-0-to-2-1-deletes-all-devices.md) | Migration from 2.0 to 2.1 deletes all devices | Technology / architecture | 2 | 3 | 6 (medium) | Mitigate | Open |
| [R022](R022-version-1-entries-leave-old-devices-in-the-registry.md) | Version 1 entries leave old devices in the registry | Maintainability | 1 | 1 | 1 (low) | Accept | Open |
| [R023](R023-blueprint-in-main-has-no-zero-value-branch-for-invalid.md) | Blueprint in `main` has no zero-value branch for invalid measurements | Integration / third party | 3 | 3 | 9 (medium) | Mitigate | Open |
| [R024](R024-error-text-of-the-charger-counts-as-success.md) | Error text of the charger counts as success | Technology / architecture | 2 | 3 | 6 (medium) | Mitigate | Closed (fixed) |
| [R025](R025-specific-start-error-message-is-covered-up.md) | Specific start error message is covered up | Technology / architecture | 3 | 1 | 3 (low) | Mitigate | Closed (fixed) |
| [R026](R026-rejected-value-stays-in-the-display.md) | Rejected value stays in the display | Technology / architecture | 3 | 2 | 6 (medium) | Mitigate | Open |
| [R027](R027-false-error-after-a-successful-multiple-write.md) | False `ERROR` after a successful multiple write | Technology / architecture | 5 | 1 | 5 (low) | Mitigate | Closed (fixed) |
| [R029](R029-without-cablecurrentlimit-there-is-no-limit-to-16-a-any.md) | Without `cableCurrentLimit` there is no limit to 16 A any more | Integration / third party | 3 | 2 | 6 (medium) | Mitigate | Open |
| [R030](R030-max-ampere-is-reset-at-every-restart.md) | Max Ampere is reset at every restart | Technology / architecture | 3 | 3 | 9 (medium) | Mitigate | Closed (fixed) |
| [R031](R031-stop-charging-does-not-check-the-unlock-and-may-report.md) | stop_charging does not check the unlock and may report success | Technology / architecture | 2 | 4 | 8 (medium) | Mitigate | Open |
| [R032](R032-tests-assert-the-exact-wording-of-messages.md) | Tests assert the exact wording of messages | Quality / testing | 3 | 2 | 6 (medium) | Mitigate | Open |
| [R033](R033-16-a-limiter-reads-over-http-also-in-websocket-mode.md) | The 16 A limiter reads over HTTP also in WebSocket mode | Technology / architecture | 2 | 2 | 4 (low) | Mitigate | Open |
<!-- /risk:table -->

## Notes

The number R028 was deliberately left out; the numbering follows the order of the findings.

The addendum to [R002](R002-multi-charger-registry-incomplete.md) is in [R002](R002-multi-charger-registry-incomplete.md).

## Open assumptions (not checked)

- Behaviour of the charger after a restart with `frc=1` set.
- Whether the charger accepts the PV data key `ids` over WebSocket exactly as over HTTP.
- Actual minimum version of Home Assistant.

## Recording a new risk

1. Copy [`_template.md`](_template.md) to `RNNN-short-title.md` with the next free number (three digits) and fill it in. The comments in the template explain the front matter and the rules; delete them when you are done.
2. Run `python tests/tools/build_risk_register.py`; it fills the tables, the heat maps and the generated blocks.
3. When a risk is fixed, do not delete the file: set the status to "Closed" and name the change that fixed it.
