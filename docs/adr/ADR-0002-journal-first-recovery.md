# ADR-0002: Journal-First Transaction Recovery

## Status

Accepted

## Context

The machine must survive crashes and power loss without double-vending products or double-paying change. In-memory FSM state and last-known UI state are insufficient to safely reconstruct what happened during a partially completed transaction.

## Decision

Critical transaction steps will be recorded in a durable transaction journal before or at intent boundaries. Recovery will replay journal entries and unresolved transaction records to determine:

- what was authorized;
- what was confirmed;
- what remains ambiguous;
- what requires retry, compensation, or operator intervention.

Recovery logic will trust durable journal facts over volatile state.

## Consequences

### Positive

- Power-loss recovery is deterministic and auditable.
- Critical ambiguity is explicit rather than hidden.
- Recovery behavior can be tested via replay.

### Negative

- More persistence code and journal schema design are required.
- Handlers must be written with idempotency in mind.

## Rejected alternatives

- Restore the last FSM state snapshot and continue optimistically
- Trust device state alone after reboot
- Use logs only for diagnostics instead of as recovery evidence
