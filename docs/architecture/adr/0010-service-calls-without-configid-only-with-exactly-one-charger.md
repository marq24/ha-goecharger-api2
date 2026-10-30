# ADR-0010: Service calls without configid only with exactly one charger

## Status

Accepted (2026-10-29, commit `4702213`)

## Context and reasoning

Before, the first registered charger was taken. After reloading an entry it moved to the end of the list, so the default silently switched to another charger. A wrong charger for writes (current, stop) is avoided [Inference, from the diff and a test finding].

## Decision

Services (`set_pv_data`, `stop_charging`) without `configid`: the charger is used only if exactly one is registered, otherwise `ServiceValidationError` (commit `4702213`, 2026-10-29; decision of the maintainer in the code, not explained in issue #172)

## Consequences

**Behaviour change:** whoever has several chargers and so far left out `configid` (for example a blueprint or an automation) now gets an error instead of access to the first charger. With one charger or with `configid` nothing changes. `docs/PVSURPLUS.md` and the blueprint option `charger_config_entry` ("required when using multiple chargers") already say that the charger must be named; the blueprint then passes `configid`. A blueprint instance without that option and with several chargers now gets the error. Not replayed on a device.

## Alternatives

Not chosen: define a fixed default charger or keep the order stable.

## Evidence (tests)

`test_without_configid_and_with_two_chargers_no_charger_is_guessed`, `test_with_an_empty_registry_no_charger_can_be_chosen`.

## Origin of this entry

Derived from the commit, diff and tests [Inference]; the maintainer did not give the reasoning in writing.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the index](README.md)
