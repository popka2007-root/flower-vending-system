#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install -r requirements-ui.txt pyinstaller
python packaging/build_release.py linux-appimage --appimagetool "${APPIMAGETOOL:?Set APPIMAGETOOL to appimagetool or a wrapper script}"
