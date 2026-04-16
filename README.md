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
готовности описана в [Production Readiness Boundary](docs/production-readiness.md).

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
Push tag вида `v0.1.3` собирает Windows/Linux artifacts и публикует их в
GitHub Releases.

Windows convenience scripts:

```powershell
scripts\validate-config.bat
scripts\run-simulator-runtime.bat
scripts\run-diagnostics.bat
scripts\run-service-mode.bat
scripts\run-simulator-ui.bat
scripts\reset-demo-and-run-ui.bat
```

Linux convenience scripts:

```bash
./scripts/validate-config.sh
./scripts/run-simulator-runtime.sh
./scripts/run-diagnostics.sh
./scripts/run-service-mode.sh
./scripts/run-simulator-ui.sh
```

Эти convenience scripts постепенно стоит заменять прямыми командами
`python -m flower_vending ...`, если они не дают platform-specific пользы.

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

- [Production Readiness Boundary](docs/production-readiness.md)
- [Operations Runbook](docs/operations-runbook.md)
- [Platform Abstractions](docs/platform-abstractions.md)
- [Project Documentation (RU)](docs/project-documentation-ru.md)
- [User Guide (RU)](docs/user-guide-ru.md)
- [Developer Guide (RU)](docs/developer-guide-ru.md)
- [Technical Guide (RU)](docs/technical-guide-ru.md)
- [Debian 13 Target Hardware Assessment](docs/hardware/debian13-target-assessment.md)
- [План будущих запросов](docs/future-requests-plan.txt)

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

1. Привести docs в порядок: `docs/README.md`, `docs/architecture/`,
   `docs/operations/`, `docs/hardware/`, `docs/ru/`.
2. Убрать thin `.bat/.sh` wrappers после перевода README/docs на
   `python -m flower_vending`.
3. Проверить `sitecustomize.py` и root `flower_vending/` shim.
4. Добавить operator diagnostics: `status --json` и `events --limit N`.
5. Усилить packaging versioning и release docs.
6. Добавить Windows/Linux simulator-safe CI matrix.
7. Реальное железо подключать только после bench inventory и bench validation.
