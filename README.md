# Flower Vending System

Simulator-first control platform for a flower vending machine.

This repository now supports a production-like software baseline that can be run
without real hardware:

- platform-neutral domain/application core and FSM;
- deterministic simulator devices with fault injection;
- kiosk UI wired through presenters/view-models and simulator controls;
- unified `python -m flower_vending ...` entrypoints;
- bootstrap checks, config validation, seed demo catalog, and SQLite runtime state;
- Windows/Linux platform abstraction modules with explicit extension points;
- automated tests for simulator scenarios, startup, diagnostics, service mode, and recovery-safe behavior.

Real hardware protocols are still intentionally **not claimed as complete**.
DBV-300-SD framing/commands, payout hardware, motors, sensors, watchdogs, kiosk
lockdown, services, and autostart remain extension points until bench-confirmed.

## Quick Start

Install dependencies on a clean machine:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-ui.txt
```

Optional editable install still works when backend dependencies are reachable:

```powershell
python -m pip install -e ".[dev,ui]"
```

Validate config and prepare runtime directories:

```powershell
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
```

Run the simulator runtime:

```powershell
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml
```

Open diagnostics:

```powershell
python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
```

Open service mode snapshot:

```powershell
python -m flower_vending service --config config\examples\machine.simulator.yaml
```

Launch the simulator UI:

```powershell
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml
```

## Desktop Releases

End users do not need to install Python for packaged desktop builds.

Windows release outputs:

- `FlowerVendingSimulator-Windows-x64.exe` - portable single-file app with bundled Python runtime;
- `FlowerVendingSimulator-Setup-Windows-x64.exe` - optional installer build for desktop deployment.

Linux release outputs:

- `FlowerVendingSimulator-Linux-x86_64.AppImage` - single-file Linux desktop app;
- `FlowerVendingSimulator-Linux-x86_64.tar.gz` - fallback self-contained bundle.

Build locally:

```powershell
scripts\build-windows-release.bat
```

```bash
./scripts/build-linux-release.sh /path/to/appimagetool
```

GitHub release automation is prepared in `.github/workflows/build-release.yml`.
Pushing a tag like `v0.1.0` builds Windows and Linux artifacts and publishes them
to GitHub Releases.

Windows convenience scripts:

```powershell
scripts\validate-config.bat
scripts\run-simulator-runtime.bat
scripts\run-diagnostics.bat
scripts\run-service-mode.bat
scripts\run-simulator-ui.bat
```

Linux convenience scripts:

```bash
./scripts/validate-config.sh
./scripts/run-simulator-runtime.sh
./scripts/run-diagnostics.sh
./scripts/run-service-mode.sh
./scripts/run-simulator-ui.sh
```

## Verification

Run the full verification helper:

```powershell
python scripts\verify_project.py
```

This verifies:

- config validation;
- compile step;
- unit/integration/recovery tests;
- diagnostics mode smoke test;
- focused runtime scenarios.

## Simulator UX

The simulator UI and service mode support:

- browse catalog and product cards;
- start cash checkout;
- quick-insert bills from the payment screen;
- open/close service door;
- raise/restore temperature;
- trigger bill rejected / bill jam / validator unavailable;
- trigger payout unavailable / partial payout;
- trigger motor fault;
- trigger inventory mismatch;
- explicit pickup-timeout placeholder warning.

Recent domain events are visible in diagnostics, and runtime logs include FSM
transitions plus correlation/transaction identifiers.

## Documentation

- [Operations Runbook](docs/operations-runbook.md)
- [Platform Abstractions](docs/platform-abstractions.md)
- [Project Documentation (RU)](docs/project-documentation-ru.md)
- [User Guide (RU)](docs/user-guide-ru.md)
- [Technical Guide (RU)](docs/technical-guide-ru.md)

## Hardware-Dependent Gaps

The following still require target hardware confirmation:

- real DBV-300-SD protocol commands and transport timings;
- real payout hardware integration and physical reconciliation;
- motor/controller protocol details and sensor feedback;
- kiosk shell lockdown on Windows/Linux;
- OS service, autostart, and watchdog deployment wiring;
- pickup-timeout automation beyond the current explicit placeholder.
