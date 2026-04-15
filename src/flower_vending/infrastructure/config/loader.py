"""YAML configuration loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from flower_vending.infrastructure.config.models import AppConfig


def load_machine_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return AppConfig.model_validate(payload)


def build_device_settings_snapshot(config: AppConfig) -> dict[str, dict[str, Any]]:
    return {
        "bill_validator": config.devices.bill_validator.model_dump(mode="json"),
        "change_dispenser": config.devices.change_dispenser.model_dump(mode="json"),
        "motor_controller": config.devices.motor_controller.model_dump(mode="json"),
        "cooling_controller": config.devices.cooling_controller.model_dump(mode="json"),
        "window_controller": config.devices.window_controller.model_dump(mode="json"),
        "temperature_sensor": config.devices.temperature_sensor.model_dump(mode="json"),
        "door_sensor": config.devices.door_sensor.model_dump(mode="json"),
        "inventory_sensor": config.devices.inventory_sensor.model_dump(mode="json"),
        "position_sensor": config.devices.position_sensor.model_dump(mode="json"),
        "watchdog": config.platform.watchdog.model_dump(mode="json"),
    }
