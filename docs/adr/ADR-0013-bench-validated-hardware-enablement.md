# ADR-0013: Bench-Validated Hardware Enablement Behind Existing Contracts

## Status

Accepted

## Context

By the end of the earlier phases, the system already has platform-neutral domain and application logic, device contracts, simulator coverage, local persistence, and explicit deferred integration points for uncertain hardware protocols.

The remaining work for production readiness is real hardware enablement. The largest risk is that bench bring-up work could leak vendor-specific behavior into payment logic, vending orchestration, or recovery semantics.

## Decision

Real hardware integration must be introduced only by implementing or binding concrete adapters behind the already accepted contracts:

- `BillValidator`
- `ChangeDispenser`
- `MotorController`
- `CoolingController`
- `WindowController`
- sensor and watchdog interfaces

For the JCM DBV-300-SD specifically, real enablement must occur by replacing deferred protocol implementations with confirmed protocol adapters, while preserving the existing `transport -> protocol -> domain-facing adapter` split.

Bench validation is mandatory before any hardware-specific timeout, retry, acknowledgement, or fault-mapping policy is treated as production truth.

When the system cannot prove whether change or product was physically dispensed, recovery must remain conservative and use journal-backed manual review rather than assuming success.

## Consequences

### Positive

- hardware bring-up stays isolated from business rules;
- simulator coverage remains useful even while drivers evolve;
- migration from Windows-specific legacy behavior becomes auditable and incremental;
- unsafe ambiguity handling cannot be hidden inside device-specific shortcuts.

### Negative

- production enablement depends on staged bench work rather than code generation alone;
- some workflows remain scaffolded until device documentation and test equipment are available;
- more explicit operator procedures are required for reconcile and ambiguous recovery.

## Rejected alternatives

- embedding vendor protocol logic into payment or vending services
- treating simulator behavior as sufficient proof of hardware correctness
- hardcoding production timeouts and fault mappings before bench confirmation
- assuming success after restart when payout or vend completion is ambiguous
