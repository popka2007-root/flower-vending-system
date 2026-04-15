@echo off
setlocal
cd /d "%~dp0.."
python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml
