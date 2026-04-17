# Flower Vending System: техническая документация

## 1. Цель текущего baseline

Проект доведен до состояния simulator-first desktop platform, которую можно:

- развернуть на чистой машине;
- запустить без установленного Python у конечного пользователя;
- использовать как kiosk-like UI для демонстрации и тестов;
- передать другому разработчику с предсказуемой структурой и запуском.

При этом hardware-dependent интеграции намеренно оставлены extension points и не
выдаются за подтвержденную готовность.

## 2. Архитектурные слои

- `domain` — сущности, value objects, commands, events, инварианты;
- `app` — orchestrators, FSM, startup flow, runtime coordination;
- `simulators` — deterministic mocks, control plane, сценарии и fault injection;
- `ui` — presenter/view-model слой и Qt views;
- `infrastructure` — config, logging, persistence, journal, bootstrap helpers;
- `platform` — общие и platform-specific extension points Windows/Linux;
- `runtime` — CLI, packaged launcher, path resolution, bootstrap sequence.

Ключевой принцип: UI не ходит напрямую в hardware adapters, а real-hardware
протоколы не моделируются как “готовые”.

## 3. Entry points

Поддерживаются единые режимы запуска:

- `python -m flower_vending validate-config`
- `python -m flower_vending simulator-runtime`
- `python -m flower_vending diagnostics`
- `python -m flower_vending service`
- `python -m flower_vending simulator-ui`

Для packaged desktop-сборки используется отдельный GUI entrypoint:

- `flower_vending.runtime.product_launcher`

Этот launcher автоматически:

- определяет resource root внутри bundled приложения;
- переносит writable state в пользовательский каталог;
- копирует документацию в state root;
- запускает simulator UI с bundled config.

## 4. Runtime и packaged path model

В `flower_vending.runtime.paths` разделены два понятия:

- `bundle_root()` — откуда читать встроенные resources;
- `state_root()` — куда писать базу, логи и runtime-состояние.

Это нужно для корректной desktop-дистрибуции:

- Windows portable `.exe` нельзя заставлять писать рядом с собой;
- Linux `AppImage` тоже должен считать себя read-only bundle;
- относительные пути к SQLite и логам должны резолвиться в user-state area.

Текущие каталоги состояния:

- Windows: `%LOCALAPPDATA%\FlowerVendingSystem`
- Linux: `~/.local/state/flower-vending-system`

## 5. Packaging strategy

### Windows

Используется `PyInstaller --onefile --windowed`.

Выходные артефакты:

- `FlowerVendingSimulator-Windows-x64.exe` — portable build с bundled Python runtime;
- `FlowerVendingSimulator-Setup-Windows-x64.exe` — базовый setup-installer через Inno Setup.

### Linux

Используется `PyInstaller --onedir --windowed`, затем staging в `AppDir`.

Выходные артефакты:

- `FlowerVendingSimulator-Linux-x86_64.AppImage`
- `FlowerVendingSimulator-Linux-x86_64.tar.gz`

`tar.gz` остается резервным вариантом на случай, если на целевой Linux-системе
есть ограничения для `AppImage`.

## 6. Скрипты и automation

Для локальной сборки добавлены:

- `scripts/build-windows-release.bat`
- `scripts/build-linux-release.sh`
- `packaging/build_release.py`

Для GitHub Releases добавлен workflow:

- `.github/workflows/build-release.yml`

Pipeline:

- собирает Windows portable `.exe`;
- собирает Windows installer `.exe`;
- собирает Linux `AppImage` и `tar.gz`;
- прикладывает артефакты к GitHub Actions artifacts;
- при tag push `v*` публикует GitHub Release.

## 7. Локальная сборка

Windows:

```powershell
python -m pip install -r requirements-ui.txt pyinstaller
python packaging\build_release.py windows-portable
python packaging\build_release.py windows-installer
```

Linux:

```bash
python -m pip install -r requirements-ui.txt pyinstaller
python packaging/build_release.py linux-appimage --appimagetool /path/to/appimagetool
```

## 8. Что считается подтвержденным

Подтверждено в software-only контуре:

- локальный запуск;
- simulator UI;
- сервисный режим;
- diagnostics mode;
- deterministic simulator scenarios;
- packaged desktop delivery;
- docs/runbook/release scaffolding;
- tests без реального железа.

## 9. Что остается hardware-dependent

Не подтверждено и не должно интерпретироваться как готовое:

- реальный протокол DBV-300-SD;
- реальная выдача сдачи;
- реальные драйверы двигателя и датчиков;
- production kiosk lock-down;
- production service/daemon registration;
- production watchdog wiring;
- bench-confirmed pickup timeout behavior.
