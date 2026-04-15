# ADR-0007: Device Contracts and DBV-300-SD Split

## Status

Accepted

## Context

The machine must support real hardware, deterministic simulators, and later protocol confirmation work for the JCM DBV-300-SD without rewriting the payment and vending core. The most fragile boundary is the bill validator because its physical transport and protocol are not fully confirmed yet.

## Decision

We separate the validator stack into:

1. a domain-facing `BillValidator` contract;
2. a raw `DBV300Transport` layer;
3. a semantic `DBV300Protocol` layer;
4. a `DBV300SDValidator` adapter that translates protocol events into normalized validator events.

The application core will depend only on `BillValidator`.

The known `COM3` deployment fact is configuration only. It must not appear in domain or application logic.

## Consequences

### Positive

- protocol uncertainty is isolated;
- serial transport can be implemented safely now;
- simulators can target the same contract;
- the application layer remains OS- and transport-agnostic.

### Negative

- extra adapter layers add some complexity;
- the validator is not runnable against real hardware until the protocol is confirmed.

## Rejected alternatives

- hardcoding serial behavior into payment logic
- treating DBV-300-SD as a generic validator with no dedicated adapter stack
- inventing protocol frames and timings before documentation or bench confirmation
