# Phase 3 - Domain Model and FSM

## Scope of this phase

This phase defines the platform-neutral domain model, command/event semantics, exception hierarchy, and the authoritative finite state machine that governs customer sales, service mode, faults, and recovery. It deliberately stops short of concrete device protocol implementation.

## Domain model overview

The model is split between:

- domain primitives and invariants;
- transaction-centric aggregates;
- machine-level operational state;
- application-facing commands and domain events.

The key design choice is that the FSM controls workflow progression, while aggregates enforce invariants that remain true even if application logic or device adapters misbehave.

## Value objects

### `Amount`

- represents money in minor units;
- always paired with a `Currency`;
- immutable;
- supports arithmetic and comparison with currency checks;
- prohibits mixed-currency operations.

### `Currency`

- ISO-like currency identity, default deployment assumption is a single configured currency;
- used to validate all money-bearing entities and events.

### `Denomination`

- represents one payout or acceptance denomination;
- includes face value and kind such as bill or coin;
- used by both accounting and change calculation services;
- does not encode device-specific protocol values.

### `Temperature`

- immutable temperature measurement in Celsius;
- supports threshold comparisons and normalization;
- carries only measurement semantics, not policy.

### `DeviceState`

- normalized device health state used across adapters and domain projections;
- expected states: `UNKNOWN`, `INITIALIZING`, `READY`, `DISABLED`, `DEGRADED`, `FAULT`, `RECOVERY_PENDING`, `OUT_OF_SERVICE`.

### `SlotId`

- stable identity for a physical inventory slot or carousel position.

### `ProductId`

- stable identity for a sellable product or bouquet SKU.

### `TransactionId`

- globally unique identifier for one purchase lifecycle.

### `CorrelationId`

- cross-cutting identifier used to join machine actions, device events, and logs across one workflow.

## Entities

### `Product`

- `product_id`
- `name`
- `display_name`
- `price: Amount`
- `category`
- `is_bouquet`
- `enabled`
- `temperature_profile`
- `metadata`

Responsibilities:

- carries catalog data relevant to the sale;
- does not own stock counts;
- does not know about device state or payment flow.

### `Slot`

- `slot_id`
- `product_id`
- `capacity`
- `quantity`
- `sensor_state`
- `is_enabled`
- `last_reconciled_at`

Responsibilities:

- owns stock presence for a physical slot;
- tracks whether the slot may be sold from;
- exposes sellability based on accounting plus sensor confidence.

### `MoneyInventory`

- `currency`
- `accounting_counts_by_denomination`
- `reserved_counts_by_denomination`
- `physical_state_confidence`
- `exact_change_only`
- `last_reconciled_at`
- `drift_detected`

Responsibilities:

- owns accounting view of change inventory;
- supports reservation and release;
- separates logical counts from physical certainty;
- can force exact-change-only mode or sale blocking.

### `Transaction`

- `transaction_id`
- `correlation_id`
- `product_id`
- `slot_id`
- `price`
- `status`
- `accepted_amount`
- `change_due`
- `payment_status`
- `payout_status`
- `dispense_status`
- `delivery_status`
- `recovery_status`
- `created_at`
- `updated_at`

Responsibilities:

- tracks end-to-end purchase state;
- ensures product vend cannot be authorized before durable payment confirmation;
- ensures completion cannot occur while payout or vend status is ambiguous.

### `PaymentSession`

- `transaction_id`
- `status`
- `accepted_amount`
- `accepted_bills`
- `validator_enabled`
- `started_at`
- `expires_at`
- `cancel_requested`

Responsibilities:

- models one cash collection session;
- tracks validated/stacked cash only;
- keeps validator-specific events translated into domain-neutral session semantics.

### `ChangeReserve`

- `transaction_id`
- `reserved_counts_by_denomination`
- `reserved_total`
- `status`
- `created_at`
- `released_at`

Responsibilities:

- holds reserved change inventory for one active payment session;
- prevents overcommitting payout capacity across concurrent or interrupted flows;
- supports `ACTIVE`, `RELEASED`, `CONSUMED`, `AMBIGUOUS`.

### `MachineStatus`

- `machine_state`
- `service_mode`
- `exact_change_only`
- `sale_blockers`
- `warnings`
- `active_transaction_id`
- `allow_cash_sales`
- `allow_vending`

Responsibilities:

- projects current machine availability;
- centralizes whether sales can start;
- exposes degraded but safe operating modes.

### `DeviceHealthSnapshot`

- `validator_state`
- `change_dispenser_state`
- `motor_state`
- `cooling_state`
- `window_state`
- `temperature_sensor_state`
- `door_sensor_state`
- `inventory_sensor_state`
- `watchdog_state`
- `last_heartbeat_at`
- `faults`

Responsibilities:

- normalized view of device health across adapters;
- powers sale-block decisions and operator diagnostics;
- does not contain protocol-specific payloads.

## Aggregates

### `PurchaseTransactionAggregate`

Aggregate root: `Transaction`

Contains or references:

- `PaymentSession`
- `ChangeReserve`
- vend and delivery outcome markers

Invariants:

- a transaction may have at most one active payment session;
- change reserve must exist before accepting cash unless zero-change policy explicitly applies;
- vend authorization requires payment confirmed and payout resolved;
- completion requires non-ambiguous payout and non-ambiguous vend outcome;
- cancellation after payout or vend intent is governed by recovery or compensation policy, not by blind rollback.

### `CashInventoryAggregate`

Aggregate root: `MoneyInventory`

Invariants:

- reserved counts may not exceed accounting counts;
- payout commitment cannot exceed unreserved inventory;
- `exact_change_only` may be enabled automatically by policy;
- `drift_detected` blocks risky payouts until reconciliation policy allows them.

### `MachineRuntimeAggregate`

Aggregate root: `MachineStatus`

References:

- `DeviceHealthSnapshot`
- current operational mode
- blocking conditions

Invariants:

- sales cannot start if a critical blocker is active;
- service mode and customer mode are mutually exclusive;
- unresolved critical recovery keeps the machine out of normal sale mode.

## Domain services

### `SaleEligibilityPolicy`

Checks whether a sale may start based on:

- door state;
- temperature state;
- device health;
- inventory confidence;
- exact-change or safe-payout policy;
- unresolved recovery blockers.

### `ChangeCalculationService`

- computes feasible payout combinations from available denominations;
- prefers policy-defined payout strategy;
- returns exact combination or failure;
- does not talk to hardware.

### `ChangeReservationService`

- reserves denominations before enabling payment;
- releases, consumes, or marks ambiguous reserve state based on transaction outcome.

### `CashSettlementPolicy`

- decides when payment is confirmed;
- determines whether overpay can be accepted safely;
- blocks further cash acceptance when payout safety is lost.

### `InventoryAvailabilityPolicy`

- determines whether a slot is sellable from accounting plus sensor confidence;
- detects unsafe mismatch between inventory record and sensor state.

### `CoolingSafetyPolicy`

- maps measured temperature into `NORMAL`, `WARNING`, or `CRITICAL`;
- tells the machine whether sales must be blocked.

### `RecoveryDecisionService`

- evaluates unresolved journal facts;
- distinguishes retriable, compensatable, ambiguous, and operator-only cases;
- never invents physical completion without evidence.

## Commands

### Customer flow commands

- `StartPurchase`
- `AcceptCash`
- `CancelPurchase`
- `CompletePayment`
- `DispenseChange`
- `DispenseProduct`
- `OpenDeliveryWindow`
- `ConfirmPickup`

### Recovery and service commands

- `RecoverInterruptedTransaction`
- `EnterServiceMode`
- `ReconcileCashInventory`

### Command handler mapping

| Command | Primary handler | Typical emitted events |
| --- | --- | --- |
| `StartPurchase` | `StartPurchaseHandler` | `purchase_started`, `availability_check_requested`, `change_check_requested` |
| `AcceptCash` | `AcceptCashHandler` | `cash_session_started`, `bill_validated`, `bill_stacked`, `cash_amount_updated` |
| `CancelPurchase` | `CancelPurchaseHandler` | `purchase_cancel_requested`, `payment_cancelled`, `change_reserve_released` |
| `CompletePayment` | `CompletePaymentHandler` | `payment_confirmed`, `change_dispense_requested` or `vend_authorized` |
| `DispenseChange` | `DispenseChangeHandler` | `change_dispense_requested`, `change_dispensed` or `change_dispense_failed` |
| `DispenseProduct` | `DispenseProductHandler` | `product_dispense_requested`, `product_dispensed` or `product_dispense_failed` |
| `OpenDeliveryWindow` | `OpenDeliveryWindowHandler` | `delivery_window_open_requested`, `delivery_window_opened` |
| `ConfirmPickup` | `ConfirmPickupHandler` | `pickup_confirmed`, `transaction_completed` |
| `RecoverInterruptedTransaction` | `RecoverInterruptedTransactionHandler` | `recovery_started`, `recovery_pending`, `transaction_marked_ambiguous`, `recovery_completed` |
| `EnterServiceMode` | `EnterServiceModeHandler` | `service_mode_entered`, `machine_sale_blocked` |
| `ReconcileCashInventory` | `ReconcileCashInventoryHandler` | `cash_inventory_reconciled`, `exact_change_policy_recomputed` |

## Events

### Purchase and transaction lifecycle

- `purchase_started`
- `product_selection_confirmed`
- `availability_check_requested`
- `availability_confirmed`
- `availability_failed`
- `change_check_requested`
- `change_reserve_created`
- `change_reserve_failed`
- `cash_session_started`
- `cash_amount_updated`
- `payment_confirmed`
- `payment_cancel_requested`
- `payment_cancelled`
- `transaction_completed`
- `transaction_cancelled`
- `transaction_faulted`
- `transaction_marked_ambiguous`

### Bill validator events

- `bill_detected`
- `bill_validated`
- `bill_rejected`
- `escrow_available`
- `bill_stacked`
- `bill_returned`
- `validator_fault`
- `validator_disabled`

### Change payout events

- `change_dispense_requested`
- `change_dispensed`
- `change_dispense_partially_completed`
- `change_dispense_failed`
- `change_inventory_released`
- `cash_inventory_reconciled`

### Vending and pickup events

- `product_dispense_requested`
- `product_dispensed`
- `product_delivery_failed`
- `delivery_window_open_requested`
- `delivery_window_opened`
- `pickup_confirmed`
- `pickup_timeout_elapsed`
- `pickup_timeout_window_closed`
- `pickup_timeout_window_close_failed`
- `delivery_window_close_requested`
- `delivery_window_closed`

### Machine and recovery events

- `machine_faulted`
- `machine_recovered`
- `service_mode_entered`
- `service_mode_exited`
- `exact_change_only_enabled`
- `exact_change_only_disabled`
- `critical_temperature_detected`
- `service_door_opened`
- `recovery_started`
- `recovery_pending`
- `recovery_completed`
- `manual_review_required`

## Event handler responsibilities

- payment projection handlers update accepted amount and remaining balance;
- health projection handlers update `MachineStatus` and sale blockers;
- journal handlers persist durable intent and result entries;
- recovery handlers build unresolved action graphs from journal history;
- UI presenters react only to application-facing projections, never raw device frames.

## Exception hierarchy

### Base exceptions

- `FlowerVendingError`
- `DomainValidationError`
- `InvariantViolationError`
- `IdempotencyViolationError`
- `ConcurrencyConflictError`

### Sale and inventory exceptions

- `SaleBlockedError`
- `ProductUnavailableError`
- `SlotUnavailableError`
- `InventoryMismatchError`

### Payment and change exceptions

- `PaymentError`
- `PaymentSessionUnavailableError`
- `PaymentCancelledError`
- `BillRejectedError`
- `ValidatorUnavailableError`
- `ChangeUnavailableError`
- `ExactChangeOnlyViolationError`
- `PartialPayoutError`
- `PayoutAmbiguousError`

### Device and safety exceptions

- `DeviceHealthError`
- `ServiceDoorOpenError`
- `CriticalTemperatureError`
- `MotorFaultError`
- `DeliveryWindowFaultError`
- `WatchdogFaultError`

### Recovery exceptions

- `RecoveryError`
- `RecoveryPendingError`
- `AmbiguousTransactionStateError`
- `JournalConsistencyError`
- `ManualInterventionRequiredError`

## FSM overview

The FSM is authoritative for workflow progression, but not for truth of physical side effects. Physical truth is confirmed through device events plus durable journal entries. If the FSM and journal disagree after restart, the journal wins and the FSM is rebuilt.

### Event classes used by the FSM

- operator or UI events: product selected, cancel, service mode requested, pickup confirmed;
- device events: bill stacked, payout complete, motor fault, door opened, temperature critical;
- timer events: payment timeout, pickup timeout, recovery timeout;
- recovery events: journal replay complete, ambiguity detected, operator resolution complete.

## FSM states

### `BOOT`

Input events:

- `startup_initiated`
- `bootstrap_failed`

Allowed transitions:

- `BOOT -> SELF_TEST`
- `BOOT -> FAULT`

Guards:

- configuration loaded;
- bootstrap dependencies available.

Side effects:

- initialize logging;
- load configuration;
- create infrastructure adapters;
- write startup journal marker.

Idempotency requirements:

- startup initialization may be retried safely after crash;
- duplicate bootstrap marker entries must be deduplicated by correlation and stage.

Rollback and recovery behavior:

- if boot fails before self-test, restart from `BOOT`;
- no customer transaction may start here.

Prohibited actions:

- accept payment;
- move vend motor;
- open delivery window.

Power-loss recovery:

- restart in `BOOT` and continue through self-test;
- unresolved transaction handling is deferred to `RECOVERY_PENDING` decision after self-test.

### `SELF_TEST`

Input events:

- `self_test_passed`
- `self_test_failed`
- `recovery_needed_detected`

Allowed transitions:

- `SELF_TEST -> IDLE`
- `SELF_TEST -> RECOVERY_PENDING`
- `SELF_TEST -> OUT_OF_SERVICE`
- `SELF_TEST -> FAULT`

Guards:

- mandatory devices initialized enough for health assessment;
- journal store reachable.

Side effects:

- poll device health;
- evaluate cooling safety;
- verify unresolved transaction presence;
- compute exact-change policy.

Idempotency requirements:

- repeated self-test may run without changing accounting state;
- health probes must not command actuators unexpectedly.

Rollback and recovery behavior:

- failed self-test does not roll back device state, only blocks sale mode.

Prohibited actions:

- customer purchase flow;
- payout;
- vend.

Power-loss recovery:

- resume with fresh self-test; never trust previous pass result blindly.

### `IDLE`

Input events:

- `product_selection_confirmed`
- `service_mode_entered`
- `machine_faulted`
- `critical_temperature_detected`
- `service_door_opened`

Allowed transitions:

- `IDLE -> PRODUCT_SELECTED`
- `IDLE -> SERVICE_MODE`
- `IDLE -> OUT_OF_SERVICE`
- `IDLE -> FAULT`

Guards:

- no active critical blockers;
- no unresolved transaction locking customer mode.

Side effects:

- expose catalog;
- publish current machine availability and exact-change banners.

Idempotency requirements:

- repeated idle-entry projection refresh is safe;
- duplicate product select for same transaction must not create multiple transactions.

Rollback and recovery behavior:

- no transactional rollback required;
- if a blocker appears, sale availability flips immediately.

Prohibited actions:

- accepting cash without a selected transaction;
- moving vend hardware.

Power-loss recovery:

- if no unresolved transaction exists, restore to `IDLE`;
- otherwise transition to `RECOVERY_PENDING`.

### `PRODUCT_SELECTED`

Input events:

- `purchase_started`
- `selection_cancelled`
- `machine_faulted`

Allowed transitions:

- `PRODUCT_SELECTED -> CHECKING_AVAILABILITY`
- `PRODUCT_SELECTED -> CANCELLED`
- `PRODUCT_SELECTED -> FAULT`

Guards:

- selected product exists and is enabled.

Side effects:

- create transaction shell;
- persist product, slot intent, price, correlation id;
- display product summary.

Idempotency requirements:

- repeating selection for same correlation updates view only, not duplicate transaction shell creation.

Rollback and recovery behavior:

- if cancelled here, transaction may be safely cancelled without payout or vend side effects.

Prohibited actions:

- cash acceptance;
- payout;
- vend.

Power-loss recovery:

- journal replay may reconstruct pending selection and restart availability checks or cancel stale shells by policy.

### `CHECKING_AVAILABILITY`

Input events:

- `availability_confirmed`
- `availability_failed`
- `service_door_opened`
- `critical_temperature_detected`

Allowed transitions:

- `CHECKING_AVAILABILITY -> CHECKING_CHANGE`
- `CHECKING_AVAILABILITY -> CANCELLED`
- `CHECKING_AVAILABILITY -> OUT_OF_SERVICE`
- `CHECKING_AVAILABILITY -> FAULT`

Guards:

- slot accounting says stock available;
- sensor confidence above policy threshold;
- machine still safe for sale.

Side effects:

- lock candidate slot logically for the transaction if policy requires;
- record availability result in journal.

Idempotency requirements:

- repeated availability checks must not decrement stock;
- slot lock acquisition must be idempotent by transaction id.

Rollback and recovery behavior:

- release slot lock if availability fails or transaction cancels.

Prohibited actions:

- enabling validator;
- vend command.

Power-loss recovery:

- replay may require re-check of inventory confidence before continuing.

### `CHECKING_CHANGE`

Input events:

- `change_reserve_created`
- `change_reserve_failed`
- `exact_change_only_enabled`
- `selection_cancelled`

Allowed transitions:

- `CHECKING_CHANGE -> WAITING_FOR_PAYMENT`
- `CHECKING_CHANGE -> CANCELLED`
- `CHECKING_CHANGE -> OUT_OF_SERVICE`

Guards:

- safe payout available for expected transaction range;
- or policy allows zero-change-only exact cash flow.

Side effects:

- simulate payout feasibility;
- reserve denominations if needed;
- record exact-change-only banner or cash block decision.

Idempotency requirements:

- repeated reservation request for same transaction returns the same active reserve or a conflict error;
- failed reservation must not leak partial holds.

Rollback and recovery behavior:

- release reservation on cancellation or sale block;
- if reservation state becomes ambiguous, enter recovery or block cash sales.

Prohibited actions:

- accepting cash before reservation or exact-cash policy decision;
- vend authorization.

Power-loss recovery:

- replay must rebuild reserve state from journal and money inventory;
- ambiguous reserve state forces `RECOVERY_PENDING` or exact-change-only block by policy.

### `WAITING_FOR_PAYMENT`

Input events:

- `cash_session_started`
- `selection_cancelled`
- `validator_fault`
- `service_door_opened`
- `payment_timeout`

Allowed transitions:

- `WAITING_FOR_PAYMENT -> ACCEPTING_CASH`
- `WAITING_FOR_PAYMENT -> CANCELLED`
- `WAITING_FOR_PAYMENT -> FAULT`
- `WAITING_FOR_PAYMENT -> OUT_OF_SERVICE`

Guards:

- validator healthy and enabled;
- transaction still sellable;
- reservation or exact-cash policy still valid.

Side effects:

- enable validator;
- display remaining amount and instructions;
- start payment timeout.

Idempotency requirements:

- validator enable command must be safe to repeat;
- repeated timeout setup must not create multiple active timers.

Rollback and recovery behavior:

- if cancellation occurs before cash is stacked, release reserve and cancel transaction;
- if validator faults after enable but before stacked cash, cancel or fault according to recoverability.

Prohibited actions:

- payout;
- vend.

Power-loss recovery:

- disable validator on restart if possible;
- inspect journal for stacked cash before deciding whether transaction may cancel cleanly.

### `ACCEPTING_CASH`

Input events:

- `bill_detected`
- `bill_validated`
- `bill_rejected`
- `bill_stacked`
- `bill_returned`
- `validator_fault`
- `selection_cancelled`
- `payment_threshold_reached`

Allowed transitions:

- `ACCEPTING_CASH -> PAYMENT_ACCEPTED`
- `ACCEPTING_CASH -> CANCELLED`
- `ACCEPTING_CASH -> FAULT`
- `ACCEPTING_CASH -> OUT_OF_SERVICE`

Guards:

- validator remains enabled and healthy;
- additional accepted amount does not create unsafe payout exposure.

Side effects:

- update accepted amount on `bill_stacked`;
- refresh remaining balance;
- reject or disable further bills if overpay becomes unsafe;
- persist bill-related journal events.

Idempotency requirements:

- only `bill_stacked` changes durable accepted amount;
- duplicate device notifications must be deduplicated by validator event identity or sequence.

Rollback and recovery behavior:

- user cancellation after stacked cash is not an in-memory rollback; it becomes a refund or settlement decision;
- validator jam or ambiguous stack status moves transaction into fault or recovery flow.

Prohibited actions:

- product vend before payment confirmation;
- consuming change reserve before payout stage.

Power-loss recovery:

- journal replay determines last confirmed stacked amount;
- ambiguous validator state may require disabling cash sales and operator review.

### `PAYMENT_ACCEPTED`

Input events:

- `payment_confirmed`
- `change_dispense_requested`
- `vend_authorized`
- `payment_faulted`

Allowed transitions:

- `PAYMENT_ACCEPTED -> DISPENSING_CHANGE`
- `PAYMENT_ACCEPTED -> DISPENSING_PRODUCT`
- `PAYMENT_ACCEPTED -> FAULT`
- `PAYMENT_ACCEPTED -> RECOVERY_PENDING`

Guards:

- accepted amount is at least price;
- final change due computed;
- settlement policy resolved whether payout is required.

Side effects:

- durably mark payment confirmed;
- freeze further cash acceptance;
- compute final payout plan;
- consume or release change reserve according to due amount.

Idempotency requirements:

- payment confirmation is once-only per transaction;
- duplicate completion requests must return current settled state rather than re-trigger payout or vend.

Rollback and recovery behavior:

- payment confirmation cannot be undone by simple cancel;
- if payout requirement becomes ambiguous, enter recovery rather than proceeding to vend.

Prohibited actions:

- reopening cash session;
- direct transaction completion before payout or zero-change vend path is resolved.

Power-loss recovery:

- if payment confirmed is journaled, restart must never treat the sale as unpaid;
- next state is reconstructed from payout or vend intent markers.

### `DISPENSING_CHANGE`

Input events:

- `change_dispensed`
- `change_dispense_partially_completed`
- `change_dispense_failed`
- `manual_review_required`

Allowed transitions:

- `DISPENSING_CHANGE -> DISPENSING_PRODUCT`
- `DISPENSING_CHANGE -> FAULT`
- `DISPENSING_CHANGE -> RECOVERY_PENDING`

Guards:

- payout device healthy enough to attempt dispense;
- payout amount and denomination plan are durably recorded.

Side effects:

- command change dispenser;
- persist payout intent and confirmation;
- update cash inventory accounting only on confirmed payout facts.

Idempotency requirements:

- payout command must use an idempotency token tied to transaction id and payout attempt number;
- repeated confirmation events must not double-deduct inventory.

Rollback and recovery behavior:

- partial payout is not silently absorbed; it becomes fault or recovery depending on evidence;
- vend is blocked until payout is fully resolved by policy.

Prohibited actions:

- product vend before payout resolved;
- releasing transaction as completed.

Power-loss recovery:

- if payout intent exists without confirmation, treat payout as ambiguous until proven otherwise;
- machine may require operator reconciliation before more cash sales.

### `DISPENSING_PRODUCT`

Input events:

- `product_dispensed`
- `product_delivery_failed`
- `motor_fault`
- `inventory_mismatch_detected`

Allowed transitions:

- `DISPENSING_PRODUCT -> OPENING_DELIVERY_WINDOW`
- `DISPENSING_PRODUCT -> FAULT`
- `DISPENSING_PRODUCT -> RECOVERY_PENDING`

Guards:

- payment confirmed;
- payout resolved;
- slot still sellable and not already dispensed for this transaction.

Side effects:

- send vend command with transaction id;
- mark vend intent in journal before actuator command;
- decrement stock only on confirmed vend semantics defined by policy.

Idempotency requirements:

- vend command must be guarded against double-dispatch;
- duplicate product-dispensed signal must not double-decrement stock.

Rollback and recovery behavior:

- failed vend after confirmed payment cannot be solved by silent cancellation; recovery or compensation path is required;
- ambiguous vend result leads to operator review or sensor-assisted resolution.

Prohibited actions:

- accepting new sales on same slot if current vend outcome is ambiguous;
- reopening payment flow.

Power-loss recovery:

- journal replay determines whether vend was authorized;
- if physical result cannot be proven, transaction remains unresolved.

### `OPENING_DELIVERY_WINDOW`

Input events:

- `delivery_window_opened`
- `delivery_window_fault`

Allowed transitions:

- `OPENING_DELIVERY_WINDOW -> WAITING_FOR_CUSTOMER_PICKUP`
- `OPENING_DELIVERY_WINDOW -> FAULT`
- `OPENING_DELIVERY_WINDOW -> RECOVERY_PENDING`

Guards:

- vend result confirmed or sufficiently proven by policy;
- window subsystem healthy.

Side effects:

- issue open command;
- start pickup timer;
- project pickup instructions to UI.

Idempotency requirements:

- repeated open command should not damage actuator state and should converge on open intent;
- duplicate window-opened event is harmless.

Rollback and recovery behavior:

- if window does not open, transaction remains unresolved after successful vend and needs service handling.

Prohibited actions:

- final completion before pickup opportunity;
- new sale start.

Power-loss recovery:

- after restart, window state must be re-polled;
- if vend confirmed but window status uncertain, machine enters recovery or service flow.

### `WAITING_FOR_CUSTOMER_PICKUP`

Input events:

- `pickup_confirmed`
- `pickup_timeout_elapsed`
- `service_door_opened`

Allowed transitions:

- `WAITING_FOR_CUSTOMER_PICKUP -> CLOSING_DELIVERY_WINDOW`
- `WAITING_FOR_CUSTOMER_PICKUP -> FAULT`
- `WAITING_FOR_CUSTOMER_PICKUP -> RECOVERY_PENDING`

Guards:

- delivery window is open;
- pickup monitoring active.

Side effects:

- display pickup instructions;
- monitor sensors or timeout.

Idempotency requirements:

- duplicate pickup confirmations must not create multiple close-window sequences.

Rollback and recovery behavior:

- timeout closes the delivery window, then holds the transaction for recovery/manual review or enters fault if close fails;
- if pickup cannot be confirmed but product is accessible, software must avoid duplicate vend.

Prohibited actions:

- new payment session;
- second vend for same transaction.

Power-loss recovery:

- restart requires evaluating whether product is already in pickup zone and whether window is open.

### `CLOSING_DELIVERY_WINDOW`

Input events:

- `delivery_window_closed`
- `delivery_window_fault`

Allowed transitions:

- `CLOSING_DELIVERY_WINDOW -> COMPLETED`
- `CLOSING_DELIVERY_WINDOW -> FAULT`
- `CLOSING_DELIVERY_WINDOW -> RECOVERY_PENDING`

Guards:

- pickup phase ended by confirmation or timeout policy.

Side effects:

- command window close;
- write close intent and result to journal.

Idempotency requirements:

- close command and confirmation handling must be repeat-safe.

Rollback and recovery behavior:

- if close fails, machine may complete customer delivery but remain blocked for further sales until service.

Prohibited actions:

- clearing transaction before window resolution policy runs.

Power-loss recovery:

- poll physical window state and reconstruct whether closure remains outstanding.

### `COMPLETED`

Input events:

- `completion_acknowledged`

Allowed transitions:

- `COMPLETED -> IDLE`
- `COMPLETED -> OUT_OF_SERVICE`

Guards:

- transaction marked settled and non-ambiguous.

Side effects:

- finalize journal entry;
- release any remaining non-consumed reservation artifacts;
- clear active transaction;
- publish sales counters and telemetry.

Idempotency requirements:

- completion event may be replayed without changing money or stock twice.

Rollback and recovery behavior:

- none; completion is terminal for the transaction.

Prohibited actions:

- further payout or vend for the same transaction.

Power-loss recovery:

- completed transactions remain completed after replay; machine usually returns to `IDLE`.

### `CANCELLED`

Input events:

- `cancellation_acknowledged`

Allowed transitions:

- `CANCELLED -> IDLE`
- `CANCELLED -> OUT_OF_SERVICE`

Guards:

- no unresolved payout or vend action remains.

Side effects:

- record cancellation result;
- release change reservation and slot lock if safe;
- disable validator if still enabled.

Idempotency requirements:

- cancellation can be replayed without double-releasing reserve or stock lock.

Rollback and recovery behavior:

- if cash had already been stacked, cancellation is allowed only after refund or explicit recovery policy resolution.

Prohibited actions:

- treating stacked cash as if it never existed;
- reopening transaction without a new transaction id.

Power-loss recovery:

- replay verifies reserve release and absence of unresolved cash or vend side effects before restoring `IDLE`.

### `OUT_OF_SERVICE`

Input events:

- `service_mode_entered`
- `fault_cleared`
- `machine_recovered`

Allowed transitions:

- `OUT_OF_SERVICE -> SERVICE_MODE`
- `OUT_OF_SERVICE -> IDLE`
- `OUT_OF_SERVICE -> RECOVERY_PENDING`

Guards:

- customer mode blocked;
- operator or recovery preconditions decide next state.

Side effects:

- disable validator and vend actions;
- show blocking UI;
- raise service alerts.

Idempotency requirements:

- repeated disable commands are safe;
- repeated alerts should be deduplicated.

Rollback and recovery behavior:

- remains non-selling until blockers clear.

Prohibited actions:

- customer sale flow.

Power-loss recovery:

- restart remains blocked until self-test and recovery re-evaluate.

### `FAULT`

Input events:

- `fault_cleared`
- `manual_review_required`

Allowed transitions:

- `FAULT -> OUT_OF_SERVICE`
- `FAULT -> SERVICE_MODE`
- `FAULT -> RECOVERY_PENDING`

Guards:

- critical fault present or recent unresolved hardware failure.

Side effects:

- disable cash acceptance and vending;
- persist fault details;
- preserve transaction ambiguity markers.

Idempotency requirements:

- entering fault repeatedly must not duplicate destructive device commands.

Rollback and recovery behavior:

- fault may downgrade to out-of-service or recovery pending after diagnosis;
- never auto-resume sale mode if transaction integrity is uncertain.

Prohibited actions:

- new sale start;
- assuming compensation occurred without evidence.

Power-loss recovery:

- faults are rebuilt from journal plus fresh health snapshot.

### `SERVICE_MODE`

Input events:

- `service_mode_exited`
- `reconcile_requested`
- `fault_detected`

Allowed transitions:

- `SERVICE_MODE -> OUT_OF_SERVICE`
- `SERVICE_MODE -> IDLE`
- `SERVICE_MODE -> FAULT`
- `SERVICE_MODE -> RECOVERY_PENDING`

Guards:

- operator authorization present;
- customer mode inactive.

Side effects:

- enable maintenance UI;
- allow reconcile procedures and diagnostics;
- audit all service actions.

Idempotency requirements:

- entering service mode again must not disturb open maintenance session state.

Rollback and recovery behavior:

- service actions are audited, not silently rolled back;
- if maintenance discovers ambiguity, keep machine blocked until resolved.

Prohibited actions:

- customer sales;
- implicit clearing of faults without audit trail.

Power-loss recovery:

- restart returns to blocked mode, not to customer mode, until operator or policy re-enables sales.

### `RECOVERY_PENDING`

Input events:

- `recovery_started`
- `recovery_completed`
- `manual_review_required`
- `fault_detected`

Allowed transitions:

- `RECOVERY_PENDING -> IDLE`
- `RECOVERY_PENDING -> OUT_OF_SERVICE`
- `RECOVERY_PENDING -> FAULT`
- `RECOVERY_PENDING -> SERVICE_MODE`

Guards:

- unresolved or ambiguous transaction or journal state exists.

Side effects:

- replay journal;
- query device health and any available physical indicators;
- classify unresolved actions;
- block unsafe sales until recovery outcome is known.

Idempotency requirements:

- replay and classification must be deterministic;
- repeated recovery attempts must not double-issue payout or vend commands unless explicitly authorized by recovery policy.

Rollback and recovery behavior:

- this is the dedicated state for non-trivial post-crash resolution;
- outcome may be automatic, operator-assisted, or faulted.

Prohibited actions:

- accepting new cash;
- starting new vend cycles;
- auto-marking ambiguous transactions as successful.

Power-loss recovery:

- re-enter `RECOVERY_PENDING` until ambiguity is resolved.

## Global FSM guards

- sales blocked if service door is open;
- sales blocked if temperature state is critical;
- sales blocked if a critical device fault exists;
- cash acceptance blocked if safe change cannot be guaranteed under current policy;
- vend blocked unless payment is durably confirmed;
- transaction completion blocked while payout or vend outcome remains ambiguous.

## Global idempotency rules

- every critical command must carry `transaction_id` and `correlation_id`;
- device-side operations that can change cash or stock must also carry an operation idempotency token;
- journal writes for the same logical stage must be deduplicatable;
- replay must never transform one ambiguous fact into multiple physical commands without explicit policy.

## Recovery semantics summary

- journal facts override volatile FSM state;
- payment confirmation is irreversible without explicit compensating flow;
- ambiguous payout blocks new cash sales until reconciled;
- ambiguous vend blocks affected slot and may block the whole machine;
- cancellation is only cheap before confirmed cash stack or physical action intent;
- after confirmed side effects, recovery chooses compensation or manual review, not silent rollback.

## Phase outcome classification

### Fully implemented conceptually

- domain entities and value objects
- aggregates and invariants
- domain services and policies
- commands, events, and handler responsibilities
- custom exception hierarchy
- full FSM with recovery semantics

### Scaffolded

- file-based Phase 3 domain and FSM specification
- ADR for FSM authority and domain invariant ownership

### Requires hardware confirmation

- exact sensor evidence needed to mark vend success or ambiguity
- exact payout confirmation signals available from the change dispenser
- validator event granularity and ordering guarantees on the selected DBV-300-SD protocol
- delivery window pickup confirmation mechanism

## Assumptions

- A transaction-centric aggregate is the right unit of consistency for payment, payout, vend, and pickup outcome decisions.
- Only one customer transaction is active per machine at a time.
- Payment acceptance is based on confirmed stack semantics, not mere bill detection.
- Inventory sensor confidence may be partial, so the domain must support ambiguous stock states.
- Recovery can classify some cases automatically, but unresolved payout or vend ambiguities may require operator review.
