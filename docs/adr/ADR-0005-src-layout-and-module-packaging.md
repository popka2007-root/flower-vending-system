# ADR-0005: Src Layout and Module Packaging

## Status

Accepted

## Context

The project must expose explicit module boundaries for domain, application, devices, infrastructure, UI, and simulators while remaining maintainable as a single deployable product. A flat repository-level package layout would make imports fragile and increase the chance of environment-dependent behavior.

## Decision

The repository uses a `src/flower_vending/` package root with subpackages for:

- `app`
- `domain`
- `devices`
- `infrastructure`
- `payments`
- `inventory`
- `vending`
- `cooling`
- `telemetry`
- `ui`
- `simulators`

Repository-level folders such as `config/`, `docs/`, `scripts/`, and `tests/` remain outside the runtime package.

## Consequences

### Positive

- Packaging and imports are explicit.
- Top-level bounded contexts stay visible without fragmenting deployment.
- Tests can exercise the core through one product namespace.
- Platform-specific code has a clearly bounded home under infrastructure.

### Negative

- Some users may expect the requested module names as repository-root packages.
- Empty directories may exist temporarily until later implementation phases populate them.

## Rejected alternatives

- Flat repository root packages without `src/`
- Multiple separately packaged services
- UI, persistence, and device code mixed directly under one generic package
