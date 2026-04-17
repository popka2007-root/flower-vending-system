# Phase 1 - Architectural Decision

## Scope of this phase

This phase establishes the production-grade architecture baseline for a flower vending machine control system. It intentionally avoids inventing unconfirmed device-level protocol details, especially for the JCM DBV-300-SD, while still defining the system boundaries, core responsibilities, recovery approach, and safety model needed for later implementation phases.

## Short architectural description

The system is designed as a layered, event-driven control platform with strict separation between:

- domain logic;
- application orchestration;
- device abstractions;
- infrastructure adapters;
- kiosk UI;
- simulation and test harnesses.

At runtime, the machine is controlled by an application core that executes a finite state machine (FSM) backed by a command/event model and a journal-first persistence strategy. Critical steps such as payment acceptance, change reservation, change payout, product vend authorization, delivery window control, and recovery decisions are recorded as durable transaction journal entries before or at the point of intent, so that restart logic can reconstruct the machine state from durable facts rather than from volatile memory.

The business core is platform-neutral. Linux/Windows differences are isolated in infrastructure adapters for serial access, service hosting, kiosk mode, watchdog integration, autostart, and OS-facing device supervision. Device drivers are hidden behind interfaces so the core can run with mocks or deterministic simulators without real hardware or UI.

## Selected technology stack

### Primary stack

- Python 3.11+
- `asyncio` for orchestration, device polling, timers, and event-driven workflows
- PySide6 / Qt for touch-first kiosk UI
- SQLite for local durable state and transaction journal
- YAML for configuration
- structured logging with rotating files

### Why this stack

#### Reliability

- Python 3.11 provides mature async I/O, strong typing support, and a broad ecosystem for industrial integration.
- SQLite offers robust local durability, crash recovery guarantees, and operational simplicity for single-machine deployments.
- PySide6 supports kiosk/touch applications on both Windows and Linux while remaining separate from the control core.

#### Maintainability

- The stack supports modular packaging, clear boundaries, and fast team onboarding.
- Python is well-suited for writing simulation-heavy and test-heavy device orchestration logic.

#### Testability

- Async orchestration plus interface-driven devices enables deterministic simulators and failure injection.
- The domain and application layers can be tested headlessly, without COM ports, GUI, or real electromechanical devices.

#### Hardware integration

- Serial integration is straightforward on both Windows and Linux.
- Protocol and transport splitting supports later MDB/serial/pulse integration without contaminating business logic.

### Explicit non-goals for this phase

- No low-level JCM DBV-300-SD binary frames, timings, or handshakes are implemented without confirmed documentation and lab validation.
- No vendor-specific payout protocol is defined without hardware confirmation.

## Key engineering trade-offs

### 1. Python over lower-level languages

Chosen for maintainability, velocity, testability, and cross-platform support. The trade-off is less deterministic low-level timing control than C/C++, but that risk is contained because:

- device protocols are isolated behind adapters;
- time-critical hardware control should remain in device firmware or dedicated controllers where applicable;
- the vending controller mostly coordinates stateful workflows rather than generating high-frequency control loops.

### 2. Journal-first recovery over in-memory FSM snapshots

Chosen because legacy instability and power-loss scenarios require durable intent tracking. The trade-off is more disciplined persistence design and slightly more complexity, but it significantly reduces ambiguity after restarts.

### 3. Rich abstraction around payment devices

Chosen to support DBV-300-SD variability across serial/MDB/pulse-like configurations. The trade-off is upfront architectural complexity, but it prevents rewrites when the confirmed field configuration changes.

### 4. Strict pre-checks before cash acceptance

Chosen to avoid unsafe scenarios where the machine can collect cash but cannot safely vend or return change. The trade-off is that some otherwise possible sales are refused earlier, but this is the correct fail-safe behavior for a production machine.

### 5. Change reservation before payment start

Chosen to minimize the risk of accepting cash that cannot later be settled safely. The trade-off is that reservation logic and reconciliation become more complex, especially when cash inventory accounting diverges from physical state.

## Bounded contexts and module boundaries

### `vending`

Owns sale lifecycle, vend authorization, product movement, delivery window coordination, anti-double-dispense rules, and sale completion semantics.

### `payments`

Owns payment sessions, cash acceptance workflow, change reservation, change payout policies, exact-change-only policies, future cashless extension points, and transaction settlement semantics.

### `inventory`

Owns product catalog, slot mapping, stock availability, slot-level sensing, inventory drift detection, and reconciliation workflows.

### `cooling`

Owns temperature monitoring, thresholds, cooling supervision, warnings, and sale-block policies for unsafe temperature states.

### `telemetry`

Owns structured logs, metrics hooks, health status publication, service audit, and error reporting.

### `devices`

Owns hardware abstraction interfaces and device-facing adapters. It does not contain business rules.

### `ui`

Owns presentation, kiosk navigation, localized messages, service screens, and interaction mapping into application commands.

### `app`

Owns orchestration across bounded contexts: command handling, workflow sequencing, FSM execution, recovery manager, health supervision, and transaction coordination.

### `infrastructure`

Owns SQLite persistence, logging backends, YAML configuration loading, serial/MDB transport implementations, OS integration, and startup bootstrap.

## Platform strategy for Linux and Windows

### Platform-neutral core

The following must remain fully platform-neutral:

- domain entities, value objects, aggregates, domain services;
- FSM definitions and transition policies;
- application orchestration and recovery logic;
- command/event contracts;
- repositories as interfaces;
- tests, mocks, and simulators.

### Platform-specific areas

#### Serial / COM access

- Windows: COM ports such as `COM3`
- Linux: device nodes such as `/dev/ttyS*` or `/dev/ttyUSB*`
- isolated behind transport adapters and device configuration

#### System service hosting

- Windows Service or equivalent wrapper
- Linux `systemd` unit
- isolated in infrastructure bootstrap and deployment packaging

#### Watchdog integration

- Windows: service monitoring / supervisor integration
- Linux: systemd watchdog or hardware watchdog device
- exposed through `WatchdogAdapter`

#### Kiosk mode

- Windows shell replacement / assigned access / startup shell strategy
- Linux compositor/window manager kiosk startup strategy
- isolated in deployment and UI host layer

#### Autostart

- Windows service/task/startup wrapper
- Linux `systemd` autostart

#### Touch and peripheral drivers

- OS and vendor driver specifics remain outside the domain and application layers

### Design rule

No business rule may branch on operating system identity. OS differences are resolved during adapter binding at bootstrap.

## Recovery strategy

### Core principle

Recovery is based on durable journal evidence, not on RAM state, last UI screen, or optimistic assumptions about what physical actions "probably" completed.

### Recovery phases

1. Startup self-test and device discovery
2. Load unresolved transactions and the transaction journal
3. Rebuild logical transaction state from journal events
4. Identify ambiguous physical side effects
5. Apply per-step recovery policy
6. Move machine into:
   - recovered operational state;
   - `RECOVERY_PENDING`;
   - `FAULT`;
   - `OUT_OF_SERVICE`

### Ambiguous action handling

If the system cannot prove whether change or product was physically dispensed, it must not assume success. Instead:

- mark the transaction for operator review or controlled recovery;
- block unsafe future actions if stock/cash integrity may be compromised;
- emit recovery journal entries and service alerts.

### Why journal-first matters

Durable intent markers let the system distinguish:

- payment accepted but vend not authorized;
- vend authorized but product result unknown;
- payout initiated but confirmation missing;
- cancellation requested but refund unresolved.

Without this, restart behavior degenerates into guesswork and creates double-dispense or double-payout risk.

## Fail-safe strategy

### Sales must be blocked when any critical precondition fails

Cash acceptance and vending are disabled when:

- the service door is open;
- critical temperature policy is violated;
- inventory is unavailable or uncertain for the selected item;
- safe change payout is unavailable for cash payment mode;
- a critical device fault exists;
- the payout path is unhealthy;
- the vend mechanism is unhealthy;
- recovery is pending on an unresolved critical transaction.

### Graceful degradation

The machine may continue operating in degraded mode when safe, for example:

- entering exact-change-only mode if change cannot be guaranteed;
- disabling only cash sales while allowing future cashless modes;
- allowing service mode diagnostics while customer mode remains locked.

### Critical design rule

No item is dispensed until payment is durably confirmed and any required change payout is durably completed or otherwise resolved by policy.

## Exact change only strategy

### When exact-change-only should be activated

The machine enters exact-change-only mode when:

- change availability falls below a configurable safe threshold;
- the payout subsystem is degraded but still safe enough to accept exact cash only;
- accounting state and physical change state are temporarily inconsistent;
- reservation simulation shows that common change cases cannot be fulfilled safely.

### Operational semantics

- The machine advertises exact-change-only in UI and health state.
- Cash purchases are allowed only when the inserted total can be accepted without requiring payout.
- Change reservation is bypassed only when the transaction requires zero change.
- If exact cash cannot be enforced safely with the validator configuration, cash sales are blocked entirely.

### Exit conditions

The machine exits exact-change-only mode only after:

- refill or reconciliation;
- successful health checks;
- policy re-evaluation proving safe payout capability.

## Why the transaction journal is the recovery foundation

The journal is the system of record for critical workflow intent and outcome because:

- power loss can occur between command issue and physical confirmation;
- UI state is not authoritative;
- device state may be unavailable or stale after reboot;
- SQLite durability is stronger and more inspectable than ad hoc in-memory checkpoints;
- journal replay enables deterministic recovery tests;
- service audit needs a trustworthy historical trail with transaction and correlation identifiers.

Each critical stage should write journal entries such as:

- purchase started;
- change reserved;
- cash session enabled;
- bill stacked;
- payment threshold reached;
- payout requested;
- payout confirmed or ambiguous;
- vend requested;
- vend confirmed or ambiguous;
- delivery window opened;
- pickup confirmed;
- transaction completed, cancelled, faulted, or sent to manual review.

## Phase outcome classification

### Fully implemented conceptually

- Layered architecture and bounded contexts
- Platform isolation strategy
- Journal-first recovery strategy
- Fail-safe sales blocking model
- Exact-change-only business strategy
- DBV-300-SD integration boundary rules

### Scaffolded

- File-based architecture baseline document
- ADR set for key architectural choices

### Requires hardware confirmation

- DBV-300-SD transport/protocol specifics
- Change dispenser device behavior and payout confirmations
- Vend motor and position sensing semantics
- Delivery window actuator timing and sensors
- Temperature sensor hardware behavior and thresholds

## ADR index for this phase

- ADR-0001: Layered architecture and bounded contexts
- ADR-0002: Journal-first transaction recovery
- ADR-0003: Cash transaction and change safety policy
- ADR-0004: Platform isolation and DBV-300-SD adapter strategy

## Assumptions

- The machine controller is a single-host PC/SBC running one main control application instance.
- SQLite local durability is acceptable for the deployment model.
- Safety-critical hard interlocks that require dedicated hardware are outside the software-only scope but the software must cooperate with them.
- The payout device provides some auditable confirmation model, even if exact protocol details are not yet known.
- The vend mechanism exposes enough sensing to distinguish at least command issued, movement attempted, and terminal result/timeout states.
- The service organization can handle a `RECOVERY_PENDING` workflow with operator intervention for ambiguous transactions.
- Future cashless payments will be added through a separate payment provider adapter without changing the domain model of transaction settlement.
