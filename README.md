# Flower Vending System

Simulator-first control platform для flower vending machine.

Проект уже содержит production-like software baseline, который можно запускать
без реального железа:

- platform-neutral domain/application core и FSM;
- deterministic simulator devices с fault injection;
- kiosk UI через presenters/view-models и simulator controls;
- единые entrypoints через `python -m flower_vending ...`;
- bootstrap checks, config validation, seed demo catalog и SQLite runtime state;
- Windows/Linux platform abstraction modules с явными extension points;
- automated tests для simulator scenarios, startup, diagnostics, service mode и
  recovery-safe behavior.

Реальные hardware protocols пока **не считаются завершёнными**. DBV-300-SD
framing/commands, payout hardware, motors, sensors, watchdogs, kiosk lockdown,
services и autostart остаются extension points до bench confirmation. Граница
готовности описана в [Production Readiness Boundary](docs/overview/production-readiness.md).

## Быстрый Старт

Установить зависимости:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-ui.txt
```

Опционально можно поставить editable install:

```powershell
python -m pip install -e ".[dev,ui]"
```

Проверить config и подготовить runtime directories:

```powershell
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
```

Запустить simulator runtime:

```powershell
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml
```

Открыть diagnostics:

```powershell
python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
```

Открыть service mode snapshot:

```powershell
python -m flower_vending service --config config\examples\machine.simulator.yaml
```

Запустить simulator UI:

```powershell
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml
```

Очистить persisted demo SQLite database и сразу запустить UI:

```powershell
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml --reset-state
```

## Desktop Releases

Для packaged desktop builds пользователю не нужен установленный Python.

Windows release outputs:

- `FlowerVendingSimulator-Windows-x64.exe` - portable single-file app с bundled
  Python runtime;
- `FlowerVendingSimulator-Setup-Windows-x64.exe` - installer build для desktop
  deployment.

Linux release outputs:

- `FlowerVendingSimulator-Linux-x86_64.AppImage` - single-file Linux desktop app;
- `FlowerVendingSimulator-Linux-x86_64.tar.gz` - fallback self-contained bundle.

Собрать локально:

```powershell
scripts\build-windows-release.bat
```

```bash
./scripts/build-linux-release.sh /path/to/appimagetool
```

GitHub release automation находится в `.github/workflows/build-release.yml`.
Push tag вида `v0.1.5` собирает Windows/Linux artifacts и публикует их в
GitHub Releases.

## Unified CLI

Use direct `python -m flower_vending ...` commands for simulator workflows.
They work the same way on Windows and Linux, with only path separators changed
for the host shell.

```powershell
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml
python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
python -m flower_vending status --config config\examples\machine.simulator.yaml --json
python -m flower_vending events --config config\examples\machine.simulator.yaml --limit 20
python -m flower_vending service --config config\examples\machine.simulator.yaml
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml --reset-state
```

Linux equivalent:

```bash
python -m flower_vending validate-config --config config/examples/machine.simulator.yaml --prepare
python -m flower_vending simulator-runtime --config config/examples/machine.simulator.yaml
python -m flower_vending diagnostics --config config/examples/machine.simulator.yaml
python -m flower_vending status --config config/examples/machine.simulator.yaml --json
python -m flower_vending events --config config/examples/machine.simulator.yaml --limit 20
python -m flower_vending service --config config/examples/machine.simulator.yaml
python -m flower_vending simulator-ui --config config/examples/machine.simulator.yaml
python -m flower_vending simulator-ui --config config/examples/machine.simulator.yaml --reset-state
```

## Verification

Запустить весь simulator-safe verification suite:

```powershell
python scripts\verify_project.py
```

Verifier проверяет:

- config validation для simulator, Windows, Linux и Debian target YAML files;
- CLI help smoke checks для всех unified entrypoints;
- compile step;
- pytest-based unit/integration/recovery tests;
- UI smoke check;
- diagnostics mode smoke test;
- focused runtime scenarios.

## Simulator UX

Simulator UI и service mode поддерживают:

- русский demo catalog с product cards и локальными flower images;
- cash checkout;
- quick-insert bills на payment screen;
- open/close service door;
- raise/restore temperature;
- bill rejected / bill jam / validator unavailable faults;
- payout unavailable / partial payout faults;
- motor fault;
- inventory mismatch;
- forced pickup timeout, который закрывает delivery window и переводит систему в
  recovery/manual review.

Recent domain events видны в diagnostics. Runtime logs содержат FSM transitions,
correlation identifiers и transaction identifiers.

Demo catalog в `config/examples/machine.simulator.yaml` использует локальные
assets из `src/flower_vending/ui/assets/products/`; release packaging включает
эти assets для Windows и Linux builds.

Если UI показывает старый persisted demo catalog, запусти UI с `--reset-state`.
Это очистит simulator database и поднимет storefront UI с актуальным demo catalog.

## Документация

- [Docs Index](docs/README.md)
- [Production Readiness Boundary](docs/overview/production-readiness.md)
- [Operations Runbook](docs/operations/runbook.md)
- [Platform Abstractions](docs/architecture/platform-abstractions.md)
- [Project Documentation (RU)](docs/ru/project-documentation.md)
- [User Guide (RU)](docs/ru/user-guide.md)
- [Developer Guide (RU)](docs/ru/developer-guide.md)
- [Technical Guide (RU)](docs/ru/technical-guide.md)
- [Hardware Bench Validation Checklist](docs/hardware/bench-validation-checklist.md)
- [Debian 13 Target Hardware Assessment](docs/hardware/debian13-target-assessment.md)
- [План будущих запросов](docs/overview/future-requests-plan.txt)

## Hardware-Dependent Gaps

Следующее требует target hardware confirmation:

- DBV-300-SD command frames, acknowledgements, denomination/event mapping,
  escrow behavior, transport timings и restart recovery;
- real payout hardware integration, physical reconciliation, partial-payout
  evidence и cash accounting procedures;
- motor/controller protocol details, home/jam feedback и product-drop
  confirmation;
- physical delivery-window и pickup confirmation sensors сверх simulator-safe
  pickup timeout coordinator;
- temperature, door, inventory и position sensor calibration на target cabinet;
- kiosk shell lockdown на target Windows/Linux image;
- OS service, autostart и watchdog deployment wiring.

## Куда Двигаться Дальше

Короткий порядок развития:

1. Усилить packaging versioning и release docs.
2. Добавить Windows/Linux simulator-safe CI matrix.
3. Улучшить simulator UI fault/service states.
4. Реальное железо подключать только после bench inventory и bench validation.
