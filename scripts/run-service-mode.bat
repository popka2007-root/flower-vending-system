@echo off
setlocal
cd /d "%~dp0.."
python -m flower_vending service --config config\examples\machine.simulator.yaml
