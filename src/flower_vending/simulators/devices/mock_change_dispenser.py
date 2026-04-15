"""Deterministic mock change dispenser."""

from __future__ import annotations

from flower_vending.devices.contracts import (
    ChangeDispenseRequest,
    ChangeDispenseResult,
    DeviceOperationalState,
    PayoutStatus,
)
from flower_vending.devices.exceptions import DeviceAdapterError
from flower_vending.devices.interfaces import ChangeDispenser
from flower_vending.simulators.devices.base import MockManagedDevice
from flower_vending.simulators.faults import SimulatorFaultCode


class MockChangeDispenser(MockManagedDevice, ChangeDispenser):
    def __init__(
        self,
        name: str = "mock_change_dispenser",
        *,
        inventory: dict[int, int] | None = None,
    ) -> None:
        super().__init__(name)
        self._inventory = dict(inventory or {})

    async def can_dispense(self, request: ChangeDispenseRequest) -> bool:
        if self.injector.has(SimulatorFaultCode.PAYOUT_UNAVAILABLE):
            return False
        return all(
            self._inventory.get(denomination, 0) >= count
            for denomination, count in request.counts_by_denomination.items()
        )

    async def dispense(self, request: ChangeDispenseRequest) -> ChangeDispenseResult:
        unavailable = self.injector.consume(SimulatorFaultCode.PAYOUT_UNAVAILABLE)
        if unavailable is not None:
            self._activate_fault(
                code=unavailable.code.value,
                message=unavailable.message or "payout unavailable",
                **unavailable.details,
            )
            return ChangeDispenseResult(
                request_id=request.request_id,
                status=PayoutStatus.FAILED,
                details={"fault_code": unavailable.code.value, **unavailable.details},
            )

        if not await self.can_dispense(request):
            return ChangeDispenseResult(
                request_id=request.request_id,
                status=PayoutStatus.FAILED,
                details={"reason": "insufficient_inventory"},
            )

        partial = self.injector.consume(SimulatorFaultCode.PARTIAL_PAYOUT)
        if partial is not None:
            paid = self._partial_plan(request.counts_by_denomination)
            self._consume_inventory(paid)
            self._activate_fault(
                code=partial.code.value,
                message=partial.message or "partial payout",
                critical=False,
                **partial.details,
            )
            return ChangeDispenseResult(
                request_id=request.request_id,
                status=PayoutStatus.PARTIAL,
                paid_counts_by_denomination=paid,
                details={"fault_code": partial.code.value, **partial.details},
            )

        self._consume_inventory(request.counts_by_denomination)
        self._heartbeat(state=DeviceOperationalState.READY, inventory=dict(self._inventory))
        return ChangeDispenseResult(
            request_id=request.request_id,
            status=PayoutStatus.DISPENSED,
            paid_counts_by_denomination=dict(request.counts_by_denomination),
        )

    async def get_accounting_inventory(self) -> dict[int, int]:
        return dict(self._inventory)

    def _consume_inventory(self, plan: dict[int, int]) -> None:
        for denomination, count in plan.items():
            self._inventory[denomination] = self._inventory.get(denomination, 0) - count

    def _partial_plan(self, requested: dict[int, int]) -> dict[int, int]:
        paid: dict[int, int] = {}
        remaining_skip = 1
        for denomination in sorted(requested.keys(), reverse=True):
            count = requested[denomination]
            if count <= 0:
                continue
            paid_count = count
            if remaining_skip > 0:
                paid_count = max(0, count - 1)
                remaining_skip -= count - paid_count
            if paid_count > 0:
                paid[denomination] = paid_count
        if not paid:
            raise DeviceAdapterError("partial payout plan would dispense nothing")
        return paid
