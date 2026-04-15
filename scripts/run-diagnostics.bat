@echo off
setlocal
cd /d "%~dp0.."
python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
