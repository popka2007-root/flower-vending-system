from __future__ import annotations

import unittest

from flower_vending.devices.contracts import (
    ChangeDispenseRequest,
    DeviceCommandPolicy,
    DeviceFaultCode,
    DeviceOperationalState,
    PayoutStatus,
)
from flower_vending.devices.exceptions import DeviceCommandError, DeviceCommandTimeoutError
from flower_vending.simulators.devices import MockChangeDispenser, MockMotorController
from flower_vending.simulators.faults import SimulatorFaultCode


class DeviceCommandPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_records_fault_and_can_recover(self) -> None:
        motor = MockMotorController(
            command_policy=DeviceCommandPolicy(timeout_s=0.01, retry_count=0)
        )
        await motor.start()
        self.addAsyncCleanup(motor.stop)
        motor.inject_fault(
            SimulatorFaultCode.COMMAND_TIMEOUT,
            remaining_hits=1,
            delay_s=0.05,
        )

        with self.assertRaises(DeviceCommandTimeoutError):
            await motor.vend_slot("A1", correlation_id="timeout-corr")

        faulted = await motor.get_health()
        self.assertEqual(faulted.state, DeviceOperationalState.FAULT)
        self.assertEqual(faulted.faults[0].code, DeviceFaultCode.COMMAND_TIMEOUT.value)
        self.assertEqual(faulted.faults[0].details["correlation_id"], "timeout-corr")

        motor.clear_faults()
        recovered = await motor.get_health()
        self.assertEqual(recovered.state, DeviceOperationalState.READY)
        self.assertEqual(recovered.faults, ())

    async def test_retry_success_records_recovery_without_duplicate_side_effect(self) -> None:
        motor = MockMotorController(
            command_policy=DeviceCommandPolicy(timeout_s=0.1, retry_count=1)
        )
        await motor.start()
        self.addAsyncCleanup(motor.stop)
        motor.inject_fault(SimulatorFaultCode.TRANSIENT_COMMAND_FAILURE, remaining_hits=1)

        await motor.vend_slot("A1", correlation_id="retry-corr")
        health = await motor.get_health()
        self.assertEqual(motor.vend_history, ["A1"])
        self.assertEqual(health.state, DeviceOperationalState.READY)
        self.assertEqual(health.details["attempts"], 2)
        self.assertTrue(health.details["recovered"])

        await motor.vend_slot("A1", correlation_id="retry-corr")
        replay_health = await motor.get_health()
        self.assertEqual(motor.vend_history, ["A1"])
        self.assertTrue(replay_health.details["idempotent_replay"])

    async def test_retry_exhausted_records_terminal_fault(self) -> None:
        motor = MockMotorController(
            command_policy=DeviceCommandPolicy(timeout_s=0.1, retry_count=1)
        )
        await motor.start()
        self.addAsyncCleanup(motor.stop)
        motor.inject_fault(SimulatorFaultCode.TRANSIENT_COMMAND_FAILURE, remaining_hits=2)

        with self.assertRaises(DeviceCommandError):
            await motor.vend_slot("A1", correlation_id="exhausted-corr")

        health = await motor.get_health()
        self.assertEqual(motor.vend_history, [])
        self.assertEqual(health.state, DeviceOperationalState.FAULT)
        self.assertEqual(health.faults[0].code, DeviceFaultCode.COMMAND_RETRY_EXHAUSTED.value)
        self.assertEqual(
            health.faults[0].details["cause_fault_code"],
            DeviceFaultCode.TRANSIENT_COMMAND_FAILURE.value,
        )

    async def test_ambiguous_physical_result_requires_manual_review(self) -> None:
        dispenser = MockChangeDispenser(
            inventory={100: 3},
            command_policy=DeviceCommandPolicy(timeout_s=0.1, retry_count=1),
        )
        await dispenser.start()
        self.addAsyncCleanup(dispenser.stop)
        dispenser.inject_fault(
            SimulatorFaultCode.AMBIGUOUS_PHYSICAL_RESULT,
            remaining_hits=1,
            paid_counts_by_denomination={100: 1},
        )
        request = ChangeDispenseRequest(
            request_id="txn-1:change",
            counts_by_denomination={100: 2},
            correlation_id="ambiguous-corr",
        )

        result = await dispenser.dispense(request)

        health = await dispenser.get_health()
        self.assertEqual(result.status, PayoutStatus.AMBIGUOUS)
        self.assertEqual(health.state, DeviceOperationalState.FAULT)
        self.assertEqual(health.faults[0].code, DeviceFaultCode.AMBIGUOUS_PHYSICAL_RESULT.value)
        self.assertTrue(health.faults[0].details["manual_review_required"])
        self.assertEqual(health.faults[0].details["correlation_id"], "ambiguous-corr")


if __name__ == "__main__":
    unittest.main()
