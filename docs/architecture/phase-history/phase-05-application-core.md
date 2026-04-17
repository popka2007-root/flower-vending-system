# Phase 5 - Application Core

## Scope of this phase

This phase implements the application orchestration layer on top of the domain model and device interfaces:

- command bus;
- event bus;
- machine FSM engine;
- transaction coordinator;
- payment coordinator;
- vending controller;
- change manager integration;
- recovery manager;
- health monitor;
- bootstrap wiring for a headless application core.

The focus here is orchestration. Persistence, durable transaction journal, and repository-backed recovery are intentionally deferred to Phase 7.

## Implemented application core

### Command bus

`CommandBus` dispatches strongly typed command objects to async handlers. This gives the UI, service mode, or tests one clean entrypoint into the application layer.

### Event bus

`EventBus` publishes domain events to async subscribers. It is used for:

- transaction and payment projections;
- event-driven handoff from payment completion to vending;
- machine health and recovery notifications.

### FSM engine

`StateMachineEngine` enforces allowed machine-state transitions using the explicit state graph from Phase 3. Orchestrators update machine state through the FSM rather than mutating status flags ad hoc.

### Transaction coordinator

`TransactionCoordinator` is the current in-memory registry for active and recent transactions. It owns:

- transaction creation;
- active transaction tracking;
- unresolved transaction enumeration.

This is intentionally in-memory for now; Phase 7 will replace or back this with repositories and journal replay.

### Payment coordinator

`PaymentCoordinator` orchestrates the cash session:

- preflight change assessment through `ChangeManager`;
- pre-session reserve creation;
- validator enable or disable;
- processing `bill_stacked` events;
- payment confirmation;
- final reserve reconciliation;
- change dispense request and settlement;
- emission of `vend_authorized` only after payment and required change payout are resolved.

### Vending controller

`VendingController` is the top-level sale orchestrator:

- validates product and slot selection through `InventoryService`;
- creates the transaction and advances the FSM into `WAITING_FOR_PAYMENT`;
- starts cash acceptance on `AcceptCash`;
- subscribes to `vend_authorized`;
- commands the motor and delivery window;
- completes pickup and returns the machine to `IDLE`.

### Recovery manager

`RecoveryManager` provides the application-level recovery decision point for interrupted transactions. At this stage it uses transaction aggregate state, not yet journal replay. It already distinguishes:

- safe cancellation before confirmed payment;
- manual review for ambiguous or faulted transactions;
- operator-required review for confirmed-payment but unresolved side effects.

### Health monitor

`HealthMonitor` polls normalized device health from registered adapters and maps it into machine sale blockers:

- device fault;
- service door open;
- critical temperature.

It updates `MachineStatusService` and emits machine-level events.

### Bootstrap wiring

`build_application_core(...)` assembles:

- command bus;
- event bus;
- FSM;
- transaction coordinator;
- payment coordinator;
- vending controller;
- recovery manager;
- health monitor.

It also registers:

- command handlers for `StartPurchase`, `AcceptCash`, `CancelPurchase`, and `ConfirmPickup`;
- the event subscription from `vend_authorized` to `VendingController.handle_vend_authorized`.

## Transaction lifecycle example

### Headless command flow

1. `StartPurchase`
   - inventory is validated;
   - transaction is created;
   - FSM advances to `WAITING_FOR_PAYMENT`.
2. `AcceptCash`
   - `PaymentCoordinator` checks safe change;
   - reserves change capacity;
   - enables the validator;
   - FSM advances to `ACCEPTING_CASH`.
3. `bill_stacked`
   - accepted amount is updated;
   - once `accepted_amount >= price`, payment is confirmed.
4. `Complete payment` inside `PaymentCoordinator`
   - validator is disabled;
   - exact payout reserve is finalized;
   - change is dispensed if needed;
   - `vend_authorized` event is published.
5. `vend_authorized`
   - `VendingController` commands the vend motor;
   - inventory is decremented only after successful vend command path;
   - delivery window opens;
   - FSM enters `WAITING_FOR_CUSTOMER_PICKUP`.
6. `ConfirmPickup`
   - delivery window closes;
   - transaction is completed;
   - active transaction clears;
   - FSM returns to `IDLE`.

## Current recovery example

### Reboot while waiting for payment

- transaction exists;
- payment is not confirmed;
- recovery manager can classify it as `cancel_safe`.

### Reboot after confirmed payment but before vend outcome is known

- transaction is confirmed but side effects are unresolved;
- recovery manager classifies it as operator-required review for now;
- Phase 7 will move this to journal-based replay instead of aggregate-only assessment.

## Boundaries at the end of this phase

### What is now real application code

- command and event dispatching;
- explicit FSM transition enforcement;
- in-memory transaction orchestration;
- change preflight and payout orchestration;
- vend handoff through `vend_authorized`;
- health-based sale blocking;
- bootstrap composition root.

### What is still intentionally deferred

- SQLite-backed repositories;
- transaction journal writes and replay;
- durable recovery logic based on journal evidence;
- simulator devices and deterministic fault injection;
- UI integration layer;
- real hardware protocol completion for DBV-300-SD and payout devices.

## Phase outcome classification

### Fully implemented

- command bus
- event bus
- FSM engine
- transaction coordinator
- payment coordinator
- vending controller
- recovery manager skeleton with concrete decision logic
- health monitor
- bootstrap composition root
- example command-driven transaction lifecycle

### Scaffolded

- in-memory transaction registry instead of persistence-backed coordinator
- aggregate-state-based recovery pending journal replay phase
- change policy limited to the currently configured accepted bill denominations
- event-driven vend handoff without telemetry or journal sinks attached yet

### Requires hardware confirmation

- real validator event timing and ordering under physical load
- real payout device behavior under partial payout or jam conditions
- physical confirmation semantics for vend completion and delivery window operation

## Assumptions

- Only one active customer transaction is allowed at a time.
- Event-driven handoff from payment to vend is acceptable and clearer than a single monolithic coordinator.
- Before Phase 7, in-memory coordination is sufficient to prove orchestration structure even though it is not yet power-loss durable.
- Device adapters already provide normalized contracts, so the application layer can remain protocol-agnostic.
