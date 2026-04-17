# Phase 6 - Simulators and Mocks

## Scope of this phase

This phase implements deterministic mock devices and headless scenario drivers so that the platform-neutral application core can be exercised without real hardware.

The main goals are:

- provide mock implementations for every required device contract;
- support deterministic fault injection;
- drive the existing `ApplicationCore` through real commands and validator events;
- emulate the required failure scenarios from the project brief;
- keep clear extension points between simulator behavior and real device integration.

## Implemented mock devices

The simulator device layer now includes:

- `MockBillValidator`
- `MockChangeDispenser`
- `MockMotorController`
- `MockCoolingController`
- `MockWindowController`
- `MockTemperatureSensor`
- `MockDoorSensor`
- `MockInventorySensor`
- `MockPositionSensor`
- `MockWatchdogAdapter`

All mock devices inherit common lifecycle and health behavior from `MockManagedDevice`. This keeps start/stop semantics, health snapshots, and fault activation consistent across the simulator layer.

## Deterministic fault injection

Fault injection is modeled explicitly through:

- `SimulatorFaultCode`
- `FaultInjectionPlan`
- `FaultInjector`

Each simulator device can consume a configured fault on a specific interaction. This is intentionally deterministic rather than probabilistic. A test, smoke scenario, or operator diagnostic should be able to request a known failure and get the same outcome every time.

Implemented fault codes in this phase:

- `validator_unavailable`
- `bill_jam`
- `bill_rejected`
- `payout_unavailable`
- `partial_payout`
- `motor_fault`
- `window_fault`
- `watchdog_fault`

## Simulation harness

`SimulationHarness` is the headless entrypoint for deterministic scenarios.

It builds:

- an `InventoryService` with one configured product and slot;
- an in-memory `MoneyInventory`;
- the mock devices;
- a real `ApplicationCore` via `build_application_core(...)`;
- an `EventRecorder` subscribed to the event bus.

The harness deliberately does not bypass the application layer. It starts purchases through `CommandBus`, feeds normalized validator events into `PaymentCoordinator`, and collects machine outcomes from the real FSM and transaction coordinator.

This is important because the simulator should validate the same orchestration seams that production code will use.

## Scenario suite

The deterministic scenario package now exposes:

- `happy_path`
- `validator_unavailable`
- `bill_jam`
- `partial_payout`
- `motor_fault`
- `door_open`
- `critical_temperature`
- `inventory_mismatch`

`run_default_scenario_suite()` executes the registry sequentially and returns typed `ScenarioResult` objects containing:

- scenario name;
- success flag;
- final machine state;
- final transaction status when present;
- observed event types;
- active sale blockers;
- error strings;
- scenario notes.

## Emulated failure behavior

### Validator unavailable

The validator can fail before entering bill acceptance. The payment coordinator now transitions the machine into `FAULT`, marks the transaction as faulted, and blocks sales through the validator fault reason.

### Bill jam

The mock validator emits a deterministic `validator_fault` event after a bill is detected. The application core escalates that to a transaction fault and machine `FAULT`.

### Partial payout

The mock change dispenser can return a partial payout result. The transaction becomes ambiguous, vend remains blocked, and the FSM transitions into `RECOVERY_PENDING`.

### Motor fault

The vend motor can fault after payment was already confirmed. The transaction is marked faulted and the machine transitions into `FAULT`.

### Door open

The health monitor blocks new sales when the service door sensor reports open. This is enforced before a transaction can start.

### Critical temperature

The health monitor blocks new sales when chamber temperature crosses the configured critical threshold.

### Inventory mismatch

The inventory sensor can contradict accounting inventory before payment starts. The vending controller rejects the purchase before a transaction is created.

## Important bug found and corrected during this phase

While executing the deterministic partial payout scenario, the simulator exposed a real orchestration bug in `ChangeManager.finalize_reserve(...)`.

The original implementation attempted to compute the final payout plan while the provisional reserve was still held. That could make a valid exact payout plan appear impossible.

The implementation was corrected so that the provisional reserve is released before computing and applying the final exact reserve. This is exactly the sort of production-risk issue the simulator layer is intended to surface early.

## Verification performed

Verification completed in two steps:

- `py_compile` over the full `src/` tree passed;
- the default simulator suite executed successfully for all deterministic scenarios.

Observed final outcomes from the suite:

- `happy_path` -> `IDLE`
- `validator_unavailable` -> `FAULT`
- `bill_jam` -> `FAULT`
- `partial_payout` -> `RECOVERY_PENDING`
- `motor_fault` -> `FAULT`
- `door_open` -> sale blocked
- `critical_temperature` -> sale blocked
- `inventory_mismatch` -> purchase rejected before payment

## Assumptions

- One active customer flow at a time is sufficient for simulator execution.
- Deterministic, scripted faults are more valuable than randomized fault generation at this stage.
- Mock device timing can remain immediate until later phases introduce richer timeout and retry testing.
- Event ordering in the simulator should mimic normalized domain-facing behavior, not undocumented low-level vendor timing.

## Fully implemented

- Mock implementations for the required device contracts
- Deterministic fault injection primitives
- Headless `SimulationHarness`
- Event recording for simulator runs
- Scenario registry and default scenario suite
- Emulation of the required failure cases for Phase 6

## Scaffolded

- Richer timing simulation and long-running polling behavior
- Multi-step recovery playbooks after ambiguous payout or vend outcomes
- Watchdog failure scenarios beyond adapter-level fault injection
- Additional simulator scenarios for bill rejection, pickup timeout, and reboot mid-transaction

## Requires hardware confirmation

- Real validator latency and event cadence on DBV-300-SD
- Real payout timing and partial payout semantics on the physical change subsystem
- Real vend motor completion confirmation and failure signatures
- Real delivery window timing, sensors, and interlocks
- Real interaction between temperature excursions, cooling control, and operator policy
