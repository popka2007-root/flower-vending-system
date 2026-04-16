# Phase 9 - Tests

## Scope of this phase

This phase adds executable test coverage across the already implemented core, simulator, persistence, and UI-adjacent layers.

The goals are:

- add unit tests for core financial safety logic;
- add simulator-backed integration tests for the cash/vend lifecycle;
- add recovery and persistence tests for reboot and journal evidence;
- cover the requested edge cases explicitly;
- keep tests aligned with the existing architecture and accepted ADRs.

## Test strategy

The implemented test strategy is intentionally layered.

### Unit tests

Unit tests target isolated policy and algorithm behavior without full application orchestration.

In this phase, unit coverage focuses on `ChangeManager`:

- exact-change-only assessment when worst-case change is unsafe;
- reserve rejection when accounting inventory is insufficient.

### Integration tests

Integration tests use the real `ApplicationCore` together with Phase 6 simulators through `SimulationHarness`.

This is important because the tests exercise:

- command bus dispatch;
- FSM transitions;
- event-bus handoff from payment to vending;
- device-fault escalation;
- health-based sale blocking.

### Recovery tests

Recovery tests cover durable reboot evidence and manual-review classification:

- unresolved transaction and journal evidence survive a simulated reboot;
- partial payout remains a manual-review recovery case.

## Implemented test files

The current suite is split into:

- `tests/unit/test_change_manager.py`
- `tests/integration/test_cash_flows.py`
- `tests/integration/test_pickup_timeout.py`
- `tests/recovery/test_recovery_and_persistence.py`

The package also includes:

- `tests/_support.py`
- package markers for recursive stdlib `unittest` discovery.

## Covered edge cases

The requested edge cases are covered as follows.

### Exact change only

Covered by:

- unit assessment of unsafe worst-case payout;
- integration test that verifies the machine enters exact-change-only signaling when safe change is unavailable before acceptance starts.

### Insufficient change reserve

Covered by:

- unit reserve failure on insufficient accounting inventory.

### Payment cancelled

Covered by:

- integration test for `AcceptCash -> CancelPurchase -> IDLE`.

### Bill rejected

Covered by:

- integration test verifying rejected bills do not increment accepted amount and do not settle payment.

### Partial payout

Covered by:

- integration test verifying transition to `RECOVERY_PENDING` and ambiguous transaction state.

### Motor fault

Covered by:

- integration test verifying transition to `FAULT` and no successful vend history when motor control faults.

### Pickup timeout

Covered as executable integration tests:

- timeout closes the simulator delivery window and moves the transaction to recovery/manual review;
- `confirm_pickup` cancels the armed timeout;
- `window_controller.close_window` failure moves the machine to `FAULT`;
- restart while waiting for customer pickup preserves the need to resume timeout/recovery.

### Reboot mid-transaction

Covered by:

- recovery test that persists an unresolved transaction plus journal evidence, reopens SQLite, and verifies recovery evidence is still available after a simulated reboot.

### Service door open

Covered by:

- integration test verifying health monitor blocks sale start while service door is open.

### Critical temperature

Covered by:

- integration test verifying health monitor blocks sale start once chamber temperature crosses the critical threshold.

## Runtime and tooling choice

The tests are implemented with the Python standard library `unittest` stack instead of depending on `pytest` runtime availability.

This choice was made because:

- the current shell environment does not guarantee the project dev dependencies are installed;
- the core already uses `asyncio`, which is supported by `IsolatedAsyncioTestCase`;
- the goal of this phase is durable executable coverage, not framework-specific test syntax.

This keeps the suite runnable even in constrained environments.

## Verification performed

The following verification completed successfully:

- `py_compile` over the test tree;
- full recursive test execution through:
  - `python -m unittest discover -s tests -p "test_*.py" -v`

Observed result:

- pickup-timeout policy is now part of the passing integration suite.

## Assumptions

- The simulator harness remains the correct integration test surface for customer-flow scenarios.
- `unittest` is an acceptable production-baseline test runner even if `pytest` may be added later.
- Pickup-timeout policy belongs in application-core runtime logic, not in tests or UI workarounds.

## Fully implemented

- unit coverage for change safety logic
- integration coverage for cash flow, cancellation, device faults, and health-based blocking
- recovery coverage for reboot evidence and ambiguous payout assessment
- recursive stdlib test discovery package layout
- executable edge-case coverage for the requested scenarios including pickup timeout

## Scaffolded

- richer journal-replay integration directly through repository-backed bootstrap
- UI presenter and Qt widget runtime tests
- card-payment extension-path tests for future phases

## Requires hardware confirmation

- none for the simulator-backed tests themselves
- any future hardware-in-the-loop tests for real payout timing, validator cadence, or delivery-window sensors remain real-equipment work
