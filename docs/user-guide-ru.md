# Flower Vending Simulator: руководство пользователя

## 1. Что это за приложение

`Flower Vending Simulator` — это настольная simulator-first версия ПО цветочного автомата.

Приложение нужно для:

- демонстрации интерфейса автомата;
- проверки сценариев покупки без реального железа;
- показа сервисных и диагностических режимов;
- воспроизведения типовых ошибок в безопасном режиме.

Это **не готовая боевая прошивка автомата**. Реальные протоколы купюроприемника, узла сдачи, моторов и датчиков пока не подтверждены стендом и не должны считаться завершенными.

## 2. Что уже умеет текущая версия

В текущем simulator baseline можно:

- открыть kiosk-подобный интерфейс;
- просматривать каталог цветов;
- выбрать товар и пройти наличный сценарий оплаты;
- быстро “внести” купюры через simulator controls;
- открыть экран диагностики;
- войти в сервисный режим;
- воспроизвести ошибки: `bill rejected`, `bill jam`, `validator unavailable`, `partial payout`, `motor fault`, `inventory mismatch`, `door open`, `critical temperature`;
- увидеть блокировки продаж и последние события автомата.

## 3. Самый простой способ проверить работу

Если у вас проект открыт из исходников:

```powershell
cd C:\Users\User\Desktop\flower-vending-system
python scripts\verify_project.py
```

Если проверка успешна, вы увидите:

- успешную валидацию конфига;
- успешную компиляцию кода;
- прохождение unit/integration/recovery тестов;
- успешный diagnostics smoke test;
- успешные simulator runtime сценарии.

## 4. Как запустить приложение вручную

### 4.1 Проверка конфига

```powershell
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
```

Команда:

- проверяет конфиг;
- создает рабочие каталоги;
- подготавливает локальное состояние.

### 4.2 Диагностика без UI

```powershell
python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
```

Вы увидите:

- текущее состояние автомата;
- блокировки продаж;
- состояния устройств;
- последние события;
- platform extension points.

### 4.3 Сервисный режим

```powershell
python -m flower_vending service --config config\examples\machine.simulator.yaml
```

### 4.4 Запуск simulator runtime

```powershell
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml
```

### 4.5 Запуск интерфейса

```powershell
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml
```

Если хотите пользоваться готовыми Windows-скриптами:

```powershell
scripts\validate-config.bat
scripts\run-diagnostics.bat
scripts\run-service-mode.bat
scripts\run-simulator-runtime.bat
scripts\run-simulator-ui.bat
```

## 5. Как пройти обычную покупку

1. Откройте каталог товаров.
2. Выберите товар.
3. Перейдите на экран оплаты.
4. Используйте быстрые действия внесения купюр.
5. Дождитесь перехода к выдаче.
6. Перейдите к экрану получения товара.

Так как это simulator mode, сценарий не зависит от настоящего купюроприемника или моторов.

## 6. Что можно делать в сервисном режиме

В сервисном режиме и simulator controls можно:

- открыть и закрыть сервисную дверь;
- поднять или восстановить температуру;
- включить `validator unavailable`;
- вызвать `bill rejected`;
- вызвать `bill jam`;
- вызвать `partial payout`;
- вызвать `motor fault`;
- вызвать `inventory mismatch`;
- вернуться к нормальному состоянию.

Это полезно для проверки UX и защитной логики без реального стенда.

## 7. Где лежат рабочие данные

При запуске проект пишет состояние, базу и логи не в папку с кодом, а в пользовательский state root.

Windows:

- `%LOCALAPPDATA%\FlowerVendingSystem`

Там обычно находятся:

- `var\data` — база и runtime state;
- `var\log` — журналы;
- `docs` — копии документации для packaged build.

## 8. Что делать, если продажа заблокирована

1. Откройте diagnostics mode.
2. Посмотрите список `sale blockers`.
3. Если включен fault-сценарий, откройте service mode.
4. Сбросьте fault или верните нормальные условия.
5. Повторите покупку.

Типовые причины блокировки:

- открыта сервисная дверь;
- критическая температура;
- неисправность валидатора;
- неисправность мотора;
- недостаточно безопасной сдачи;
- inventory mismatch;
- recovery/restricted mode.

## 9. Что уже подтверждено, а что нет

Подтверждено в software-only режиме:

- запуск CLI;
- запуск simulator runtime;
- diagnostics mode;
- service mode;
- тесты и базовые runtime-сценарии;
- kiosk-like UI слой;
- deterministic simulator controls.

Пока не подтверждено реальным железом:

- настоящий DBV-300-SD protocol;
- реальная выдача сдачи;
- реальные моторы и датчики;
- production watchdog;
- production kiosk lockdown;
- OS service/autostart deployment;
- physical pickup/window sensing и стендовая проверка pickup timeout для боевого автомата.

## 10. Если нужен самый быстрый ответ “работает ли проект”

Используйте одну команду:

```powershell
python scripts\verify_project.py
```

Если она завершается успешно, значит текущая simulator-safe версия проекта работоспособна.
