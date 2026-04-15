#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m flower_vending service --config config/examples/machine.simulator.yaml
