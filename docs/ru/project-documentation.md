# Flower Vending System

Полная проектная документация и руководство по передаче проекта.

Проект: `flower-vending-system`

Этот документ объясняет проект от начала до конца: назначение, архитектуру, слои, денежный поток, работу со сдачей, JCM DBV-300-SD, симуляторы, тесты, запуск проверки, текущие ограничения и план доведения до реального промышленного автомата.

## 1. Краткое резюме

Flower Vending System — это production-oriented основа программной системы для вендингового автомата по продаже цветов.

- Это не однофайловый демонстрационный пример.
- В проекте есть доменная модель, application core, FSM, device abstractions, симуляторы, тесты, persistence scaffold, UI facade и архитектурные документы.
- Система рассчитана на PC/SBC-контроллер и должна быть переносимой между Windows и Linux.
- Текущая версия проверяется в симуляторном режиме без настоящего купюроприемника, моторов и датчиков.
- Реальная интеграция с железом намеренно не выдумана: DBV-300-SD, узел сдачи, моторы, датчики, watchdog, kiosk mode и autostart требуют документации и стендовых испытаний.

Главный принцип надежности: критические действия с деньгами и физическими механизмами должны восстанавливаться по transaction journal, а не по оперативной памяти процесса.

## 2. Быстрая проверка работоспособности

Откройте PowerShell:

```powershell
cd flower-vending-system
python scripts\verify_project.py
```

Ожидаемый результат:

```text
PASS: compile source and tests
PASS: unit/integration/recovery tests
PASS: service door blocks sale on startup health check
PASS: validator background loop processes inserted bill
PASS: unsafe multi-note change path is blocked
PASS: cancel after accepted cash dispenses refund
Verification finished successfully.
```

Если команда прошла успешно, значит текущий simulator baseline компилируется, автоматические тесты проходят, фоновые runtime-задачи работают, базовые safety-блокировки активны, небезопасная сдача блокируется, а отмена после принятой наличности выполняет возврат.

Сценарий `pickup timeout` теперь входит в passing simulator baseline: таймаут закрывает окно выдачи, блокирует продажи и переводит транзакцию в manual review. Для реального автомата это остается hardware-dependent областью: нужны физические датчики pickup/window и стендовая проверка.

## 3. Что уже реализовано

- Доменная модель для товаров, слотов, денег, номиналов, транзакций, платежных сессий, статуса автомата и health snapshot.
- Application layer с command bus, event bus, FSM, vending controller, payment coordinator, health monitor, recovery manager и service-mode coordinator.
- Device contracts для купюроприемника, узла сдачи, мотора, охлаждения, окна выдачи, температурного датчика, сервисной двери, датчика товара, датчика позиции и watchdog.
- DBV-300-SD adapter scaffold с разделением transport, protocol и domain-facing adapter.
- ChangeManager с расчетом сдачи, резервированием, refund, exact-change-only policy и drift/reconcile flags.
- Симуляторы устройств и fault injection для локальной разработки.
- SQLite persistence scaffold, transaction journal primitives, repositories, config loader и logging hooks.
- UI facade, presenters/view models и skeleton экранов для kiosk/touch сценария.
- Unit, integration и recovery tests.
- Скрипт `scripts\verify_project.py`, который запускает основную проверку проекта одной командой.

## 4. Что пока не является production-ready

- Низкоуровневый протокол JCM DBV-300-SD не реализован, потому что команды, фреймы, handshake, тайминги и режим работы должны быть подтверждены документацией JCM и стендом.
- Реальный узел сдачи не подключен: нужен подтвержденный протокол, датчики наличия денег, сценарии partial payout и процедуры сверки.
- Мотор выдачи, окно выдачи, датчики позиции, датчик товара, охлаждение и сервисная дверь пока представлены интерфейсами и симуляторами.
- Полный durable journal wiring в live runtime path нужно усилить перед production.
- Pickup timeout policy реализована для simulator-safe runtime, но поведение для реального автомата требует physical pickup/window sensing и bench validation.
- Kiosk mode, autostart, OS watchdog, упаковка под Windows service или Linux systemd не завершены.

## 5. Архитектура по слоям

Система разделена на независимые слои.

- `domain` содержит бизнес-правила, value objects, entities, domain events и exceptions. Здесь не должно быть COM-портов, SQL, Qt, asyncio-задач и бинарных протоколов.
- `app` содержит use cases, orchestration, FSM, command/event bus, health monitor и recovery decisions. Этот слой управляет процессом продажи, но не знает деталей фреймов DBV-300-SD.
- `devices` содержит интерфейсы устройств и адаптеры. Здесь живут BillValidator, ChangeDispenser, MotorController, CoolingController, WindowController, sensors и WatchdogAdapter.
- `infrastructure` содержит SQLite, repositories, transaction journal, config loader, structured logging, serial/MDB transport и platform-specific adapters.
- `payments` содержит реализованную подсистему расчета сдачи; inventory, vending, cooling и telemetry сейчас реализованы через domain/app/devices/simulators, без пустых placeholder-пакетов.
- `ui` содержит presenters/view models/screens. UI не должен напрямую управлять железом или менять доменные объекты.
- `simulators` содержит mock devices, deterministic сценарии и fault injection.
- `tests` проверяет domain, application, integration и recovery cases.

Такое разделение позволяет запускать core без UI и без железа, а реальные драйверы подключать позже без переписывания бизнес-логики.

## 6. Основные каталоги и файлы

- `src/flower_vending/domain` — деньги, товары, слоты, транзакции, payment session, status, events, exceptions.
- `src/flower_vending/app/bootstrap.py` — сборка ApplicationCore и runtime lifecycle.
- `src/flower_vending/app/orchestrators/payment_coordinator.py` — cash payment flow, обработка событий валидатора, cancel и refund.
- `src/flower_vending/payments/change_manager.py` — расчет и резервирование сдачи, refund, drift detection.
- `src/flower_vending/app/fsm/transitions.py` — допустимые переходы конечного автомата.
- `src/flower_vending/simulators/harness.py` — симуляторный запуск core с background runtime tasks.
- `src/flower_vending/devices/dbv300sd` — архитектурная заготовка DBV-300-SD adapter/protocol/transport.
- `config` — YAML-конфигурация устройств, портов и runtime параметров.
- `docs/architecture/phase-history/phase-01...phase-10` — фазовая архитектурная документация.
- `docs/operations/runbook.md` — практический runbook по запуску и диагностике.
- `scripts/verify_project.py` — основная команда проверки.
- `scripts/generate_project_documentation_docx.py` — генератор этого Word-документа.

## 7. Нормальный cash payment flow

Безопасный поток продажи за наличные:

- Пользователь выбирает товар.
- Система создает transaction id и payment session.
- Проверяется наличие товара в слоте.
- Проверяется, что автомат не в ошибке, сервисная дверь закрыта, температура безопасна, валидатор доступен, узел сдачи доступен.
- До приема денег ChangeManager проверяет возможность безопасной сдачи и резервирует сдачу для платежной сессии.
- Валидатор включается только после успешных preconditions.
- События валидатора приходят как domain-level события: `bill_detected`, `bill_validated`, `bill_rejected`, `escrow_available`, `bill_stacked`, `bill_returned`, `validator_fault`, `validator_disabled`.
- PaymentCoordinator накапливает внесенную сумму.
- После достижения цены валидатор отключается.
- Рассчитывается финальная сдача.
- Сдача выдается и подтверждается.
- Только после успешной сдачи запускается выдача товара.
- Открывается окно выдачи, пользователь забирает товар, транзакция завершается.
- Результат должен попадать в transaction journal.

В текущей стратегии товар выдается после сдачи. Это снижает риск ситуации, когда клиент уже получил товар, но автомат не смог вернуть сдачу.

## 8. Отмена покупки и refund

Если пользователь отменяет покупку до подтверждения оплаты:

- Валидатор отключается.
- Если деньги еще не были приняты, сессия отменяется без refund.
- Если банкноты уже были приняты и зафиксированы как stacked, система выполняет refund через ChangeManager.
- Если refund выполнен успешно, транзакция отменяется безопасно.
- Если refund частичный, неоднозначный или завершился ошибкой, автомат должен перейти в `RECOVERY_PENDING`, а продажи блокируются до сервисного решения.

Это защищает от двойной выдачи денег и от ситуации, когда учетная система считает деньги возвращенными, но физически возврат не подтвержден.

## 9. Логика сдачи

Сдача вынесена в отдельный модуль, потому что она затрагивает сразу бизнес-логику, физическое устройство и учет денег.

ChangeManager отвечает за:

- учет доступных номиналов;
- расчет сдачи по доступным номиналам;
- проверку worst-case overpay до начала приема денег;
- резервирование сдачи на время платежной сессии;
- финальную выдачу сдачи;
- refund при отмене;
- exact-change-only policy;
- detection accounting/physical drift;
- подготовку к reconcile после ошибки.

Важно разделять accounting state и physical state.

- Accounting state — что система считает доступным по номиналам после резервов, payout и service operations.
- Physical state — что реально находится в кассете или хоппере по датчикам, self-test или ручной сверке.
- Если эти состояния расходятся, продажа за наличные должна блокироваться или переводиться в безопасный режим до сверки.

## 10. Exact change only

Если точную сдачу выдать нельзя, система не должна принимать деньги в обычном режиме.

Возможные политики:

- полностью заблокировать cash sale;
- разрешить только покупку за точную сумму;
- показать пользователю экран exact change only;
- оставить безналичную оплату доступной в будущем, если она не зависит от узла сдачи.

Политика должна быть конфигурируемой и явно видимой в UI.

## 11. JCM DBV-300-SD

DBV-300-SD рассматривается как реальное устройство, а не абстрактный bill acceptor. При этом низкоуровневые команды не выдумываются.

Архитектурное разделение:

- Transport layer — COM/serial, MDB или другой физический канал.
- Protocol layer — конкретные команды, ответы, статусы, handshake, polling и тайминги после подтверждения документацией.
- Domain-facing adapter — преобразует protocol events в события уровня приложения.
- Business logic — работает только с интерфейсом BillValidator и не знает, что на текущем стенде устройство на COM3.

COM3 должен жить в конфигурации, а не в domain или application logic.

Что нужно подтвердить на реальном стенде:

- режим работы устройства: MDB, Serial или Pulse-like;
- параметры порта: baud rate, parity, stop bits, flow control, timeouts;
- команды включения и отключения приема;
- escrow/stack/return поведение;
- fault codes и recovery после jam или потери связи;
- допустимые задержки и retry policy;
- что именно означает подтверждение физического приема банкноты.

## 12. FSM автомата

FSM ограничивает допустимые переходы и запрещает опасные действия.

Основные состояния:

- `BOOT` — старт процесса, прием денег и выдача товара запрещены.
- `SELF_TEST` — проверка устройств.
- `IDLE` — автомат готов к выбору товара.
- `PRODUCT_SELECTED` — товар выбран, но деньги еще нельзя принимать без проверок.
- `CHECKING_AVAILABILITY` — проверка товара и датчиков.
- `CHECKING_CHANGE` — проверка безопасной сдачи.
- `WAITING_FOR_PAYMENT` — ожидание оплаты.
- `ACCEPTING_CASH` — прием событий валидатора.
- `PAYMENT_ACCEPTED` — оплата подтверждена.
- `DISPENSING_CHANGE` — выдача сдачи.
- `DISPENSING_PRODUCT` — физическая выдача товара.
- `OPENING_DELIVERY_WINDOW` — открытие окна выдачи.
- `WAITING_FOR_CUSTOMER_PICKUP` — ожидание, пока клиент заберет товар.
- `CLOSING_DELIVERY_WINDOW` — закрытие окна.
- `COMPLETED` — транзакция завершена.
- `CANCELLED` — транзакция отменена.
- `RECOVERY_PENDING` — требуется восстановление после неоднозначного состояния.
- `SERVICE_MODE` — сервисный режим.
- `FAULT` и `OUT_OF_SERVICE` — критическая ошибка или блокировка продаж.

Критическое правило: если после рестарта система не уверена, была ли физически выдана сдача или товар, она не должна повторять действие автоматически. Нужно переходить в recovery/service flow.

## 13. Runtime lifecycle

ApplicationCore имеет runtime lifecycle:

- `start_runtime()` запускает фоновые задачи.
- `stop_runtime()` корректно останавливает задачи.
- Validator loop обрабатывает события купюроприемника асинхронно.
- Health monitor loop обновляет sale blockers по двери, температуре и fault devices.
- Watchdog loop имитирует arm/kick/disarm и готов к замене на platform-specific реализацию.

Это важно, потому что живой автомат работает с асинхронными событиями, а не только с ручными вызовами методов в unit tests.

## 14. Safety и fail-safe

Система должна быть консервативной.

- Нельзя выдавать товар до подтвержденной оплаты.
- Нельзя принимать оплату, если автомат в ошибке.
- Нельзя принимать оплату при открытой сервисной двери.
- Нельзя принимать оплату при критической температуре.
- Нельзя принимать оплату, если товар отсутствует.
- Нельзя принимать оплату, если сдача небезопасна.
- Нельзя повторно выдавать товар при неоднозначном recovery.
- Нельзя повторно выдавать сдачу при неизвестном результате payout.

Fail-safe поведение означает блокировку продаж, логирование, journal entry и перевод в service/recovery режим, если продолжение может привести к потере денег, двойной выдаче или продаже испорченного товара.

## 15. Persistence и config

SQLite используется для локального durable состояния.

Хранить нужно:

- каталог товаров;
- цены;
- остатки по ячейкам;
- transaction journal;
- ошибки устройств;
- деньги по номиналам;
- кассовые остатки;
- service events;
- temperature events;
- recovery log;
- незавершенные транзакции;
- настройки устройств;
- platform-specific параметры портов и таймаутов.

YAML-конфигурация должна содержать device mappings, включая купюроприемник на COM3, но это не должно попадать в доменную модель.

## 16. UI и kiosk mode

UI должен быть touch-friendly и отделенным от core.

Нужные экраны:

- главный экран;
- каталог цветов;
- карточка товара;
- экран оплаты;
- отображение внесенной суммы;
- экран "нет сдачи";
- экран exact change only;
- экран "товар выдается";
- экран "заберите товар";
- экран ошибок;
- экран блокировки продаж по температуре или fault state;
- сервисный экран;
- экран диагностики устройств.

UI отправляет команды в application layer и получает view model от presenter. UI не должен напрямую управлять валидатором, мотором, окном выдачи или SQLite.

## 17. Симуляторы и fault injection

Симуляторы позволяют проверять поведение без оборудования.

Поддерживаемые сценарии:

- validator unavailable;
- bill rejected;
- bill jam;
- partial payout;
- motor fault;
- door open;
- critical temperature;
- inventory mismatch;
- unsafe multi-note change;
- cancel after accepted cash.

Симуляторы не заменяют bench tests, но позволяют безопасно разрабатывать core, пока железо и протоколы уточняются.

## 18. Тесты

Основные проверки:

- compileall для `src` и `tests`;
- unit/integration/recovery tests через unittest;
- health check при открытой сервисной двери;
- background validator loop;
- блокировка unsafe change;
- refund при отмене после принятой наличности.

Команды:

```powershell
python -m compileall -q src tests
python -m unittest discover -s tests -t tests -q
python scripts\verify_project.py
```

Если plain `python -m unittest discover` ведет себя иначе, используйте именно `-s tests -t tests`, как указано в runbook.

## 19. Что было исправлено после анализа

- Добавлен runtime lifecycle в `ApplicationCore`.
- Добавлена фоновая обработка событий валидатора.
- Добавлен health monitor polling на старте и в runtime.
- Добавлена watchdog loop за интерфейсом WatchdogAdapter.
- Усилен ChangeManager для worst-case multi-note overpay.
- Добавлен refund при cancel после accepted cash.
- Добавлен переход FSM `ACCEPTING_CASH -> RECOVERY_PENDING`.
- Simulator harness переведен на runtime tasks.
- Добавлены тесты для unsafe change и refund.
- Добавлен единый скрипт проверки проекта.

## 20. Что делать дальше

Приоритетный план:

- Получить официальную документацию и стендовые параметры JCM DBV-300-SD.
- Подтвердить режим DBV-300-SD: MDB, Serial или Pulse-like.
- Реализовать и протестировать реальный transport/protocol adapter.
- Подключить реальный узел сдачи и проверить partial payout, empty cassette, jam, mismatch.
- Подтвердить pickup/window sensing на стенде и описать pilot-процедуру manual review после pickup timeout.
- Довести transaction journal до полного journal-first live path.
- Реализовать service procedures: инкассация, пополнение, ручная сверка, аудит сервисной двери.
- Реализовать platform-specific kiosk/autostart/watchdog packaging для Windows и Linux.
- Провести bench tests и затем пилот на реальном автомате.

## 21. Риски миграции с legacy Windows-системы

- В legacy могли быть скрытые COM-настройки и тайминги.
- Старое ПО могло содержать аппаратные workaround, которых нет в документации.
- Отдельная кнопка "Сдача" из старой логики должна быть заменена безопасным транзакционным cash flow или явно оформлена как отдельный бизнес-сценарий.
- Windows/Linux различия по serial permissions, service hosting, autostart, kiosk locking и watchdog нельзя оставлять на последний этап.
- Нужно осторожно переносить любые старые предположения: подтверждать их логами, документацией и стендом.

## 22. Чеклист передачи проекта

- Открыть этот Word-документ и убедиться, что русская кодировка отображается нормально.
- Запустить `python scripts\verify_project.py`.
- Прочитать `README.md`.
- Прочитать `docs/operations/runbook.md`.
- Для архитектуры пройти `docs/architecture/phase-history/phase-01...phase-10`.
- Для железа отдельно изучить `docs/architecture/phase-history/phase-10-real-hardware-integration.md`.
- Новые аппаратные решения фиксировать ADR-документами в `docs/adr`.
- Не писать низкоуровневые команды DBV-300-SD по догадкам.
- Любое физическое действие должно иметь idempotency, recovery story и тесты отказов.
