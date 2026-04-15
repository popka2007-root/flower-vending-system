# Flower Vending System: Operations Runbook

This runbook describes how to install, verify, and operate the simulator-safe
runtime on Windows or Linux without real vending hardware.

## 1. What Is Runnable Right Now

You can run all of the following today:

- config validation and bootstrap checks;
- simulator runtime;
- simulator kiosk UI;
- diagnostics mode;
- service mode;
- deterministic simulator scenarios;
- automated tests and verification script.

You should **not** claim that the following are ready without hardware
confirmation:

- DBV-300-SD production protocol behavior;
- payout hardware integration;
- motor/controller protocol details;
- real watchdog deployment;
- Windows/Linux kiosk lockdown and service installation;
- automated pickup timeout closure beyond the explicit placeholder.

## 2. Clean-Machine Setup

Base dependencies:

```powershell
python -m pip install -r requirements.txt
```

Development and tests:

```powershell
python -m pip install -r requirements-dev.txt
```

UI runtime:

```powershell
python -m pip install -r requirements-ui.txt
```

Optional editable install:

```powershell
python -m pip install -e ".[dev,ui]"
```

## 3. Validate the Simulator Config

Windows:

```powershell
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
```

Linux:

```bash
python -m flower_vending validate-config --config config/examples/machine.simulator.yaml --prepare
```

This command:

- validates the YAML schema;
- verifies scenario names;
- creates runtime directories such as `var/data` and `var/log`;
- reports any hardware-confirmation warnings for non-simulator configs.

## 4. Launch Modes

### Simulator Runtime

```powershell
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml
```

For deterministic scenarios:

```powershell
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml --scenario normal_sale --scenario partial_payout
```

Or use the suite defined in config:

```powershell
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml --use-config-scenarios
```

### Diagnostics Mode

```powershell
python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
```

### Service Mode

```powershell
python -m flower_vending service --config config\examples\machine.simulator.yaml
```

Apply a simulator fault before printing the snapshot:

```powershell
python -m flower_vending service --config config\examples\machine.simulator.yaml --action open_service_door --action inject_motor_fault
```

### Simulator UI

```powershell
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml
```

## 5. Convenience Scripts

Windows:

- `scripts\validate-config.bat`
- `scripts\run-simulator-runtime.bat`
- `scripts\run-diagnostics.bat`
- `scripts\run-service-mode.bat`
- `scripts\run-simulator-ui.bat`

Linux:

- `./scripts/validate-config.sh`
- `./scripts/run-simulator-runtime.sh`
- `./scripts/run-diagnostics.sh`
- `./scripts/run-service-mode.sh`
- `./scripts/run-simulator-ui.sh`

## 6. UI Scenarios You Can Walk Through

Without real hardware, the UI still supports:

- main screen and catalog browsing;
- product card;
- payment screen;
- exact-change-only advisory;
- no-change screen;
- dispensing screen;
- pickup screen;
- error screen;
- service screen;
- diagnostics screen;
- recovery/restricted mode screen.

Simulator-specific controls let you:

- insert bills from the payment screen;
- open or close the service door;
- raise or normalize temperature;
- inject bill rejected / bill jam / validator unavailable;
- inject payout unavailable / partial payout;
- inject motor fault;
- inject inventory mismatch;
- trigger the explicit pickup-timeout placeholder warning.

## 7. Verification

Run:

```powershell
python scripts\verify_project.py
```

Current verification includes:

- config validation;
- compile step;
- unittest suite;
- diagnostics mode smoke test;
- focused runtime scenarios.

## 8. Logs and Persistence

Default simulator artifacts:

- database: `var/data/flower_vending_simulator.db`
- logs: `var/log/flower_vending.simulator.jsonl`

Runtime state now persists:

- seeded catalog and money inventory;
- machine status projection;
- transaction journal entries;
- transaction snapshots for unresolved flows;
- service and temperature events;
- applied config snapshots.

## 9. Platform Split

See [Platform Abstractions](platform-abstractions.md).

In short:

- `src/flower_vending/platform/common.py` describes shared cross-platform seams;
- `src/flower_vending/platform/windows/` models Windows service/kiosk/watchdog extension points;
- `src/flower_vending/platform/linux/` models Linux/systemd/kiosk/watchdog extension points.

## 10. Troubleshooting

If `python -m flower_vending ...` fails:

- run commands from the repository root;
- install base dependencies from `requirements.txt`;
- if UI is missing, install `requirements-ui.txt`.

If diagnostics/service modes print JSON logs to stderr:

- that is expected when `logging.stderr: true`;
- logs are also written to the configured log directory.

If a simulator run stays blocked:

- open diagnostics or service mode;
- inspect `sale_blockers`;
- clear injected faults or close the service door;
- remember that pickup timeout is still a placeholder and does not auto-close the window.

If a non-simulator config looks runnable:

- treat it as a deployment template only;
- extension points remain hardware-dependent until bench-confirmed.
