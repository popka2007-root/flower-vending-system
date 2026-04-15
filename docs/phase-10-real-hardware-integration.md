# Phase 10 - Real Hardware Integration

## Scope of this phase

This phase does not revise the accepted architecture.

It documents the exact boundaries between:

- what is already implemented and runnable in simulator form;
- what is structurally ready for real hardware binding;
- what still requires confirmed vendor documentation and bench validation.

The source of truth remains:

- accepted ADRs;
- the current `devices`, `infrastructure`, `app`, `simulators`, and `tests` code;
- the explicit rule that unconfirmed low-level protocol details must not be invented.

## Architecture alignment

The following architectural constraints remain unchanged:

- domain and application logic stay platform-neutral;
- real hardware enters only through device contracts and infrastructure adapters;
- recovery remains journal-first;
- ambiguous physical outcomes are not assumed successful;
- the known `COM3` fact belongs only to configuration.

This means Phase 10 is an enablement and validation phase, not an excuse to leak protocol behavior into payment or vending logic.

## Current readiness baseline

### Already implemented in software

- normalized hardware contracts for validator, payout, motor, cooling, window, watchdog, and sensors;
- real generic serial byte transport for the DBV-300-SD;
- DBV-300-SD domain-facing adapter boundary;
- application orchestration for payment, change reservation, vending, health monitoring, and recovery;
- SQLite persistence, transaction journal, and structured logging;
- deterministic simulators and layered tests for key business and failure scenarios.

### Structurally ready but not hardware-complete

- DBV-300-SD protocol binding points for `serial`, `mdb`, and `pulse`;
- extension-point configuration for payout, motor, cooling, window, and sensor devices;
- recovery and service workflows that can consume real device faults once available;
- kiosk and service UI paths that can surface real diagnostics.

### Not complete until hardware validation

- any vendor-specific wire protocol;
- any timing-sensitive handshake or retry policy;
- any physical acknowledgement semantics that decide whether change or product was truly dispensed.

## JCM DBV-300-SD: real integration requirements

## Existing integration boundary

The validator stack is already split into:

1. `DBV300Transport`
2. `DBV300Protocol`
3. `DBV300SDValidator`

The transport layer can already open a configured serial port, but the protocol layer intentionally remains deferred until confirmed documentation and bench behavior exist.

## What requires real JCM integration

The following implementation points must be completed against real JCM documentation and hardware:

- confirmed physical mode selection for the target machine: `serial`, `mdb`, or `pulse`;
- protocol framing and packet boundaries;
- initialization and wake-up sequence;
- polling cadence and state-transition semantics;
- acceptance enable or disable commands;
- denomination mapping from validator-native payloads into normalized money values;
- escrow support confirmation, including whether escrow exists on the deployed mode and how it is committed or returned;
- fault code mapping into normalized `validator_fault` states;
- power-up, reconnect, and disable-on-fault behavior.

## Parameters that must be confirmed from documentation

The following validator parameters cannot be finalized from assumptions:

- serial settings if `serial` is truly used on the deployed unit;
- MDB addressing and bus participation rules if `mdb` is used;
- pulse timing windows and pulse-to-denomination mapping if `pulse` is used;
- banknote table and enabled denominations for the deployed country profile;
- supported escrow semantics;
- startup state and whether the device accepts cash after power restoration by default;
- fault classes that require hard disable versus soft retry.

## Timings that must be confirmed on the bench

The following timings must be measured rather than guessed:

- boot-to-ready time after power restore;
- command response timeout;
- poll interval tolerance;
- reconnect timing after transport interruption;
- bill acceptance to `bill_stacked` timing window;
- escrow decision timing;
- recovery behavior after mid-insert power loss.

## What cannot be completed without the real validator

The following runtime actions remain blocked until the real protocol is implemented and validated:

- `start()` against a live DBV-300-SD device;
- enabling or disabling acceptance on the real unit;
- polling real validator events;
- stacking or returning escrowed banknotes;
- proving that normalized validator events match real device sequencing under load.

## Change dispenser: real integration requirements

## Existing integration boundary

The system already has:

- a `ChangeDispenser` contract;
- domain logic for reserve, exact-change-only policy, accounting state, and reconcile hooks;
- simulator behavior for successful payout, payout unavailable, and partial payout.

No real payout driver is implemented yet, by design.

## What requires real payout integration

The following must be implemented and confirmed against the actual payout hardware:

- transport and addressing model for the payout controller;
- command set for payout request, status read, reset, and possibly cassette inventory readback;
- denomination channel mapping;
- distinction between accounting inventory and physical inventory readback;
- confirmation model for full payout, partial payout, jam, empty channel, and payout unavailable;
- fault recovery and reconcile procedure after incomplete payout;
- service operations for refill, cash removal, and manual correction.

## Parameters that must be confirmed from documentation

- supported denominations and cassette or hopper layout;
- minimum and maximum payout per request;
- whether the device can report exact dispensed counts;
- low-level fault and warning taxonomy;
- inventory counters and whether they are trusted accounting values or physical estimates;
- reset and clear-fault semantics;
- safe operator procedures for refill and audit.

## Timings that must be confirmed on the bench

- payout start latency;
- payout completion timeout by denomination mix;
- status polling interval;
- post-fault settle time before retry or lockout;
- refill and reconcile timing for service operations.

## What cannot be completed without the real payout device

- hardware-validated `exact change only` transitions based on real physical inventory;
- trusted partial-payout reconciliation;
- durable operator playbooks for mismatch between accounting and physical cash;
- real payout confirmation semantics for recovery after power loss.

## Other hardware requiring real integration

## Motor controller and position sensing

Need confirmed transport, homing behavior, motion commands, timeout values, position acknowledgement, and jam or stall fault semantics.

Without hardware confirmation, the system cannot prove:

- that a vend command moved to the expected slot;
- that the product actually left the slot;
- that double-dispense prevention is backed by real end-stop and sensor behavior.

## Delivery window controller

Need confirmed open, close, state readback, timeout, and obstruction behavior.

Without hardware confirmation, the system cannot finalize:

- reliable transition into `WAITING_FOR_CUSTOMER_PICKUP`;
- pickup timeout enforcement based on real door or window signals;
- safe close behavior after obstruction or customer interference.

## Cooling controller and temperature sensor

Need confirmed relay or controller interface, sensor accuracy, alarm thresholds, reading cadence, and failure semantics.

Without hardware confirmation, the system cannot finalize:

- real warning versus critical temperature thresholds;
- cooling hysteresis and anti-short-cycle protection;
- service diagnostics for sensor drift or compressor faults.

## Door sensor, inventory sensor, and position sensor

Need confirmed signal polarity, debounce behavior, read latency, and failure modes.

Without hardware confirmation, the system cannot finalize:

- confident sale blocking on service door open;
- trusted slot-empty versus product-present decisions;
- recovery rules when a sensor disagrees with the accounting state.

## Watchdog and platform service integration

Need confirmed deployment behavior for:

- Windows service watchdog or service recovery policy;
- Linux systemd or equivalent watchdog integration;
- kiosk mode lock-down, auto-login, and autostart;
- process crash restart policy and health heartbeat routing.

These are platform operations, not domain logic, but they still need target-environment validation.

## Commands and states that depend on real hardware confirmation

The following workflow steps already exist architecturally but cannot be considered production-complete without real device confirmation:

- `AcceptCash`
- `CompletePayment`
- `DispenseChange`
- `DispenseProduct`
- `OpenDeliveryWindow`
- `ConfirmPickup`
- `RecoverInterruptedTransaction` for ambiguous physical outcomes
- any self-test that requires a real command or sensor response

The following FSM states are especially dependent on hardware semantics:

- `WAITING_FOR_PAYMENT`
- `ACCEPTING_CASH`
- `DISPENSING_CHANGE`
- `DISPENSING_PRODUCT`
- `OPENING_DELIVERY_WINDOW`
- `WAITING_FOR_CUSTOMER_PICKUP`
- `CLOSING_DELIVERY_WINDOW`
- `RECOVERY_PENDING`
- `FAULT`

## What is already ready for simulation

The following areas are ready for headless simulation and remain valuable before hardware arrives:

- purchase start, precondition validation, and safety blocking;
- change reservation and exact-change-only policy;
- accepted, rejected, and faulted bill flows using normalized validator events;
- partial payout, payout unavailable, and motor fault scenarios;
- journal-backed recovery evidence and manual-review routing;
- UI presenter logic for sales flow, exact-change-only messaging, diagnostics, and service mode.

Simulation already proves architecture and failure handling, but it does not prove vendor timing, transport reliability, or physical acknowledgement semantics.

## Tests that require real equipment

The following tests should be executed on the bench with the target machine wiring:

- validator startup and disable sequence after process start and after crash restart;
- denomination acceptance matrix for all configured banknotes;
- escrow commit and return behavior if escrow is supported in the chosen mode;
- payout accuracy by denomination mix, including partial payout and empty-channel behavior;
- sell-flow with inserted cash, payout, vend, window open, pickup, and window close;
- power loss injected during `ACCEPTING_CASH`, `DISPENSING_CHANGE`, `DISPENSING_PRODUCT`, and `WAITING_FOR_CUSTOMER_PICKUP`;
- service-door-open blocking under active and idle conditions;
- critical-temperature blocking and recovery after temperature normalization;
- reconcile workflow after deliberate cash-inventory mismatch;
- watchdog restart and post-restart recovery path.

## Migration risks from the legacy Windows implementation

## Technical risks

- legacy code may have implicit assumptions about Windows serial APIs, thread timing, or COM-port behavior that do not hold on Linux;
- legacy process lifecycle may rely on Windows service restart behavior rather than explicit watchdog integration;
- legacy drivers may expose synchronous blocking semantics that differ from the new async orchestration model;
- historical device fault handling may have been hidden inside UI or imperative scripts rather than normalized device adapters.

## Business and safety risks

- the old separate `Change` button behavior must not reappear and bypass the transaction-safe cash flow;
- legacy recovery may have trusted volatile state instead of journal evidence, which is unsafe for ambiguous payout or vend cases;
- cash inventory accounting in legacy code may not distinguish accounting state from physical state clearly enough for reconcile;
- old vend sequencing may have tolerated issuing product before payout confirmation, which is explicitly forbidden now.

## Deployment and operational risks

- existing field configuration may encode port names, timeout values, or denomination tables outside the new YAML/config audit path;
- operator procedures from the legacy system may not match the new service-mode and reconcile workflow;
- Windows kiosk shell, touchscreen drivers, and auto-login setup may differ from the future Linux deployment path.

## Recommended bring-up sequence

The lowest-risk enablement sequence is:

1. validate power, wiring, and OS-level visibility of each device;
2. confirm DBV-300-SD physical mode and documentation set;
3. implement and bench-verify the real validator protocol adapter;
4. integrate and bench-verify the payout controller with reconcile procedure;
5. integrate motor, position sensing, and delivery window controls;
6. integrate cooling and safety sensors;
7. run end-to-end sale, fault, and power-loss recovery drills;
8. only then enable kiosk deployment and field pilot rollout.

This preserves the accepted architectural boundaries and reduces the chance of mixing hardware bring-up hacks into business logic.

## Assumptions

- The deployed product will still use the existing contract boundaries rather than replacing the core with vendor SDK logic.
- At least minimal hardware documentation or bench packet captures will be available for the DBV-300-SD and payout node.
- The target machine can expose enough signals to distinguish hard faults from ambiguous outcomes.
- Manual-review service workflow remains acceptable for ambiguous physical outcomes after restart or mid-operation power loss.

## Fully implemented

- hardware abstraction boundaries for all major device categories
- generic serial transport for the DBV-300-SD
- protocol and driver extension points
- simulator-first validation of the application core
- journal-first recovery baseline for ambiguous transaction handling

## Scaffolded

- real validator protocol implementation
- real payout driver
- real actuator and sensor drivers
- platform-specific watchdog and kiosk deployment adapters
- hardware-in-the-loop validation procedures and operator playbooks

## Requires hardware confirmation

- real DBV-300-SD transport mode, protocol frames, state model, and timings
- real payout transport, command set, dispense confirmation, and reconcile semantics
- real motor, window, cooling, and sensor command and feedback behavior
- real watchdog and kiosk deployment semantics on the target OS
- any production timeout, retry, debounce, and fault-threshold values tied to physical devices
