# ADR-0001: Prefer WebSocket, polling as fallback

## Status

Accepted (reconstructed, date unknown)

## Context and reasoning

Efficiency; some devices (Wattpilot) offer no HTTP API [Docs]

## Decision

Prefer WebSocket, polling as fallback

## Consequences

Two data paths with different write results (on the WebSocket an empty `{}` or a dict with the value; on HTTP a dict or `{"err": ...}`)

## Origin of this entry

Reconstructed from code and comments [Inference]. There is no decision record for it; the reasoning is inferred, not proven.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the index](README.md)
