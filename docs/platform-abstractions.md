# Platform Abstractions

This project keeps platform-neutral runtime logic in the shared application
layers and exposes OS-specific deployment concerns as explicit extension points.

## Shared Across Windows and Linux

- domain entities, commands, events, and FSM;
- application orchestrators and runtime supervision loops;
- simulator devices and deterministic scenario runners;
- Qt presenter/view-model UI layer;
- SQLite persistence, journal, config validation, and logging;
- recovery and service-mode policies.

## Windows Modules

Code: `src/flower_vending/platform/windows`

Windows-specific descriptors cover:

- kiosk shell / assigned-access style integration;
- Windows Service deployment wrapper;
- autostart registration;
- watchdog heartbeat handoff to host services.

These modules intentionally describe extension points only. They do not claim
that kiosk lockdown, service registration, or watchdog deployment is already
bench-confirmed on the target machine.

## Linux Modules

Code: `src/flower_vending/platform/linux`

Linux-specific descriptors cover:

- kiosk shell / compositor or WM lockdown;
- `systemd`-oriented service abstraction;
- autostart through system service or session wiring;
- watchdog handoff to `systemd` or an external supervisor.

Again, these are extension points rather than active deployment hacks.

## Generic Profile

Code: `src/flower_vending/platform/common.py`

The generic profile is used by the simulator config and exposes:

- kiosk mode abstraction;
- autostart abstraction;
- watchdog abstraction.

This keeps simulator/runtime behavior platform-neutral while still making the
expected deployment seams visible to the next engineer.

## Why This Separation Matters

The project must not:

- hardcode Windows COM ports or Linux device nodes into the core;
- pretend OS services or kiosk lockdown are implemented when they are not;
- couple UI/domain/application logic to one target OS.

The current structure lets simulator mode mature now, while leaving the
hardware-confirmed deployment layer for a later, bench-driven phase.
