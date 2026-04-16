"""Service and diagnostics presentation logic."""

from __future__ import annotations

from flower_vending.ui.facade import DiagnosticsSnapshot
from flower_vending.ui.viewmodels.common import ActionButtonViewModel
from flower_vending.ui.viewmodels.screens import (
    DiagnosticsDeviceViewModel,
    DiagnosticsScreenViewModel,
    ServiceScreenViewModel,
)


_SIMULATOR_ACTION_LABELS = {
    "open_service_door": "Открыть сервисную дверь",
    "close_service_door": "Закрыть сервисную дверь",
    "raise_temperature_critical": "Поднять температуру",
    "restore_temperature_nominal": "Восстановить температуру",
    "inject_validator_unavailable": "Отключить купюроприемник",
    "inject_bill_rejected": "Следующая купюра отклоняется",
    "inject_bill_jam": "Следующая купюра застрянет",
    "inject_payout_unavailable": "Отключить выдачу сдачи",
    "inject_partial_payout": "Сымитировать частичную сдачу",
    "inject_motor_fault": "Сымитировать ошибку мотора",
    "inject_window_fault": "Сымитировать ошибку окна выдачи",
    "inject_inventory_mismatch": "Сымитировать ошибку наличия товара",
    "restore_inventory_match": "Восстановить датчик наличия",
    "clear_simulator_faults": "Сбросить ошибки симулятора",
    "force_pickup_timeout_now": "Сразу вызвать таймаут получения",
}


class ServicePresenter:
    def present_service_dashboard(
        self,
        diagnostics: DiagnosticsSnapshot,
        *,
        simulator_actions: tuple[str, ...] = (),
    ) -> ServiceScreenViewModel:
        notes = [
            f"Состояние автомата: {diagnostics.machine.machine_state}",
            f"Активные блокировки: {', '.join(diagnostics.machine.sale_blockers) or 'нет'}",
        ]
        if diagnostics.unresolved_transaction_ids:
            notes.append(
                "Незавершенные транзакции: " + ", ".join(diagnostics.unresolved_transaction_ids)
            )
        if diagnostics.recent_events:
            notes.append(
                "Последние события: "
                + " | ".join(event.event_type for event in diagnostics.recent_events[-3:])
            )
        actions = [
            ActionButtonViewModel("show_diagnostics", "Диагностика"),
            *[
                ActionButtonViewModel(action_id, _SIMULATOR_ACTION_LABELS.get(action_id, action_id))
                for action_id in simulator_actions
            ],
            ActionButtonViewModel("exit_service", "Выйти из сервиса"),
        ]
        return ServiceScreenViewModel(
            title="Сервис и симулятор",
            subtitle="Панель оператора отделена от клиентской покупки",
            actions=tuple(actions),
            notes=tuple(notes),
        )

    def present_diagnostics(self, diagnostics: DiagnosticsSnapshot) -> DiagnosticsScreenViewModel:
        devices = tuple(
            DiagnosticsDeviceViewModel(
                device_name=device.device_name,
                state=device.state,
                fault_codes=device.fault_codes,
            )
            for device in diagnostics.devices
        )
        recent_events = tuple(
            f"{event.event_type} [{event.correlation_id}] {event.summary}"
            for event in diagnostics.recent_events[-8:]
        )
        return DiagnosticsScreenViewModel(
            title="Диагностика устройств",
            subtitle="Текущее состояние runtime и симулятора",
            machine_state=diagnostics.machine.machine_state,
            sale_blockers=diagnostics.machine.sale_blockers,
            unresolved_transactions=diagnostics.unresolved_transaction_ids,
            devices=devices,
            recent_events=recent_events,
            primary_action=ActionButtonViewModel("back_to_service", "Назад"),
        )
