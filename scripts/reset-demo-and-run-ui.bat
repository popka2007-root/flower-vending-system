@echo off
setlocal

cd /d "%~dp0.."

set "STATE_ROOT=%LOCALAPPDATA%\FlowerVendingSystem"
set "SIM_DB=%STATE_ROOT%\var\data\flower_vending_simulator.db"

echo [flower-vending] Resetting simulator demo state...
if exist "%SIM_DB%" (
    del /f /q "%SIM_DB%"
    if errorlevel 1 (
        echo [flower-vending] Failed to remove "%SIM_DB%".
        exit /b 1
    )
)

echo [flower-vending] Preparing runtime directories...
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
if errorlevel 1 exit /b %errorlevel%

echo [flower-vending] Launching simulator UI...
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml
exit /b %errorlevel%
