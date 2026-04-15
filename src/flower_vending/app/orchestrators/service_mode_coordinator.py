"""Service-mode orchestration for technician workflows."""

from __future__ import annotations

from flower_vending.app.event_bus import EventBus
from flower_vending.app.fsm import MachineState, StateMachineEngine
from flower_vending.app.services.machine_status_service import MachineStatusService
from flower_vending.domain.commands.service_commands import EnterServiceMode
from flower_vending.domain.events.machine_events import machine_event


class ServiceModeCoordinator:
    def __init__(
        self,
        *,
        event_bus: EventBus,
        fsm: StateMachineEngine,
        machine_status_service: MachineStatusService,
    ) -> None:
        self._event_bus = event_bus
        self._fsm = fsm
        self._machine_status_service = machine_status_service

    async def enter_service_mode(self, command: EnterServiceMode) -> str:
        if self._fsm.can_transition(MachineState.SERVICE_MODE):
            self._fsm.transition(MachineState.SERVICE_MODE, command.reason)
        else:
            self._fsm.force_state(MachineState.SERVICE_MODE, command.reason)
        self._machine_status_service.set_service_mode(True)
        self._machine_status_service.set_machine_state(self._fsm.current_state)
        await self._event_bus.publish(
            machine_event(
                "service_mode_entered",
                correlation_id=command.correlation_id,
                operator_id=command.operator_id,
                reason=command.reason,
            )
        )
        return self._fsm.current_state.value

    async def exit_service_mode(
        self,
        *,
        correlation_id: str,
        reason: str = "service_mode_exit",
        operator_id: str | None = None,
    ) -> str:
        self._machine_status_service.set_service_mode(False)
        if self._fsm.can_transition(MachineState.IDLE):
            self._fsm.transition(MachineState.IDLE, reason)
        else:
            self._fsm.force_state(MachineState.IDLE, reason)
        self._machine_status_service.set_machine_state(self._fsm.current_state)
        await self._event_bus.publish(
            machine_event(
                "service_mode_exited",
                correlation_id=correlation_id,
                operator_id=operator_id,
                reason=reason,
            )
        )
        return self._fsm.current_state.value
