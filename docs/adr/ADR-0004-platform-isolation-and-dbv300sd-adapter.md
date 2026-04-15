# ADR-0004: Platform Isolation and DBV-300-SD Adapter Strategy

## Status

Accepted

## Context

The system must run on Linux or Windows, while the current lab setup reports the JCM DBV-300-SD on `COM3`. The validator may ultimately require MDB, serial, or pulse-like integration. Business logic must not depend on the transport choice or on an OS-specific port naming scheme.

## Decision

We isolate validator integration into three layers:

1. transport adapter
2. protocol adapter
3. domain-facing validator adapter

The application and domain layers depend only on the bill validator interface and its domain events:

- `bill_detected`
- `bill_validated`
- `bill_rejected`
- `escrow_available`
- `bill_stacked`
- `bill_returned`
- `validator_fault`
- `validator_disabled`

The known `COM3` setting is stored in configuration only, never in domain logic.

## Consequences

### Positive

- Protocol confirmation can happen later without architectural rework.
- The same core supports serial, MDB, and simulator backends.
- Windows/Linux port differences remain infrastructural.

### Negative

- More adapter layers must be implemented.
- Real hardware integration cannot be completed until documentation and bench validation are available.

## Rejected alternatives

- Hardcoding `COM3` in payment logic
- Treating the DBV-300-SD as a generic validator with no device-specific adapter boundary
- Embedding binary protocol handling inside the application service layer
