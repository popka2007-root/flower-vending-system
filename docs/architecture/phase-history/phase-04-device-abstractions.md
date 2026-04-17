# Phase 4 - Device Abstractions

## Scope of this phase

This phase establishes the hardware abstraction layer for the vending machine and implements the architectural split required for the JCM DBV-300-SD:

- domain-facing device contracts;
- normalized device DTOs and events;
- separate DBV-300-SD transport layer;
- separate DBV-300-SD protocol layer;
- separate domain-facing validator adapter;
- explicit extension points for MDB, serial, and pulse-like variants.

No unconfirmed low-level JCM protocol frames, timing constants, or binary handshakes are invented here.

## Device interfaces

The device layer now defines normalized contracts for:

- `BillValidator`
- `ChangeDispenser`
- `MotorController`
- `CoolingController`
- `WindowController`
- `TemperatureSensor`
- `DoorSensor`
- `InventorySensor`
- `PositionSensor`
- `WatchdogAdapter`

All of them inherit from a common lifecycle contract, `ManagedDevice`, with:

- `start()`
- `stop()`
- `get_health()`

This gives the application core one consistent lifecycle and health model for all hardware adapters.

## Shared device contracts

The device layer uses explicit DTOs rather than ad hoc dictionaries:

- `DeviceHealth`
- `DeviceFault`
- `MoneyValue`
- `BillValidatorEvent`
- `ValidatorProtocolEvent`
- `ChangeDispenseRequest`
- `ChangeDispenseResult`
- `TemperatureReading`
- `DoorStatus`
- `InventoryPresence`
- `PositionReading`
- `WindowStatus`

The normalized validator event model includes the required domain-facing event names:

- `bill_detected`
- `bill_validated`
- `bill_rejected`
- `escrow_available`
- `bill_stacked`
- `bill_returned`
- `validator_fault`
- `validator_disabled`

## DBV-300-SD split

### 1. Transport layer

`DBV300Transport` is a raw byte-stream interface:

- `open()`
- `close()`
- `write(bytes)`
- `read(size)`
- `flush_input()`

The implemented concrete transport is `SerialDBV300Transport`, which is a generic cross-platform serial wrapper built on `pyserial`. It knows about ports, baud rate, parity, stop bits, timeouts, and open or close behavior, but it does not know any DBV-300-SD commands.

### 2. Protocol layer

`DBV300Protocol` is the semantic device-protocol contract above transport:

- `initialize()`
- `shutdown()`
- `set_acceptance_enabled()`
- `poll()`
- `stack_escrow()`
- `return_escrow()`

This layer returns `ValidatorProtocolEvent` objects and declares `ProtocolCapabilities`, including whether escrow is confirmed as supported.

At this phase, concrete protocol implementations are deliberately deferred:

- `DeferredSerialProtocol`
- `DeferredMDBProtocol`
- `DeferredPulseProtocol`

Each of them raises `HardwareConfirmationRequiredError` because the real JCM wire-level behavior has not been confirmed yet.

### 3. Domain-facing validator adapter

`DBV300SDValidator` implements the generic `BillValidator` interface and owns:

- adapter lifecycle;
- health projection;
- polling loop;
- translation from protocol events into normalized bill validator events;
- fault conversion into `validator_fault`;
- acceptance enable or disable orchestration;
- escrow support gating based on protocol capability.

This means the application layer can depend on `BillValidator` and never care whether the concrete implementation is serial, MDB, pulse-like, simulator, or future bench adapter.

## Extension points

### DBV-300-SD protocol extension point

To integrate the real JCM documentation later, implement a confirmed `DBV300Protocol` subclass without changing:

- `BillValidator`
- `DBV300SDValidator`
- payment orchestration
- domain events
- recovery logic

### Transport extension point

To add MDB or pulse-like physical access later, implement `DBV300Transport` or bind another transport adapter in the builder. The rest of the validator adapter can remain unchanged.

### Simulator extension point

Future mocks and simulators can:

- implement `BillValidator` directly; or
- reuse `DBV300SDValidator` with an in-memory test transport and a deterministic fake protocol.

This is the key boundary between real hardware integration and simulator behavior.

## Real integration boundary vs simulation boundary

### Real integration boundary

The following pieces are real runtime code and safe to use now:

- normalized device contracts;
- lifecycle and health model;
- generic serial byte transport;
- DBV-300-SD config model;
- validator adapter lifecycle and event queue handling.

### Simulation boundary

The following are intentionally left as extension points for Phase 6:

- mock validator implementation;
- fake change dispenser;
- fake motor and sensors;
- deterministic fault-injection scenarios.

### Hardware confirmation boundary

The following still require confirmed documentation and bench testing:

- real DBV-300-SD serial protocol;
- real MDB protocol mapping;
- real pulse timing and denomination mapping;
- exact escrow behavior;
- event sequencing guarantees and retry timing.

## Where COM3 is handled

The known lab fact that the validator is connected to `COM3` is handled only in configuration through:

- `DBV300SDValidatorConfig`
- `SerialTransportSettings.port`

The builder reads this configuration and creates `SerialDBV300Transport` from it. `COM3` is not hardcoded in:

- domain logic;
- payment logic;
- FSM;
- application services.

## Exceptions and safety behavior

The device layer introduces explicit exceptions:

- `DeviceAdapterError`
- `DeviceNotStartedError`
- `UnsupportedDeviceOperationError`
- `HardwareConfirmationRequiredError`
- `TransportIOError`
- `ProtocolDecodeError`
- `ConfigurationError`

This keeps protocol uncertainty separate from business failures and makes it explicit when a feature is blocked on real hardware confirmation rather than on software structure.

## Design consequences for later phases

- Phase 5 can orchestrate the validator through `BillValidator` without knowing transport details.
- Phase 6 can supply a simulator that implements the same contract.
- Phase 7 can bind YAML config into `DBV300SDValidatorConfig`, including the real `COM3` setting.
- Phase 10 can replace deferred protocols with confirmed JCM implementations without reshaping the core architecture.

## Phase outcome classification

### Fully implemented

- normalized device contracts and DTOs
- lifecycle and health abstraction for hardware adapters
- generic `BillValidator` contract with required event vocabulary
- DBV-300-SD config models
- DBV-300-SD transport/protocol/domain-adapter split
- real generic serial transport wrapper
- validator adapter lifecycle and fault translation

### Scaffolded

- builder-based DBV-300-SD binding
- deferred protocol placeholders for serial, MDB, and pulse modes
- protocol capability model for escrow support
- simulator injection boundary

### Requires hardware confirmation

- actual DBV-300-SD serial protocol commands and framing
- MDB-specific integration details
- pulse timing and denomination mapping
- validator startup, disable, poll, and escrow sequences
- exact timeout and retry policy validated on a real bench

## Assumptions

- A byte-stream serial transport can be implemented safely before the validator command set is confirmed.
- The chosen lab setup exposes the validator through a host-visible serial port such as `COM3`, but that fact belongs to configuration only.
- A future confirmed JCM implementation can map wire-level events into the normalized event vocabulary already defined here.
- Some protocol variants may not support escrow; that must be expressed via capabilities, not hidden in payment logic.
