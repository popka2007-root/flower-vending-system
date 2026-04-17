# Phase 7 - Persistence and Config

## Scope of this phase

This phase implements the durable local persistence and configuration baseline required by the architecture decisions from earlier phases.

The focus is:

- SQLite schema for local machine state and audit data;
- repositories for catalog, runtime state, and operational logs;
- an append-only transaction journal suitable for recovery-first replay;
- YAML-backed configuration models;
- structured logging setup with rotating files;
- example device mappings and port/timeouts configuration, including the current `COM3` validator deployment fact.

## Architecture alignment

This phase follows the existing source of truth and does not revise earlier decisions.

Key constraints preserved here:

- durable recovery is journal-first;
- business logic remains platform-neutral;
- device and OS specifics stay in infrastructure/configuration;
- `COM3` exists only in configuration and example deployment files, never in domain or application logic;
- unsupported hardware details remain explicit extension points.

## Implemented SQLite schema

The SQLite schema now includes:

- `schema_metadata`
- `products`
- `slots`
- `machine_status_projection`
- `money_inventory`
- `transactions`
- `transaction_journal`
- `device_fault_log`
- `service_events`
- `temperature_events`
- `recovery_log`
- `device_settings`
- `applied_config`

This covers the required storage areas from the brief:

- product catalog and prices;
- slot inventory;
- unresolved and historical transactions;
- durable transaction journal;
- change inventory and accounting state;
- device faults;
- service and temperature events;
- recovery actions;
- applied device and platform configuration snapshots.

## SQLite infrastructure layer

### SQLiteDatabase

`SQLiteDatabase` provides:

- one owned SQLite connection;
- `WAL`-friendly connection pragmas;
- `busy_timeout`;
- helper methods for scripts, inserts, queries, and transactions;
- JSON serialization helpers.

The implementation stays intentionally small so that repository and journal logic remain easy to audit.

### Schema bootstrap

`ensure_sqlite_schema(...)` installs the schema and stores the current schema version in `schema_metadata`.

This gives later phases a clear extension point for migration handling without prematurely introducing a migration framework.

## Implemented repositories

The following repositories are now implemented:

- `ProductRepository`
- `SlotRepository`
- `MachineStatusRepository`
- `MoneyInventoryRepository`
- `TransactionRepository`
- `DeviceFaultLogRepository`
- `OperationalEventRepository`
- `DeviceSettingsRepository`
- `AppliedConfigRepository`

### Repository responsibilities

`ProductRepository` and `SlotRepository` persist the sellable catalog and slot state.

`MachineStatusRepository` persists the machine status projection separately from the transaction log. This keeps current operational policy visible without treating it as the recovery source of truth.

`MoneyInventoryRepository` stores accounting counts, reserved counts, confidence, and drift flags for the change subsystem.

`TransactionRepository` persists transaction aggregates, including nullable `payment_session` and `change_reserve` snapshots.

`DeviceFaultLogRepository` persists machine and device faults for service workflows and audit.

`OperationalEventRepository` records service, temperature, and recovery events.

`DeviceSettingsRepository` stores the effective device-level settings snapshot.

`AppliedConfigRepository` stores the text and hash of the applied YAML configuration for auditability.

## Implemented transaction journal

`SQLiteTransactionJournal` is the durable append-only journal for:

- intent records;
- domain events;
- fault records;
- recovery records.

Each journal row stores:

- transaction id when available;
- correlation id;
- entry kind;
- entry name;
- machine state;
- transaction status;
- JSON payload;
- optional idempotency key;
- creation timestamp.

The journal supports:

- append by explicit `JournalEntry`;
- convenience methods for intent, event, fault, and recovery records;
- async event-bus compatible `handle_domain_event(...)`;
- per-transaction replay reads;
- recent readback;
- unresolved transaction id discovery.

## Important persistence fixes found during implementation

Two concrete persistence bugs were caught and corrected during this phase.

### Nullable JSON columns

`TransactionRepository` originally serialized missing `payment_session` and `change_reserve` values as `{}` instead of `NULL`.

That is unsafe for recovery because it turns "no session exists" into "an empty session object exists".

The implementation was corrected so nullable JSON columns remain nullable on write and are restored with explicit defaults on read.

### JSON default handling

The generic JSON serializer originally coerced any falsy payload to `{}`. That would silently corrupt empty arrays and similar values.

The serializer was corrected to preserve empty lists and other non-`None` payloads exactly.

## YAML configuration models

The infrastructure configuration package now provides strongly validated application config models for:

- machine identity and policy;
- persistence settings;
- structured logging settings;
- platform runtime mode;
- watchdog settings;
- bill validator settings;
- generic extension-point settings for the remaining devices.

The bill validator config deliberately maps into the already accepted `DBV300SDValidatorConfig` runtime contract instead of inventing a second source of truth.

## Example configuration files

Three example configurations were added:

- `config/examples/machine.windows.yaml`
- `config/examples/machine.linux.yaml`
- `config/examples/machine.simulator.yaml`

The Windows example includes the currently known validator deployment on `COM3`.

The Linux example uses a placeholder serial path example and keeps all non-confirmed device integrations as `requires_hardware_confirmation`.

The simulator example maps the same logical machine roles to simulator drivers and is suitable for headless runs and later tests.

## Structured logging

The structured logging package now provides:

- `JsonLogFormatter`
- `StructuredLoggerAdapter`
- `configure_logging(...)`

The default runtime behavior is:

- JSON log lines;
- rotating file output;
- optional stderr mirroring;
- support for correlation and transaction identifiers via structured extras.

This keeps diagnostic logging separate from the recovery journal while still making cross-component tracing possible.

## Verification performed

### Successful verification

The following verification was completed successfully:

- `py_compile` over the full `src/` tree;
- a persistence smoke run that initialized SQLite schema, saved and loaded catalog/runtime entities, appended journal records, recorded operational logs, and read them back successfully.

### Environment limitation

Runtime smoke validation for YAML file loading and pydantic-backed config objects inside the current shell environment was blocked because the declared project dependencies `PyYAML` and `pydantic` are not installed in the active interpreter environment.

This is an environment dependency issue, not a design conflict. The project metadata already declares these packages as runtime dependencies.

## Assumptions

- Local SQLite remains the single-node durable store for this product baseline.
- Journal replay remains the authoritative recovery path, while status projections remain secondary views.
- One logical machine instance writes to one local SQLite file.
- YAML configuration is loaded during bootstrap and can be snapshotted into SQLite for audit.

## Fully implemented

- SQLite connection wrapper
- SQLite schema and schema bootstrap
- repositories for catalog, machine status, money inventory, transactions, faults, operations, device settings, and applied config
- durable transaction journal with append and readback helpers
- validated configuration model structure
- YAML example files for Windows, Linux, and simulator deployment
- structured logging setup with JSON output and rotation

## Scaffolded

- migration framework beyond schema version stamping
- repository-backed integration into the application bootstrap path
- journal-first recovery manager backed directly by persisted replay instead of in-memory coordinator state
- cryptographic signing or tamper-evidence for journal rows
- richer config-profile merging or secrets handling

## Requires hardware confirmation

- non-validator device driver names, transports, and timeout values in the example YAML files
- Linux serial device path for the DBV-300-SD on the target controller
- final accepted banknote denominations for the deployed validator configuration
- change dispenser timeout, fault, and reconcile settings
- motor, window, cooling, and sensor-specific transport settings
