# Architecture decisions (ADR)

Every decision is in a file of its own, numbered consecutively. The entries ADR-0001 to ADR-0009 are **reconstructed** from code and comments because the repository has no decision records. ADR-0010 and ADR-0011 come from the course of the collaboration in October 2026.

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](0001-prefer-websocket-polling-as-fallback.md) | Prefer WebSocket, polling as fallback | Accepted (reconstructed, date unknown) |
| [ADR-0002](0002-operating-mode-follows-from-the-password.md) | Operating mode follows from the password | Accepted (reconstructed, date unknown) |
| [ADR-0003](0003-bridge-as-a-sub-library-in-the-same-folder.md) | Bridge as a sub-library in the same folder | Accepted (reconstructed, date unknown) |
| [ADR-0004](0004-declarative-entity-descriptions.md) | Declarative entity descriptions | Accepted (reconstructed, date unknown) |
| [ADR-0005](0005-own-chainmap-data-store-instead-of-a-type-model.md) | Own ChainMap data store instead of a type model | Accepted (reconstructed, date unknown) |
| [ADR-0006](0006-hibernation-in-polling.md) | Hibernation in polling | Accepted (reconstructed, date unknown) |
| [ADR-0007](0007-pv-data-through-an-ha-automation-instead-of-extra-hardware.md) | PV data through an HA automation instead of extra hardware | Accepted (reconstructed, date unknown) |
| [ADR-0008](0008-restart-by-config-reload-on-persistent-errors.md) | Restart by config reload on persistent errors | Accepted (reconstructed, date unknown) |
| [ADR-0009](0009-no-automated-tests-in-the-repository.md) | No automated tests in the repository | Superseded by ADR-0011 |
| [ADR-0010](0010-service-calls-without-configid-only-with-exactly-one-charger.md) | Service calls without configid only with exactly one charger | Accepted (2026-10-29, commit `4702213`) |
| [ADR-0011](0011-regression-tests-in-the-repository.md) | Regression tests in the repository | Accepted (2026-10-29, PRs #178 and #179) |

## Recording a new decision

1. Copy [`_template.md`](_template.md) to `NNNN-short-title.md` with the next free number (four digits) and fill it in: status, context and reasoning, decision, consequences, origin. The comment in the template lists the rules; delete it when you are done.
2. When a decision is replaced, do not delete the old entry; set its status to "Superseded by ADR-NNNN".
3. Add it to the table above and to chapter 9 of the [arc42 documentation](../arc42-ha-goecharger-api2.md).
