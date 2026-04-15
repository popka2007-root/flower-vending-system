# Phase 2 - Project Structure

## Scope of this phase

This phase defines the repository and package structure that will host the production system. The goal is to make the architectural boundaries from Phase 1 concrete without prematurely implementing domain rules or device logic that belong to later phases.

## Repository layout

```text
flower-vending-system/
├── README.md
├── pyproject.toml
├── config/
│   ├── machine.example.yaml
│   ├── devices.example.yaml
│   └── ui.example.yaml
├── docs/
│   ├── phase-01-architecture.md
│   ├── phase-02-project-structure.md
│   └── adr/
│       ├── ADR-0001-layered-architecture.md
│       ├── ADR-0002-journal-first-recovery.md
│       ├── ADR-0003-cash-transaction-and-change-safety.md
│       ├── ADR-0004-platform-isolation-and-dbv300sd-adapter.md
│       └── ADR-0005-src-layout-and-module-packaging.md
├── scripts/
│   ├── run_kiosk.py
│   ├── run_headless.py
│   └── simulate_machine.py
├── src/
│   └── flower_vending/
│       ├── __init__.py
│       ├── app/
│       │   ├── __init__.py
│       │   ├── bootstrap.py
│       │   ├── command_bus.py
│       │   ├── event_bus.py
│       │   ├── fsm/
│       │   │   ├── __init__.py
│       │   │   ├── machine_fsm.py
│       │   │   ├── states.py
│       │   │   └── transitions.py
│       │   ├── orchestrators/
│       │   │   ├── __init__.py
│       │   │   ├── vending_controller.py
│       │   │   ├── payment_coordinator.py
│       │   │   ├── transaction_coordinator.py
│       │   │   ├── recovery_manager.py
│       │   │   ├── health_monitor.py
│       │   │   └── cooling_supervisor.py
│       │   └── services/
│       │       ├── __init__.py
│       │       ├── inventory_service.py
│       │       └── machine_status_service.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── aggregates/
│       │   │   ├── __init__.py
│       │   │   ├── payment_transaction.py
│       │   │   └── machine_runtime.py
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── purchase_commands.py
│       │   │   ├── service_commands.py
│       │   │   └── recovery_commands.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── product.py
│       │   │   ├── slot.py
│       │   │   ├── money_inventory.py
│       │   │   ├── transaction.py
│       │   │   ├── payment_session.py
│       │   │   ├── change_reserve.py
│       │   │   ├── machine_status.py
│       │   │   └── device_health_snapshot.py
│       │   ├── events/
│       │   │   ├── __init__.py
│       │   │   ├── payment_events.py
│       │   │   ├── vending_events.py
│       │   │   ├── machine_events.py
│       │   │   └── device_events.py
│       │   ├── exceptions/
│       │   │   ├── __init__.py
│       │   │   ├── payment_exceptions.py
│       │   │   ├── vending_exceptions.py
│       │   │   └── recovery_exceptions.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── change_policy.py
│       │   │   ├── availability_policy.py
│       │   │   └── recovery_policy.py
│       │   └── value_objects/
│       │       ├── __init__.py
│       │       ├── amount.py
│       │       ├── currency.py
│       │       ├── denomination.py
│       │       ├── temperature.py
│       │       ├── device_state.py
│       │       ├── slot_id.py
│       │       ├── product_id.py
│       │       ├── transaction_id.py
│       │       └── correlation_id.py
│       ├── devices/
│       │   ├── __init__.py
│       │   ├── interfaces/
│       │   │   ├── __init__.py
│       │   │   ├── bill_validator.py
│       │   │   ├── change_dispenser.py
│       │   │   ├── motor_controller.py
│       │   │   ├── cooling_controller.py
│       │   │   ├── window_controller.py
│       │   │   ├── temperature_sensor.py
│       │   │   ├── door_sensor.py
│       │   │   ├── inventory_sensor.py
│       │   │   ├── position_sensor.py
│       │   │   └── watchdog_adapter.py
│       │   └── dbv300sd/
│       │       ├── __init__.py
│       │       ├── adapter.py
│       │       ├── protocol/
│       │       │   ├── __init__.py
│       │       │   ├── base.py
│       │       │   ├── serial_protocol.py
│       │       │   ├── mdb_protocol.py
│       │       │   └── pulse_protocol.py
│       │       └── transport/
│       │           ├── __init__.py
│       │           ├── base.py
│       │           ├── serial_transport.py
│       │           ├── mdb_transport.py
│       │           └── pulse_transport.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── config/
│       │   │   ├── __init__.py
│       │   │   ├── loader.py
│       │   │   └── models.py
│       │   ├── logging/
│       │   │   ├── __init__.py
│       │   │   └── structured.py
│       │   ├── persistence/
│       │   │   ├── __init__.py
│       │   │   └── sqlite/
│       │   │       ├── __init__.py
│       │   │       ├── connection.py
│       │   │       ├── journal_repository.py
│       │   │       ├── machine_state_repository.py
│       │   │       ├── inventory_repository.py
│       │   │       ├── cash_repository.py
│       │   │       └── schema.sql
│       │   ├── platform/
│       │   │   ├── __init__.py
│       │   │   ├── linux/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── kiosk.py
│       │   │   │   ├── service_host.py
│       │   │   │   └── watchdog.py
│       │   │   └── windows/
│       │   │       ├── __init__.py
│       │   │       ├── kiosk.py
│       │   │       ├── service_host.py
│       │   │       └── watchdog.py
│       │   ├── startup/
│       │   │   ├── __init__.py
│       │   │   └── bootstrap.py
│       │   └── telemetry/
│       │       ├── __init__.py
│       │       ├── metrics.py
│       │       └── error_reporting.py
│       ├── inventory/
│       │   ├── __init__.py
│       │   ├── policies.py
│       │   └── service.py
│       ├── payments/
│       │   ├── __init__.py
│       │   ├── change_manager.py
│       │   ├── exact_change_policy.py
│       │   └── accounting.py
│       ├── vending/
│       │   ├── __init__.py
│       │   ├── service.py
│       │   └── pickup_policy.py
│       ├── cooling/
│       │   ├── __init__.py
│       │   ├── policy.py
│       │   └── supervisor.py
│       ├── telemetry/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   └── audit.py
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── presenters/
│       │   │   ├── __init__.py
│       │   │   ├── catalog_presenter.py
│       │   │   ├── payment_presenter.py
│       │   │   ├── error_presenter.py
│       │   │   └── service_presenter.py
│       │   ├── viewmodels/
│       │   │   ├── __init__.py
│       │   │   ├── catalog_vm.py
│       │   │   ├── payment_vm.py
│       │   │   ├── machine_status_vm.py
│       │   │   └── diagnostics_vm.py
│       │   ├── views/
│       │   │   ├── __init__.py
│       │   │   ├── main_window.py
│       │   │   ├── catalog_screen.py
│       │   │   ├── payment_screen.py
│       │   │   ├── dispensing_screen.py
│       │   │   ├── pickup_screen.py
│       │   │   ├── fault_screen.py
│       │   │   └── service_screen.py
│       │   └── widgets/
│       │       ├── __init__.py
│       │       └── touch_controls.py
│       └── simulators/
│           ├── __init__.py
│           ├── devices/
│           │   ├── mock_bill_validator.py
│           │   ├── mock_change_dispenser.py
│           │   ├── mock_motor_controller.py
│           │   ├── mock_window_controller.py
│           │   ├── mock_temperature_sensor.py
│           │   ├── mock_door_sensor.py
│           │   └── mock_inventory_sensor.py
│           └── scenarios/
│               ├── happy_path.py
│               ├── partial_payout.py
│               ├── reboot_mid_transaction.py
│               └── service_door_open.py
└── tests/
    ├── fixtures/
    │   ├── sample_catalog.yaml
    │   ├── sample_devices.yaml
    │   └── journal_samples.json
    ├── integration/
    ├── recovery/
    └── unit/
```

## Module purpose by layer

### `src/flower_vending/domain`

Pure business model. No UI, OS, SQLite, COM port, or protocol assumptions are allowed here.

### `src/flower_vending/app`

Application layer for orchestration, FSM execution, command handling, workflow sequencing, and coordination of domain plus devices.

### `src/flower_vending/devices`

Hardware abstraction layer and device-specific adapters. DBV-300-SD integration is isolated here with a strict split between transport, protocol, and domain-facing adapter.

### `src/flower_vending/infrastructure`

Cross-cutting technical adapters: SQLite, logging, config, startup, telemetry sinks, and Linux/Windows bindings.

### `src/flower_vending/payments`

Cash-session orchestration helpers, change management, accounting policies, and future settlement extension points.

### `src/flower_vending/inventory`

Inventory-specific services, policies, and drift handling that do not belong to generic domain primitives.

### `src/flower_vending/vending`

Vend execution policies, pickup semantics, and safe delivery coordination.

### `src/flower_vending/cooling`

Cooling supervision policies and temperature-driven sales blocking behavior.

### `src/flower_vending/telemetry`

Machine health projection, service audit semantics, and domain-level observability models.

### `src/flower_vending/ui`

Presenter/view-model driven touch UI. Depends on application interfaces, not domain internals or direct device drivers.

### `src/flower_vending/simulators`

Deterministic mocks, fault injection, and scenario runners for headless testing and bench-free development.

## Layer separation rules

- `domain` cannot import from `app`, `devices`, `ui`, or `infrastructure`.
- `app` can depend on `domain` and device interfaces, but not on concrete hardware protocol details.
- `devices` can depend on infrastructure transport utilities, but device protocol code cannot contain business rules.
- `ui` can call application commands and subscribe to application-facing view models only.
- `simulators` must implement the same contracts as real devices.

## Platform-specific areas

### Linux/Windows specific

The following are intentionally platform-specific and live under `src/flower_vending/infrastructure/platform/`:

- kiosk shell integration;
- service hosting;
- watchdog integration;
- OS-specific startup and recovery hooks.

### Platform-neutral but hardware-facing

The following remain platform-neutral in contract but connect to hardware-specific implementations:

- `devices/interfaces/`
- `devices/dbv300sd/`
- `infrastructure/persistence/`
- `app/orchestrators/`

## Mock and simulator placement

- deterministic device doubles live in `src/flower_vending/simulators/devices/`
- scenario scripts live in `src/flower_vending/simulators/scenarios/`
- reusable sample input and journal fixtures live in `tests/fixtures/`

## Where COM3 is handled

The known `COM3` fact is not part of the package structure or business code. It is expected to appear only in configuration files under `config/` and in infrastructure config models that bind device settings at startup.

## Why `src` layout was chosen

- avoids accidental imports from the working directory;
- keeps packaging explicit;
- lets us expose a single logical product package, `flower_vending`;
- makes the top-level module groups from the ADRs visible as subpackages without flattening the repository into fragile import paths.

## Phase outcome classification

### Fully implemented conceptually

- Full repository layout
- Layer boundaries
- Placement of platform-specific code
- Placement of mocks and simulators
- Packaging strategy for future implementation phases

### Scaffolded

- Repository directories
- Base Python package markers
- Build metadata and repository README
- Phase 2 structure document
- ADR for source layout and packaging

### Requires hardware confirmation

- Final shape of concrete DBV-300-SD protocol files
- Concrete payout device adapter subtree
- Low-level motor/window device package granularity if vendor SDKs are introduced

## Assumptions

- A single distributable Python package is preferred over many separately deployed services.
- The machine runs one main application process, even if helper watchdog/service wrappers exist.
- Kiosk UI, headless simulator, and service tooling can share the same package graph with different entrypoints.
- Device-specific vendor SDKs, if later required, can be isolated behind adapters without reshaping the package tree.
