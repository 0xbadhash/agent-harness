# ADR 001 — Tier review depth by door class

**Status:** accepted
**Date:** 2026-11-27
**Deciders:** operator, agent

## Context

Every shipped diff currently gets the same review ritual. A local refactor and a
schema migration have the same blast radius only on paper; treating them alike
spends review attention where it does not reduce risk.

## Decision

Key review depth off the existing `**Door:**` field. A two-way door needs the
agent gates and a rollback line. A one-way door additionally needs a human
sign-off and a named rollout plan.

## Consequences

- **Reversibility:** easy. The tier table is skill text and a validator field;
  reverting restores the flat review without touching history.
- **Surprise:** a reader may expect every PR to get a human sign-off; the
  document states which door classes skip it and why.
- **Tradeoff:** two-way doors get less human attention, in exchange for faster
  landing and a tighter human budget on irreversible changes.
