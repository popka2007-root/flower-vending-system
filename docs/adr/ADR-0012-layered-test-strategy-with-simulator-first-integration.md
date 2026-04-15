# ADR-0012: Layered Test Strategy with Simulator-First Integration

## Status

Accepted

## Context

The product now has a platform-neutral core, deterministic simulators, durable local persistence, and a presenter-based UI layer. We need executable coverage that validates these boundaries without requiring real hardware or a GUI runtime for every run.

The most important risks are:

- payment and vend orchestration regressions;
- recovery regressions after reboot or ambiguous side effects;
- simulator drift away from the real command/event flow;
- silent gaps between requirements and current implementation.

## Decision

We adopt a layered automated test strategy:

- unit tests for isolated policy and algorithm behavior;
- simulator-backed integration tests for end-to-end orchestration;
- recovery tests for persistence and journal evidence;
- explicit `expectedFailure` coverage where requirements are known but implementation is not yet present.

Integration tests must prefer the real `ApplicationCore` plus simulator devices over demo-only shortcuts.

## Consequences

### Positive

- Regression coverage follows the accepted architecture.
- Recovery and fault paths are continuously testable without hardware.
- Known gaps such as pickup-timeout policy are visible in the suite rather than hidden.

### Negative

- Some runtime behavior still cannot be validated without optional dependencies or hardware.
- Standard-library tests are slightly more verbose than a richer third-party test framework.

## Rejected alternatives

- testing only individual classes without end-to-end simulator coverage
- marking missing requirements as undocumented instead of explicit expected failures
- relying only on manual simulator scripts instead of executable test cases
