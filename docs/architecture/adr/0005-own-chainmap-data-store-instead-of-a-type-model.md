# ADR-0005: Own ChainMap data store instead of a type model

## Status

Accepted (reconstructed, date unknown)

## Context and reasoning

Quick adaptation to new keys

## Decision

Own `ChainMap` data store instead of a type model

## Consequences

No schema; errors show only at runtime (`KeyError` are caught)

## Origin of this entry

Reconstructed from code and comments [Inference]. There is no decision record for it; the reasoning is inferred, not proven.

Architecture: [arc42](../arc42-ha-goecharger-api2.md) | [Back to the index](README.md)
