# Flower Vending System: руководство разработчика

## 1. Назначение проекта

Проект представляет собой simulator-first программную платформу для цветочного автомата.

Цель текущего состояния:

- дать исполняемый baseline без реального железа;
- сохранить platform-neutral архитектуру;
- развивать UI, orchestration, FSM, payment flow, diagnostics и recovery-safe поведение;
- оставить hardware-dependent части как корректные extension points.

Проект **не должен** делать вид, что реальная интеграция с DBV-300-SD, узлом сдачи, моторами и датчиками уже готова, если этого нет на стенде.

## 2. Что сейчас реально работает

На текущий момент подтверждено:

- `python -m flower_vending` CLI с командами `validate-config`, `diagnostics`, `service`, `simulator-runtime`, `simulator-ui`;
- simulator runtime environment;
- SQLite persistence baseline;
- config validation и bootstrap checks;
- deterministic simulator devices;
- UI facade, presenters, view-models и kiosk window;
- tests: unit, integration, recovery, runtime modes, simulator scenarios;
- release scaffolding для Windows и Linux.

Фактически это уже не “архитектурная болванка”, а рабочая software-only платформа.

## 3. Ключевые каталоги

- `src/flower_vending/domain` — сущности, value objects, domain events, commands и инварианты.
- `src/flower_vending/app` — application core, orchestrators, FSM, coordination.
- `src/flower_vending/simulators` — mock devices, control plane, fault injection, scenario flows.
- `src/flower_vending/ui` — facade, presenters, view-models, Qt views.
- `src/flower_vending/infrastructure` — config, logging, journal, SQLite persistence.
- `src/flower_vending/runtime` — bootstrap, CLI, path resolution, packaged launcher.
- `src/flower_vending/platform` — platform abstraction и extension points Windows/Linux.
- `config/examples` — simulator, windows и linux примеры конфигов.
- `tests` — автоматические проверки.
- `scripts` — локальный запуск, валидация, релизные сценарии, verification.
- `docs` — проектная и эксплуатационная документация.

## 4. Как устроен запуск

Основная точка входа:

```powershell
python -m flower_vending
```

CLI определен в [src/flower_vending/runtime/cli.py](/C:/Users/User/Desktop/flower-vending-system/src/flower_vending/runtime/cli.py).

Главные команды:

- `validate-config` — проверка YAML и bootstrap checks;
- `diagnostics` — запуск среды и печать диагностики;
- `service` — вход в service mode и получение service snapshot;
- `simulator-runtime` — runtime без UI или запуск детерминированных сценариев;
- `simulator-ui` — kiosk UI.

Bootstrap и сборка runtime происходят в [src/flower_vending/runtime/bootstrap.py](/C:/Users/User/Desktop/flower-vending-system/src/flower_vending/runtime/bootstrap.py).

## 5. Как проверить проект после изменений

Минимальная обязательная проверка:

```powershell
python scripts\verify_project.py
```

Скрипт запускает:

- `validate-config`;
- `compileall`;
- `unittest discover -s tests -t tests -q`;
- diagnostics smoke test;
- focused runtime scenarios.

Если хотите запускать части вручную:

```powershell
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
python -m unittest discover -s tests -t tests -q
python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml
```

## 6. Текущее состояние качества

Сильные стороны проекта:

- хорошая модульность;
- separation of concerns;
- единые entrypoints;
- симуляторы и fault injection;
- tests на ключевые сценарии;
- release/build scaffolding;
- documentation coverage;
- Windows/Linux стратегия без вшивания платформы в core.

Что пока ограничивает production readiness:

- нет реальных протоколов DBV-300-SD;
- нет подтвержденного payout hardware flow;
- нет реальных sensor/motor adapters;
- нет полного bench-validated recovery на настоящем железе;
- `pickup timeout` реализован в simulator-safe runtime через coordinator и требует реальный датчик позже;
- kiosk lockdown, autostart и watchdog не доведены до production wiring.

## 7. Что можно менять безопасно без железа

Безопасно развивать:

- UI;
- presenters и view-models;
- runtime UX;
- simulator controls;
- config validation;
- diagnostics mode;
- service mode;
- event visualization;
- logging;
- persistence scaffolding;
- seed data;
- сценарии тестов и simulator flows;
- Windows/Linux packaging и launch scripts.

## 8. Что нельзя выдумывать

Без документации и стенда нельзя:

- придумывать бинарные команды DBV-300-SD;
- объявлять готовой работу через COM3 только потому, что порт указан в config;
- симулировать “как будто точно так работает железо” там, где поведение не подтверждено;
- прошивать business logic под конкретный transport;
- выдавать simulator adapter за production adapter.

## 9. Как правильно добавлять новый код

Рекомендуемый порядок:

1. Сначала определить, в каком слое находится новая логика.
2. Если это бизнес-правило — класть в `domain` или `app`.
3. Если это device contract или adapter boundary — класть в `devices` или `platform`.
4. Если это только simulator-specific поведение — класть в `simulators`.
5. Если это только отображение — класть в `ui`.
6. Если это persistence/config/logging — класть в `infrastructure`.
7. После изменений добавлять тест и прогонять `verify_project.py`.

## 10. Как читать проект новому разработчику

Рекомендуемый порядок входа:

1. [README.md](/C:/Users/User/Desktop/flower-vending-system/README.md)
2. [docs/operations-runbook.md](/C:/Users/User/Desktop/flower-vending-system/docs/operations-runbook.md)
3. [docs/project-documentation-ru.md](/C:/Users/User/Desktop/flower-vending-system/docs/project-documentation-ru.md)
4. [src/flower_vending/runtime/cli.py](/C:/Users/User/Desktop/flower-vending-system/src/flower_vending/runtime/cli.py)
5. [src/flower_vending/runtime/bootstrap.py](/C:/Users/User/Desktop/flower-vending-system/src/flower_vending/runtime/bootstrap.py)
6. [tests/integration/test_runtime_modes.py](/C:/Users/User/Desktop/flower-vending-system/tests/integration/test_runtime_modes.py)
7. [tests/integration/test_simulator_scenarios.py](/C:/Users/User/Desktop/flower-vending-system/tests/integration/test_simulator_scenarios.py)

Так быстрее всего понять реальный исполняемый контур проекта.

## 11. Что я бы рекомендовал делать дальше

Приоритетный roadmap без реального железа:

- улучшить simulator UI и сценарии демонстрации;
- сделать более чистый пользовательский event log в diagnostics;
- добавить export/import demo state;
- добавить smoke test для UI запуска;
- улучшить release notes и версионирование артефактов;
- формализовать developer onboarding;
- подготовить integration harness для будущего bench testing;
- затем отдельно переходить к hardware-confirmed adapters.
