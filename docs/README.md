# Документация Flower Vending System

Эта папка разделена по слоям, чтобы документацию было проще читать и
поддерживать. Проект остается simulator-first: software baseline можно проверять
без железа, а hardware readiness подтверждается отдельно на bench stand.

## Основные Разделы

- [Overview](overview/) - текущий статус проекта, production-readiness boundary,
  cleanup audit и план будущих запросов.
- [Operations](operations/) - запуск, verification, troubleshooting и
  эксплуатационные процедуры simulator-safe runtime.
- [Architecture](architecture/) - platform abstractions и исторические phase
  docs по архитектуре.
- [Hardware](hardware/) - bench checklist, DBV bench plan, target assessment и
  hardware-dependent ограничения.
- [ADR](adr/) - отдельный слой архитектурных решений.
- [RU](ru/) - русскоязычные guides и handoff documentation.

## Быстрый Маршрут

1. Для понимания текущей границы готовности начни с
   [production-readiness](overview/production-readiness.md).
2. Для запуска и проверки используй [operations runbook](operations/runbook.md).
3. Для архитектуры смотри [platform abstractions](architecture/platform-abstractions.md)
   и [phase history](architecture/phase-history/).
4. Для русскоязычной передачи проекта используй
   [project documentation](ru/project-documentation.md).
5. Для следующих задач смотри [future requests plan](overview/future-requests-plan.txt).

## Mapping Старых Путей

| Старый файл | Новый раздел |
| --- | --- |
| `docs/production-readiness.md` | `docs/overview/production-readiness.md` |
| `docs/operations-runbook.md` | `docs/operations/runbook.md` |
| `docs/platform-abstractions.md` | `docs/architecture/platform-abstractions.md` |
| `docs/phase-01-architecture.md` | `docs/architecture/phase-history/phase-01-architecture.md` |
| `docs/phase-02-project-structure.md` | `docs/architecture/phase-history/phase-02-project-structure.md` |
| `docs/phase-03-domain-fsm.md` | `docs/architecture/phase-history/phase-03-domain-fsm.md` |
| `docs/phase-04-device-abstractions.md` | `docs/architecture/phase-history/phase-04-device-abstractions.md` |
| `docs/phase-05-application-core.md` | `docs/architecture/phase-history/phase-05-application-core.md` |
| `docs/phase-06-simulators-mocks.md` | `docs/architecture/phase-history/phase-06-simulators-mocks.md` |
| `docs/phase-07-persistence-config.md` | `docs/architecture/phase-history/phase-07-persistence-config.md` |
| `docs/phase-08-ui.md` | `docs/architecture/phase-history/phase-08-ui.md` |
| `docs/phase-09-tests.md` | `docs/architecture/phase-history/phase-09-tests.md` |
| `docs/phase-10-real-hardware-integration.md` | `docs/architecture/phase-history/phase-10-real-hardware-integration.md` |
| `docs/project-documentation-ru.md` | `docs/ru/project-documentation.md` |
| `docs/user-guide-ru.md` | `docs/ru/user-guide.md` |
| `docs/developer-guide-ru.md` | `docs/ru/developer-guide.md` |
| `docs/technical-guide-ru.md` | `docs/ru/technical-guide.md` |
| `docs/release-guide-ru.md` | `docs/ru/release-guide.md` |
| `docs/cleanup-audit-2026-04-16.md` | `docs/overview/cleanup-audit-2026-04-16.md` |
| `docs/future-requests-plan.txt` | `docs/overview/future-requests-plan.txt` |

ADR files intentionally remain in `docs/adr/`.
