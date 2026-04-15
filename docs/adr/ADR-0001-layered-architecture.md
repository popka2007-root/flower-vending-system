# ADR-0001: Layered Architecture and Bounded Contexts

## Status

Accepted

## Context

The vending machine software must be production-grade, cross-platform, testable without hardware, and resilient to device failures and power loss. The legacy system exhibited instability, so responsibilities must be sharply separated to prevent device integration details from leaking into business logic.

## Decision

We adopt a layered architecture with the following top-level module groups:

- `domain`
- `app`
- `devices`
- `infrastructure`
- `ui`
- `payments`
- `inventory`
- `vending`
- `cooling`
- `telemetry`
- `config`
- `tests`
- `simulators`

Within this structure:

- domain models business state and invariants;
- application orchestrates workflows and FSM transitions;
- devices define hardware-facing interfaces and adapters;
- infrastructure provides persistence, logging, config loading, and platform integration;
- UI communicates with the application layer via commands and view models only.

## Consequences

### Positive

- Core logic is testable without GUI or hardware.
- Linux/Windows differences are localized.
- Future card payments can be added without rewriting vending logic.
- Device simulators can mirror production contracts.

### Negative

- More modules and interfaces increase initial complexity.
- Integration takes more disciplined dependency management.

## Rejected alternatives

- Monolithic service with embedded serial logic and UI state coupling
- Device-specific branching inside business logic
- OS-specific implementation in the core orchestration layer
