# ADR-0011: Regression tests in the repository

## Status

Accepted (2026-10-29, PRs #178 and #179)

## Context and reasoning

The maintainer took over the tests in PR #178 and the adapted workflows in PR #179. Before that there were no tests in the repository (ADR-0009). Regressions should be noticed before a release, also when code is restructured [Inference, from the course of issue #172].

## Decision

The regression tests are in the repository (`tests/integration`) and run on every push to `main` and on every pull request (`.github/workflows/tests.yaml`). Open findings carry the markers `known_bug` or `needs_decision` and are not blocking.

## Consequences

Tests and report must be maintained; a fixed finding requires removing its marker by hand. The tests check with fakes, not on the device (see test concept).

## Origin of this entry

Derived from the commit, diff and tests [Inference]; the maintainer did not give the reasoning in writing.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the index](README.md)
