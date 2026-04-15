"""Scenario registry and suite runner for deterministic simulators."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

from flower_vending.simulators.scenario_result import ScenarioResult
from flower_vending.simulators.scenarios.customer_flows import (
    run_exact_change_only_scenario,
    run_happy_path_scenario,
    run_insufficient_change_scenario,
    run_normal_sale_scenario,
    run_payment_cancelled_scenario,
    run_pickup_timeout_placeholder_scenario,
)
from flower_vending.simulators.scenarios.fault_flows import (
    run_bill_jam_scenario,
    run_bill_rejected_scenario,
    run_critical_temperature_scenario,
    run_door_open_scenario,
    run_inventory_mismatch_scenario,
    run_motor_fault_scenario,
    run_partial_payout_scenario,
    run_product_vend_failure_scenario,
    run_validator_unavailable_scenario,
)


ScenarioRunner = Callable[[], Awaitable[ScenarioResult]]


SCENARIO_REGISTRY: dict[str, ScenarioRunner] = {
    "happy_path": run_happy_path_scenario,
    "normal_sale": run_normal_sale_scenario,
    "insufficient_change": run_insufficient_change_scenario,
    "exact_change_only": run_exact_change_only_scenario,
    "payment_cancelled": run_payment_cancelled_scenario,
    "bill_rejected": run_bill_rejected_scenario,
    "validator_unavailable": run_validator_unavailable_scenario,
    "bill_jam": run_bill_jam_scenario,
    "partial_payout": run_partial_payout_scenario,
    "motor_fault": run_motor_fault_scenario,
    "product_vend_failure": run_product_vend_failure_scenario,
    "door_open": run_door_open_scenario,
    "critical_temperature": run_critical_temperature_scenario,
    "inventory_mismatch": run_inventory_mismatch_scenario,
    "pickup_timeout_placeholder": run_pickup_timeout_placeholder_scenario,
}


async def run_default_scenario_suite(
    names: Iterable[str] | None = None,
) -> tuple[ScenarioResult, ...]:
    selected_names = tuple(names or SCENARIO_REGISTRY.keys())
    results: list[ScenarioResult] = []
    for scenario_name in selected_names:
        runner = SCENARIO_REGISTRY[scenario_name]
        results.append(await runner())
    return tuple(results)
