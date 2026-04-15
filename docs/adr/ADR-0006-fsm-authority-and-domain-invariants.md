# ADR-0006: FSM Authority and Domain Invariants

## Status

Accepted

## Context

The system needs both rich workflow orchestration and strict safety invariants. A pure workflow engine without domain invariants risks unsafe transitions, while domain entities alone are not enough to coordinate asynchronous device-driven behavior such as cash acceptance, payout, vend, delivery, and recovery.

## Decision

We use two complementary control mechanisms:

- the application-layer FSM is authoritative for workflow progression;
- domain aggregates are authoritative for business invariants.

The FSM decides which state transitions and side effects are allowed next. The aggregates ensure that forbidden conditions remain impossible even if a handler is called unexpectedly.

Examples:

- the FSM sequences `WAITING_FOR_PAYMENT -> ACCEPTING_CASH -> PAYMENT_ACCEPTED`;
- the transaction aggregate forbids vend authorization before payment confirmation and payout resolution.

Recovery rebuilds the FSM from the journal, but invariant checks still execute in the aggregates after replay.

## Consequences

### Positive

- Orchestration stays explicit and testable.
- Safety rules remain enforced below the workflow layer.
- Crash recovery can rebuild state deterministically.

### Negative

- Some rules are expressed in both transition guards and aggregate invariants.
- Developers must be disciplined about keeping workflow and invariant responsibilities separate.

## Rejected alternatives

- Putting all business rules only in the FSM
- Letting aggregates coordinate all async device workflows without an explicit state machine
- Treating UI screens as the workflow source of truth
