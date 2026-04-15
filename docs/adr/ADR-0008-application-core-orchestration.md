# ADR-0008: Application Core Orchestration

## Status

Accepted

## Context

The vending machine needs explicit orchestration across payment, change, vend, pickup, health, and recovery. Putting all logic into one service object would make it hard to test, hard to evolve, and easy to couple directly to device details.

## Decision

We implement the application core as a small set of cooperating orchestrators connected through:

- a typed command bus;
- a typed event bus;
- an explicit FSM engine;
- dedicated coordinators for transaction, payment, recovery, and health;
- a top-level vending controller.

The handoff from payment completion to vending is event-driven through `vend_authorized`.

## Consequences

### Positive

- Each orchestration concern stays testable in isolation.
- The payment flow can complete before vend authorization is emitted.
- Future telemetry, journal, or UI listeners can subscribe without changing the coordinators.

### Negative

- More wiring is required in bootstrap.
- Debugging may cross several orchestrators and event subscriptions.

## Rejected alternatives

- One monolithic application service handling all commands and device calls
- Direct UI-to-device coordination
- Immediate vend calls from raw validator events without a payment settlement step
