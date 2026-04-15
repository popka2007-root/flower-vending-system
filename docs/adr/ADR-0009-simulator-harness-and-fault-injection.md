# ADR-0009: Simulator Harness and Deterministic Fault Injection

## Status

Accepted

## Context

The platform-neutral core must be testable without UI and without hardware. We also need to exercise failure scenarios that are difficult, slow, or unsafe to reproduce repeatedly on a physical vending machine.

If simulators bypass the application layer and call domain objects directly, they will stop validating the most important production seams:

- command handling;
- FSM transitions;
- event-driven handoff from payment to vending;
- health-based sale blocking;
- ambiguous transaction behavior.

## Decision

We implement Phase 6 simulators around three rules:

- mock devices implement the same contracts as real device adapters;
- failures are injected deterministically through explicit fault plans;
- scenarios drive the real `ApplicationCore` through commands and normalized validator events.

The simulator harness is therefore a headless composition root for:

- mock devices;
- in-memory inventory and money state;
- the real application orchestrators;
- an event recorder for scenario inspection.

## Consequences

### Positive

- Simulator scenarios exercise the same orchestration boundaries as production code.
- Failure scenarios are reproducible and suitable for tests.
- Real hardware adapters can later replace mocks without rewriting the application core.
- Orchestration defects, such as reserve finalization bugs, surface early.

### Negative

- Simulator behavior is intentionally simplified and can diverge from real hardware timing.
- Some ambiguous real-world outcomes still require hardware-in-the-loop testing.

## Rejected alternatives

- Randomized fault generation as the primary simulator strategy
- Direct mutation of aggregates instead of command-driven scenarios
- Separate demo-only flows that do not use the real application core
