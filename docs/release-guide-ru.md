# Flower Vending System: release и доставка пользователю

## 1. Какие артефакты считаются основными

Для передачи пользователю или демонстрационной машине рекомендуются:

- Windows: `FlowerVendingSimulator-Setup-Windows-x64.exe`
- Windows portable: `FlowerVendingSimulator-Windows-x64.exe`
- Linux: `FlowerVendingSimulator-Linux-x86_64.AppImage`

Все эти артефакты задуманы как self-contained desktop delivery без отдельной
установки Python.

## 2. Как собрать локально

Windows:

```powershell
scripts\build-windows-release.bat
```

Linux:

```bash
./scripts/build-linux-release.sh /path/to/appimagetool
```

Готовые файлы попадают в каталог `artifacts/`.

## 3. Как публиковать на GitHub

1. Репозиторий должен быть загружен на GitHub.
2. Workflow `.github/workflows/build-release.yml` должен быть доступен в default branch.
3. При создании и push тега формата `v0.1.0` workflow автоматически:
   - соберет Windows portable `.exe`;
   - соберет Windows installer `.exe`;
   - соберет Linux AppImage и tarball;
   - опубликует релиз на GitHub.

## 4. Что получает конечный пользователь

Пользователь скачивает ровно один нужный ему файл:

- Windows — setup `.exe` или portable `.exe`;
- Linux — `.AppImage`.

Это закрывает сценарий “скачал один файл и запустил”.

## 5. Что не входит в release promise

Release-артефакты покрывают simulator-safe контур. Они не означают, что
подтверждены:

- реальные протоколы платежного оборудования;
- реальные моторные контроллеры;
- финальная конфигурация ОС для kiosk deployment;
- реальные сервисы и аппаратный watchdog на целевом стенде.
