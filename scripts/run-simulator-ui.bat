@echo off
setlocal
cd /d "%~dp0.."
python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml
