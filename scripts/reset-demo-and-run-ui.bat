@echo off
setlocal

cd /d "%~dp0.."

echo [flower-vending] Resetting simulator demo state and launching UI...
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml --reset-state
exit /b %errorlevel%
