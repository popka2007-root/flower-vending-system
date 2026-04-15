#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m flower_vending simulator-runtime --config config/examples/machine.simulator.yaml
