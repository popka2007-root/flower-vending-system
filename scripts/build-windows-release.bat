@echo off
setlocal
cd /d "%~dp0.."
python -m pip install -r requirements-ui.txt pyinstaller
python packaging\build_release.py windows-portable
python packaging\build_release.py windows-installer
