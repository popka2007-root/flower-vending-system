@echo off
setlocal
cd /d "%~dp0.."
python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare
