"""Top-level kiosk presenter coordinating navigation and screen rendering."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from flower_vending.domain.events import DomainEvent
from flower_vending.domain.exceptions import (
    ChangeUnavailableError,
    FlowerVendingError,
    ManualInterventionRequiredError,
)
from flower_vending.ui.facade import CatalogEntry, UiApplicationFacade
from flower_vending.ui.navigation import NavigationState, ScreenId
from flower_vending.ui.presenters.catalog_presenter import CatalogPresenter
from flower_vending.ui.presenters.payment_presenter import PaymentPresenter
from flower_vending.ui.presenters.service_presenter import ServicePresenter
from flower_vending.ui.presenters.status_presenter import StatusPresenter
from flower_vending.ui.session import KioskSessionState


ViewListener = Callable[["ScreenRender"], None]


@dataclass(frozen=True, slots=True)
class ScreenRender:
    screen_id: ScreenId
    model: Any


class KioskPresenter:
    def __init__(
        self,
        facade: UiApplicationFacade,
        *,
        navigation: NavigationState | None = None,
        session: KioskSessionState | None = None,
        catalog_presenter: CatalogPresenter | None = None,
        payment_presenter: PaymentPresenter | None = None,
        status_presenter: StatusPresenter | None = None,
        service_presenter: ServicePresenter | None = None,
    ) -> None:
        self._facade = facade
        self._navigation = navigation or NavigationState()
        self._session = session or KioskSessionState()
        self._catalog_presenter = catalog_presenter or CatalogPresenter()
        self._payment_presenter = payment_presenter or PaymentPresenter()
        self._status_presenter = status_presenter or StatusPresenter()
        self._service_presenter = service_presenter or ServicePresenter()
        self._listeners: list[ViewListener] = []

    def subscribe(self, listener: ViewListener) -> None:
        self._listeners.append(listener)

    async def initialize(self) -> ScreenRender:
        self._facade.subscribe_events(self.handle_domain_event)
        return await self.show_home()

    async def show_home(self) -> ScreenRender:
        self._session.reset_purchase()
        self._navigation.reset(ScreenId.HOME)
        return await self._emit_current_render()

    async def show_catalog(self) -> ScreenRender:
        self._navigation.go_to(ScreenId.CATALOG)
        return await self._emit_current_render()

    async def show_product_details(self, product_id: str, slot_id: str) -> ScreenRender:
        entry = self._facade.get_catalog_entry(product_id, slot_id)
        self._session.select_product(
            product_id=entry.product_id,
            slot_id=entry.slot_id,
            product_name=entry.display_name,
            price_minor_units=entry.price_minor_units,
            currency_code=entry.currency_code,
        )
        self._navigation.go_to(ScreenId.PRODUCT_DETAILS)
        return await self._emit_current_render()

    async def start_cash_checkout(self) -> ScreenRender:
        if self._session.selected_product_id is None or self._session.selected_slot_id is None:
            return await self._show_error("Выбор не завершен", "Сначала выберите товар.")
        correlation_id = self._facade.new_correlation_id()
        try:
            transaction_id = await self._facade.start_cash_checkout(
                product_id=self._session.selected_product_id,
                slot_id=self._session.selected_slot_id,
                correlation_id=correlation_id,
            )
        except ChangeUnavailableError as exc:
            self._session.last_warning_message = str(exc)
            self._navigation.go_to(ScreenId.NO_CHANGE)
            return await self._emit_current_render()
        except FlowerVendingError as exc:
            return await self._show_error("Оплата недоступна", str(exc))
        self._session.start_transaction(transaction_id)
        self._navigation.go_to(ScreenId.PAYMENT)
        return await self._emit_current_render()

    async def cancel_purchase(self) -> ScreenRender:
        if self._session.active_transaction_id is None:
            return await self.show_catalog()
        correlation_id = self._facade.new_correlation_id()
        try:
            await self._facade.cancel_purchase(
                transaction_id=self._session.active_transaction_id,
                correlation_id=correlation_id,
            )
        except FlowerVendingError as exc:
            return await self._show_error("Не удалось отменить покупку", str(exc))
        return await self.show_home()

    async def confirm_pickup(self) -> ScreenRender:
        if self._session.active_transaction_id is None:
            return await self.show_home()
        correlation_id = self._facade.new_correlation_id()
        try:
            await self._facade.confirm_pickup(
                transaction_id=self._session.active_transaction_id,
                correlation_id=correlation_id,
            )
        except FlowerVendingError as exc:
            return await self._show_error("Не удалось завершить выдачу", str(exc))
        return await self.show_home()

    async def open_service_mode(self, operator_id: str = "technician") -> ScreenRender:
        correlation_id = self._facade.new_correlation_id()
        try:
            await self._facade.enter_service_mode(
                operator_id=operator_id,
                correlation_id=correlation_id,
            )
        except FlowerVendingError as exc:
            return await self._show_error("Не удалось открыть сервисный режим", str(exc))
        self._navigation.go_to(ScreenId.SERVICE)
        return await self._emit_current_render()

    async def exit_service_mode(self, operator_id: str = "technician") -> ScreenRender:
        correlation_id = self._facade.new_correlation_id()
        try:
            await self._facade.exit_service_mode(
                correlation_id=correlation_id,
                operator_id=operator_id,
            )
        except FlowerVendingError as exc:
            return await self._show_error("Не удалось выйти из сервиса", str(exc))
        return await self.show_home()

    async def show_diagnostics(self) -> ScreenRender:
        self._navigation.go_to(ScreenId.DIAGNOSTICS)
        return await self._emit_current_render()

    async def recover_transaction(self, transaction_id: str) -> ScreenRender:
        correlation_id = self._facade.new_correlation_id()
        try:
            await self._facade.recover_transaction(
                transaction_id=transaction_id,
                correlation_id=correlation_id,
            )
        except ManualInterventionRequiredError as exc:
            self._session.record_restricted("manual_review_required", str(exc))
            self._navigation.go_to(ScreenId.RESTRICTED)
            return await self._emit_current_render()
        except FlowerVendingError as exc:
            return await self._show_error("Восстановление не выполнено", str(exc))
        self._session.last_warning_message = "Выполняется безопасное восстановление транзакции."
        self._navigation.go_to(ScreenId.RESTRICTED)
        return await self._emit_current_render()

    async def insert_simulated_bill(self, bill_minor_units: int) -> ScreenRender:
        correlation_id = self._facade.new_correlation_id()
        try:
            await self._facade.insert_simulated_bill(
                bill_minor_units=bill_minor_units,
                correlation_id=correlation_id,
            )
        except FlowerVendingError as exc:
            return await self._show_error("Симуляция купюры не выполнена", str(exc))
        return await self._emit_current_render()

    async def execute_service_action(self, action_id: str) -> ScreenRender:
        correlation_id = self._facade.new_correlation_id()
        try:
            await self._facade.execute_simulator_action(
                action_id=action_id,
                correlation_id=correlation_id,
            )
        except FlowerVendingError as exc:
            return await self._show_error("Simulator action failed", str(exc))
        if action_id == "pickup_timeout_placeholder":
            self._session.last_warning_message = (
                "Pickup timeout остается placeholder и не закрывает окно выдачи автоматически."
            )
        return await self._emit_current_render()

    async def back(self) -> ScreenRender:
        self._navigation.back()
        return await self._emit_current_render()

    async def handle_action(self, action_id: str) -> ScreenRender:
        handlers: dict[str, Callable[[], Any]] = {
            "show_catalog": self.show_catalog,
            "show_home": self.show_home,
            "open_service": self.open_service_mode,
            "confirm_pickup": self.confirm_pickup,
            "show_diagnostics": self.show_diagnostics,
            "exit_service": self.exit_service_mode,
            "back_to_service": self.back,
            "cancel_purchase": self.cancel_purchase,
        }
        if action_id.startswith("insert_bill:"):
            return await self.insert_simulated_bill(int(action_id.split(":", maxsplit=1)[1]))
        if action_id in self._facade.simulator_action_ids():
            return await self.execute_service_action(action_id)
        handler = handlers.get(action_id)
        if handler is None:
            return await self._emit_current_render()
        return await handler()

    async def handle_domain_event(self, event: DomainEvent) -> None:
        if event.event_type == "cash_amount_updated":
            self._session.accepted_minor_units = int(event.payload.get("accepted_minor_units", 0))
            self._navigation.go_to(ScreenId.PAYMENT)
        elif event.event_type == "payment_confirmed":
            self._session.accepted_minor_units = int(event.payload.get("accepted_minor_units", 0))
            self._session.change_due_minor_units = int(event.payload.get("change_due_minor_units", 0))
            self._navigation.go_to(ScreenId.DISPENSING)
        elif event.event_type in {
            "change_dispense_requested",
            "change_dispensed",
            "product_dispense_requested",
            "product_dispensed",
        }:
            self._navigation.go_to(ScreenId.DISPENSING)
        elif event.event_type == "delivery_window_opened":
            self._navigation.go_to(ScreenId.PICKUP)
        elif event.event_type in {"transaction_completed", "transaction_cancelled"}:
            self._session.reset_purchase()
            self._navigation.reset(ScreenId.HOME)
        elif event.event_type in {"machine_faulted"}:
            faults = tuple(str(item) for item in event.payload.get("faults", ()))
            self._session.record_error(
                title="Требуется вмешательство",
                message=", ".join(faults) or event.event_type,
            )
            self._navigation.go_to(ScreenId.ERROR)
        elif event.event_type in {"manual_review_required", "recovery_started"}:
            self._session.record_restricted(
                str(event.payload.get("action", "recovery")),
                str(event.payload.get("reason", event.event_type)),
            )
            self._navigation.go_to(ScreenId.RESTRICTED)
        elif event.event_type == "pickup_timeout_placeholder_requested":
            self._session.record_restricted(
                "pickup_timeout_placeholder",
                str(event.payload.get("warning", "pickup timeout placeholder")),
            )
            self._navigation.go_to(ScreenId.RESTRICTED)
        elif event.event_type == "critical_temperature_detected":
            self._session.last_warning_message = "Продажи остановлены из-за критической температуры."
            self._navigation.go_to(ScreenId.SALES_BLOCKED)
        elif event.event_type == "service_door_opened":
            self._session.last_warning_message = "Продажи остановлены: открыта сервисная дверь."
            self._navigation.go_to(ScreenId.SALES_BLOCKED)
        await self._emit_current_render()

    async def _emit_current_render(self) -> ScreenRender:
        render = self._build_current_render()
        for listener in self._listeners:
            listener(render)
        return render

    def _build_current_render(self) -> ScreenRender:
        machine = self._facade.machine_snapshot()
        self._session.sale_blockers = set(machine.sale_blockers)
        screen_id = self._navigation.current_screen

        if (
            machine.machine_state == "RECOVERY_PENDING" or "recovery_pending" in machine.sale_blockers
        ) and screen_id not in {ScreenId.SERVICE, ScreenId.DIAGNOSTICS, ScreenId.ERROR, ScreenId.RESTRICTED}:
            screen_id = ScreenId.RESTRICTED
        elif machine.sale_blockers and screen_id not in {
            ScreenId.SERVICE,
            ScreenId.DIAGNOSTICS,
            ScreenId.ERROR,
            ScreenId.RESTRICTED,
        }:
            screen_id = ScreenId.SALES_BLOCKED
        elif screen_id is ScreenId.HOME and machine.exact_change_only:
            screen_id = ScreenId.EXACT_CHANGE

        if screen_id in {ScreenId.HOME, ScreenId.CATALOG}:
            title = "Цветочный автомат" if screen_id is ScreenId.HOME else "Каталог"
            subtitle = (
                "Выберите свежие цветы или букет"
                if screen_id is ScreenId.HOME
                else "Доступные позиции"
            )
            model = self._catalog_presenter.present_catalog(
                title=title,
                subtitle=subtitle,
                entries=self._facade.catalog_entries(),
                machine=machine,
            )
            return ScreenRender(screen_id, model)

        if screen_id is ScreenId.PRODUCT_DETAILS:
            entry = self._selected_entry()
            model = self._catalog_presenter.present_product_details(entry=entry, machine=machine)
            return ScreenRender(screen_id, model)

        if screen_id is ScreenId.PAYMENT:
            transaction = self._facade.active_transaction_snapshot()
            if transaction is None:
                return ScreenRender(
                    ScreenId.ERROR,
                    self._status_presenter.present_error(
                        title="Сессия оплаты потеряна",
                        message="Активная транзакция не найдена.",
                    ),
                )
            model = self._payment_presenter.present_payment(
                transaction=transaction,
                machine=machine,
                quick_insert_denominations=self._facade.quick_insert_denominations(),
                warning_message=self._session.last_warning_message,
            )
            return ScreenRender(screen_id, model)

        if screen_id is ScreenId.DISPENSING:
            model = self._status_presenter.present_dispensing(
                product_name=self._session.selected_product_name or "товар",
            )
            return ScreenRender(screen_id, model)

        if screen_id is ScreenId.PICKUP:
            model = self._status_presenter.present_pickup(
                product_name=self._session.selected_product_name or "товар",
            )
            return ScreenRender(screen_id, model)

        if screen_id is ScreenId.EXACT_CHANGE:
            return ScreenRender(screen_id, self._status_presenter.present_exact_change_only())

        if screen_id is ScreenId.NO_CHANGE:
            return ScreenRender(
                screen_id,
                self._status_presenter.present_no_change(
                    message=self._session.last_warning_message or "Сдача недоступна для безопасной продажи.",
                ),
            )

        if screen_id is ScreenId.SALES_BLOCKED:
            return ScreenRender(screen_id, self._status_presenter.present_sales_blocked(machine))

        if screen_id is ScreenId.RESTRICTED:
            details = self._session.restricted_details or tuple(sorted(machine.sale_blockers)) or (
                "manual_review_required",
            )
            return ScreenRender(
                screen_id,
                self._status_presenter.present_restricted_mode(details=details),
            )

        if screen_id is ScreenId.SERVICE:
            diagnostics = self._facade.diagnostics_snapshot()
            return ScreenRender(
                screen_id,
                self._service_presenter.present_service_dashboard(
                    diagnostics,
                    simulator_actions=self._facade.simulator_action_ids(),
                ),
            )

        if screen_id is ScreenId.DIAGNOSTICS:
            diagnostics = self._facade.diagnostics_snapshot()
            return ScreenRender(screen_id, self._service_presenter.present_diagnostics(diagnostics))

        return ScreenRender(
            ScreenId.ERROR,
            self._status_presenter.present_error(
                title=self._session.last_error_title or "Ошибка автомата",
                message=self._session.last_error_message or "Произошла непредвиденная ошибка.",
            ),
        )

    async def _show_error(self, title: str, message: str) -> ScreenRender:
        self._session.record_error(title=title, message=message)
        self._navigation.go_to(ScreenId.ERROR)
        return await self._emit_current_render()

    def _selected_entry(self) -> CatalogEntry:
        if self._session.selected_product_id is None or self._session.selected_slot_id is None:
            raise RuntimeError("no product has been selected")
        return self._facade.get_catalog_entry(
            self._session.selected_product_id,
            self._session.selected_slot_id,
        )
