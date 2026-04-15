# ADR-0003: Cash Transaction and Change Safety

## Status

Accepted

## Context

The legacy flow included a separate manual "Change" button, which is unsafe because it decouples cash settlement from transaction completion. The new system must ensure that change payout is part of the payment transaction and must not occur as an uncontrolled manual side effect except in explicitly designed service or exception scenarios.

## Decision

Cash payment is modeled as a single transaction flow:

1. validate sale preconditions;
2. verify safe payout capability;
3. reserve change inventory;
4. enable the bill validator;
5. accumulate confirmed cash;
6. finalize payment amount;
7. issue and confirm change payout if needed;
8. only then authorize product vend;
9. complete the transaction and release reservations.

The machine enters exact-change-only mode or blocks cash sales if safe payout cannot be guaranteed under policy.

## Consequences

### Positive

- Prevents accepting money for a sale that cannot be settled safely.
- Reduces double-payout and under-refund risk.
- Makes recovery and auditing tractable.

### Negative

- Requires reservation and reconciliation logic for change inventory.
- Some marginal sales will be refused for safety reasons.

## Rejected alternatives

- Manual user-triggered change payout outside the purchase transaction
- Accept cash first and decide about change only after overpayment occurs
- Keep exact-change handling as a UI-only concern
