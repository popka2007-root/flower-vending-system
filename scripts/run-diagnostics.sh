#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m flower_vending diagnostics --config config/examples/machine.simulator.yaml
