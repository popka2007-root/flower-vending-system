from __future__ import annotations

import unittest

from flower_vending.simulators.control import EventLogEntry
from flower_vending.ui.facade import (
    DeviceDiagnosticsRow,
    DiagnosticsSnapshot,
    MachineUiSnapshot,
)
from flower_vending.ui.presenters.payment_presenter import PaymentPresenter
from flower_vending.ui.presenters.service_presenter import ServicePresenter
from flower_vending.ui.presenters.status_presenter import StatusPresenter
from flower_vending.ui.viewmodels.common import BannerTone


class PresenterTests(unittest.TestCase):
    def test_payment_presenter_exposes_simulator_quick_insert_buttons(self) -> None:
        presenter = PaymentPresenter()
        model = presenter.present_payment(
            transaction=type(
                "Tx",
                (),
                {
                    "product_name": "Розы Эквадор 7 шт.",
                    "price_minor_units": 249000,
                    "currency_code": "RUB",
                    "accepted_minor_units": 50000,
                    "change_due_minor_units": 0,
                },
            )(),
            machine=MachineUiSnapshot(
                machine_state="ACCEPTING_CASH",
                exact_change_only=False,
                sale_blockers=(),
                allow_cash_sales=True,
                allow_vending=True,
                service_mode=False,
                active_transaction_id="tx-1",
            ),
            quick_insert_denominations=(50000, 100000),
        )
        self.assertEqual(
            tuple(action.action_id for action in model.quick_insert_actions),
            ("insert_bill:50000", "insert_bill:100000"),
        )
        self.assertEqual(tuple(action.label for action in model.quick_insert_actions), ("500 ₽", "1 000 ₽"))

    def test_payment_presenter_humanizes_validator_warnings(self) -> None:
        presenter = PaymentPresenter()
        model = presenter.present_payment(
            transaction=type(
                "Tx",
                (),
                {
                    "product_name": "Розы Эквадор 7 шт.",
                    "price_minor_units": 249000,
                    "currency_code": "RUB",
                    "accepted_minor_units": 0,
                    "change_due_minor_units": 0,
                },
            )(),
            machine=MachineUiSnapshot(
                machine_state="ACCEPTING_CASH",
                exact_change_only=False,
                sale_blockers=(),
                allow_cash_sales=True,
                allow_vending=True,
                service_mode=False,
                active_transaction_id="tx-1",
            ),
            warning_message="simulator bill rejected",
        )
        assert model.banner is not None
        self.assertEqual(
            model.banner.message,
            "Купюра не принята. Проверьте купюру или попробуйте другую.",
        )

    def test_service_presenter_includes_simulator_actions_and_recent_events(self) -> None:
        presenter = ServicePresenter()
        diagnostics = DiagnosticsSnapshot(
            machine=MachineUiSnapshot(
                machine_state="IDLE",
                exact_change_only=False,
                sale_blockers=("service_door_open",),
                allow_cash_sales=False,
                allow_vending=False,
                service_mode=True,
                active_transaction_id=None,
            ),
            devices=(DeviceDiagnosticsRow("validator", "ready", ()),),
            unresolved_transaction_ids=("tx-1",),
            recent_events=(
                EventLogEntry(
                    timestamp="2026-04-15T00:00:00+00:00",
                    event_type="service_door_opened",
                    correlation_id="corr-1",
                    transaction_id=None,
                    summary="door opened",
                ),
            ),
        )
        model = presenter.present_service_dashboard(
            diagnostics,
            simulator_actions=("open_service_door", "inject_motor_fault"),
        )
        self.assertIn("Диагностика", tuple(action.label for action in model.actions))
        self.assertIn("Открыть сервисную дверь", tuple(action.label for action in model.actions))
        self.assertTrue(any("Последние события" in note for note in model.notes))

    def test_status_presenter_restricted_mode_is_explicit(self) -> None:
        presenter = StatusPresenter()
        model = presenter.present_restricted_mode(details=("manual_review_required", "partial_payout"))
        self.assertEqual(model.title, "Нужна проверка оператора")
        assert model.banner is not None
        assert model.primary_action is not None
        self.assertEqual(model.banner.tone, BannerTone.ERROR)
        self.assertEqual(model.primary_action.action_id, "open_service")


if __name__ == "__main__":
    unittest.main()
