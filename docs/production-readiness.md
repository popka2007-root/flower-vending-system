# Production Readiness Boundary

This project is currently a simulator-ready software baseline. It is not yet a
production-hardware-ready vending machine controller.

The simulator proves the application workflow, UI, persistence, recovery
handling, and device-contract boundaries without real hardware. A pilot on a
real vending machine requires bench evidence for every physical device adapter,
measured timings, operator procedures, and a release gate review.

## Simulator-ready capabilities

- Platform-neutral domain/application core, FSM, event bus, command bus, and
  journal-backed recovery patterns.
- Deterministic simulator devices implementing the same contracts expected from
  hardware adapters.
- Simulator runtime, diagnostics, service mode, and kiosk UI entrypoints.
- Simulator controls for bill insertion, service door, temperature, payout
  faults, motor faults, inventory mismatch, and pickup-timeout forcing.
- Pickup timeout handling in the simulator-safe runtime: when pickup is not
  confirmed before the deadline, the window is closed, sales are blocked, and
  manual review is required.
- Tests for simulator scenarios, cash flows, pickup timeout, UI presenters,
  runtime modes, recovery, config validation, and protocol scaffolding.
- Packaged desktop simulator builds for Windows and Linux.

These capabilities are suitable for software demos, operator walkthroughs,
developer handoff, and regression testing without connected vending hardware.

## Hardware integration pending

The following are not production-hardware-ready until bench-confirmed:

- DBV-300-SD command frames, acknowledgements, event mapping, denomination
  mapping, escrow behavior, timeouts, retry policy, and recovery after transport
  loss.
- Real payout hardware, physical coin/note reconciliation, partial-payout
  evidence, and accounting reconciliation.
- Vend motor or carousel adapter, home sensor behavior, jam detection, product
  drop confirmation, and ambiguous vend recovery.
- Delivery window actuator, lock state, obstruction handling, and physical
  open/closed confirmation.
- Physical pickup confirmation. The current timeout coordinator is useful in
  the simulator but does not prove that a customer took the product.
- Temperature, door, inventory, and position sensors on the target cabinet.
- Production watchdog, OS service/daemon registration, autostart, and kiosk
  lockdown on the target Windows/Linux image.
- Cabinet-level safety interlocks, emergency stop behavior, and local
  regulatory requirements.

## Device readiness table

| device | current implementation | simulator coverage | real adapter status | required bench evidence |
| --- | --- | --- | --- | --- |
| Bill validator / DBV-300-SD | Domain-facing adapter, serial transport scaffold, deferred serial/MDB/pulse protocols, and bench-only serial smoke CLI. | Mock validator supports accepted/rejected/stacked/fault flows in simulator scenarios. | Not ready. Protocol commands intentionally deferred until vendor docs or traces exist. | Confirm physical mode, serial/MDB parameters, startup handshake, enable/disable, polling/push model, denominations, escrow, faults, reset behavior, rx/tx traces, and measured timeouts. |
| Change dispenser / payout | Contract and simulator dispenser with can-dispense/dispense results. | Full, partial, unavailable, and inventory-based payout flows. | Not ready. No real payout driver or physical reconciliation. | Device command set, denomination mapping, cassette inventory readback, successful/partial/failed payout captures, accounting reconciliation, restart-after-payout ambiguity handling. |
| Vend motor or carousel | Contract and simulator motor controller. | Normal vend and motor fault scenarios. | Not ready. No target controller protocol or movement feedback. | Home sequence, vend-slot command timing, jam/overcurrent/timeout behavior, product-present/drop evidence, recovery after restart during motion. |
| Delivery window actuator | Contract and simulator window controller. | Open/close flows, close failure, and pickup-timeout closure. | Not ready. No physical actuator, lock, obstruction, or position adapter. | Open/close timing, lock state, obstruction handling, position sensor agreement, close failure behavior, safe retry limits. |
| Pickup confirmation | Simulated by UI/customer action plus timeout coordinator. | Confirm-pickup and timeout/manual-review paths are covered. | Not ready. No physical pickup sensor or camera/weight/beam adapter. | Sensor choice, false positive/negative rate, customer-took-product evidence, timeout threshold, recovery procedure when pickup is ambiguous. |
| Service door sensor | Contract and simulator door sensor. | Door-open blocker and service-mode flows. | Not ready. No cabinet sensor binding. | Open/closed electrical behavior, debounce, tamper cases, startup state, service-door-open sale blocking. |
| Inventory sensor | Contract and simulator inventory sensor. | Inventory mismatch and slot presence flows. | Not ready. No real slot sensor mapping. | Per-slot calibration, confidence thresholds, refill procedure, mismatch recovery, stale sensor handling. |
| Position sensor | Contract and simulator position sensor. | Basic position readings for simulator health. | Not ready. No real home/position sensor binding. | Home/reference behavior, movement-in-progress readings, mismatch/jam detection, restart state reconstruction. |
| Temperature sensor | Contract and simulator temperature sensor. | Critical-temperature blocker and restore flows. | Not ready. No real chamber sensor binding. | Sensor calibration, polling interval, out-of-range behavior, startup reading, cooling-fault correlation. |
| Cooling controller | Contract and simulator cooling controller. | Enable/disable and temperature-related health flows. | Not ready. No compressor/controller adapter. | Target temperature command behavior, compressor protection delays, fault reporting, recovery after power loss, safe defaults. |
| Watchdog adapter | Contract and simulator watchdog adapter. | Runtime health loop can use the simulator watchdog path. | Not ready. No production OS/hardware watchdog wiring. | Arm/kick/disarm behavior, process crash response, boot recovery, service integration, false reset avoidance. |
| Kiosk shell / autostart | Platform extension points and packaged simulator launcher. | Simulator UI can run windowed or kiosk-like locally. | Not ready. Target OS lockdown and service/autostart are not confirmed. | Boot-to-app, user escape prevention, update/maintenance path, crash restart, log access, remote or local service procedure. |

## Bench validation checklist

Before any real adapter is marked pilot-ready, capture and store:

- device model, firmware, wiring, power supply, and controller/bridge details;
- configuration used for the run, including ports, baud rates, addresses,
  timeouts, retry counts, and feature flags;
- timestamped command/response traces for startup, normal operation, faults,
  shutdown, and restart/recovery;
- physical observations linked to correlation ids in logs;
- measured timing ranges for every command and event used by the software;
- negative cases: unplug/replug, power cycle, jam, empty inventory, full
  cassette, door open, sensor mismatch, and interrupted transaction;
- operator actions needed to reconcile cash, product, and machine state;
- automated or manual test results showing that simulator assumptions still
  match the hardware contract.

DBV-300-SD work should follow `docs/hardware/dbv300sd-bench-plan.md`.

## Release gate

Current status: the project can be treated as a simulator release candidate.
It cannot be treated as a real-machine pilot release until the pilot gate below
is satisfied.

### Simulator release

A simulator release can be shipped when:

- `python scripts\verify_project.py` passes on the release machine or CI;
- packaged simulator artifacts start successfully on target desktop OSes;
- README and release notes describe the build as simulator-safe, not
  hardware-ready;
- known hardware-dependent gaps remain visible in this document and README.

### Pilot release

A pilot release for a real vending machine is not approved until:

- every enabled hardware adapter in the deployment config has bench evidence;
- unbenchmarked devices are disabled or replaced with explicit simulator-only
  modes that cannot collect customer cash;
- DBV-300-SD, payout, motor, window, pickup, and sensor behavior have measured
  timing and recovery rules;
- service/autostart/watchdog/kiosk behavior is validated on the target OS image;
- operator runbooks cover restocking, cash reconciliation, pickup timeout,
  payout ambiguity, vend ambiguity, faults, log collection, and safe shutdown;
- a manual safety review confirms that software behavior cooperates with
  cabinet-level interlocks and emergency procedures;
- the release owner signs off that simulator evidence is not being used as a
  substitute for bench evidence.

## Known safety limitations

- The software cannot by itself guarantee physical safety. Hard interlocks,
  emergency stop, fusing, door locks, and motion/cooling protection must be
  implemented and validated at cabinet/hardware level.
- Simulator success does not prove real device timing, electrical behavior,
  mechanical reliability, or sensor accuracy.
- Cash acceptance must not be enabled on real hardware until refund/escrow,
  payout, and manual reconciliation behavior are bench-confirmed.
- If payout or vend completion is ambiguous, the software must preserve the
  journal state and require manual review rather than assuming success.
- Pickup timeout currently closes the simulated delivery window and blocks sales
  for review. It does not prove whether a real customer removed the product.
- Production kiosk lockdown, watchdog restart behavior, and OS service recovery
  are pending target-system validation.

## Operator/service requirements

A real pilot needs documented operator procedures for:

- daily startup and shutdown checks;
- cabinet inspection, restocking, and inventory reconciliation;
- cash cassette/coin hopper refill, removal, and accounting reconciliation;
- manual review of unresolved transactions, pickup timeouts, partial payouts,
  vend failures, and sensor mismatches;
- clearing bill jams, payout jams, delivery-window faults, and motor faults;
- collecting logs and bench traces without losing transaction evidence;
- updating configuration and software packages with rollback steps;
- disabling sales when any hardware adapter reports unconfirmed, ambiguous, or
  degraded physical state;
- emergency stop and safe power-off procedures owned by the cabinet design.
