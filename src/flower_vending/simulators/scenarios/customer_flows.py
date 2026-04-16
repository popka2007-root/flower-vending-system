"""Nominal deterministic customer scenarios."""

from __future__ import annotations

from flower_vending.domain.commands.purchase_commands import CancelPurchase
from flower_vending.domain.exceptions import ChangeUnavailableError
from flower_vending.simulators.harness import SimulationHarness
from flower_vending.simulators.scenario_result import ScenarioResult


async def run_normal_sale_scenario() -> ScenarioResult:
    harness = SimulationHarness.build()
    await harness.start()
    try:
        transaction_id = await harness.start_purchase(correlation_id="normal_sale")
        await harness.accept_cash(transaction_id, correlation_id="normal_sale")
        await harness.insert_bill(500, correlation_id="normal_sale")
        await harness.confirm_pickup(transaction_id, correlation_id="normal_sale")
        return harness.scenario_result(
            scenario_name="normal_sale",
            success=True,
            notes=[
                "exact payment completed without change payout",
                "product dispensed and pickup confirmed",
            ],
        )
    finally:
        await harness.stop()


async def run_insufficient_change_scenario() -> ScenarioResult:
    harness = SimulationHarness.build(
        price_minor_units=300,
        change_inventory={100: 1},
        accepted_bill_denominations=(500,),
    )
    await harness.start()
    try:
        transaction_id = await harness.start_purchase(correlation_id="insufficient_change")
        try:
            await harness.accept_cash(transaction_id, correlation_id="insufficient_change")
        except ChangeUnavailableError as exc:
            return harness.scenario_result(
                scenario_name="insufficient_change",
                success=harness.core.machine_status_service.runtime.status.exact_change_only,
                errors=[str(exc)],
                notes=["sale is blocked because safe payout cannot be guaranteed"],
            )
        return harness.scenario_result(
            scenario_name="insufficient_change",
            success=False,
            errors=["expected ChangeUnavailableError was not raised"],
        )
    finally:
        await harness.stop()


async def run_exact_change_only_scenario() -> ScenarioResult:
    harness = SimulationHarness.build(
        price_minor_units=300,
        change_inventory={100: 1},
        accepted_bill_denominations=(100, 500),
    )
    await harness.start()
    try:
        transaction_id = await harness.start_purchase(correlation_id="exact_change_only")
        try:
            await harness.accept_cash(transaction_id, correlation_id="exact_change_only")
        except ChangeUnavailableError as exc:
            status = harness.core.machine_status_service.runtime.status
            return harness.scenario_result(
                scenario_name="exact_change_only",
                success=status.exact_change_only and status.machine_state == "WAITING_FOR_PAYMENT",
                errors=[str(exc)],
                notes=[
                    "runtime advertises exact-change-only posture",
                    "cash session still stays blocked until safe payout support is confirmed",
                ],
            )
        return harness.scenario_result(
            scenario_name="exact_change_only",
            success=False,
            errors=["expected ChangeUnavailableError was not raised"],
        )
    finally:
        await harness.stop()


async def run_payment_cancelled_scenario() -> ScenarioResult:
    harness = SimulationHarness.build()
    await harness.start()
    try:
        transaction_id = await harness.start_purchase(correlation_id="payment_cancelled")
        await harness.accept_cash(transaction_id, correlation_id="payment_cancelled")
        await harness.core.command_bus.dispatch(
            CancelPurchase(
                correlation_id="payment_cancelled",
                transaction_id=transaction_id,
            )
        )
        return harness.scenario_result(
            scenario_name="payment_cancelled",
            success=harness.core.fsm.current_state.value == "IDLE",
            notes=["purchase was cancelled before cash acceptance completed"],
        )
    finally:
        await harness.stop()


async def run_pickup_timeout_scenario() -> ScenarioResult:
    harness = SimulationHarness.build(pickup_timeout_s=0.05)
    await harness.start()
    try:
        transaction_id = await harness.start_purchase(correlation_id="pickup_timeout")
        await harness.accept_cash(transaction_id, correlation_id="pickup_timeout")
        await harness.insert_bill(500, correlation_id="pickup_timeout")
        await harness.wait_for_runtime_processing(timeout_s=0.2)
        return harness.scenario_result(
            scenario_name="pickup_timeout",
            success=harness.core.fsm.current_state.value == "RECOVERY_PENDING",
            notes=[
                "pickup timeout elapsed and closed the delivery window",
                "transaction is held for manual review after unconfirmed pickup",
            ],
        )
    finally:
        await harness.stop()


async def run_happy_path_scenario() -> ScenarioResult:
    return await run_normal_sale_scenario()
