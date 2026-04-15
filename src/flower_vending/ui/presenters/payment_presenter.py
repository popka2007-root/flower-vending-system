"""Payment screen presentation logic."""

from __future__ import annotations

from flower_vending.ui.facade import MachineUiSnapshot, TransactionUiSnapshot
from flower_vending.ui.presenters.formatting import format_money
from flower_vending.ui.viewmodels.common import ActionButtonViewModel, BannerTone, BannerViewModel
from flower_vending.ui.viewmodels.screens import PaymentScreenViewModel


class PaymentPresenter:
    def present_payment(
        self,
        *,
        transaction: TransactionUiSnapshot,
        machine: MachineUiSnapshot,
        quick_insert_denominations: tuple[int, ...] = (),
        warning_message: str | None = None,
    ) -> PaymentScreenViewModel:
        remaining_minor = max(0, transaction.price_minor_units - transaction.accepted_minor_units)
        banner = None
        if warning_message:
            banner = BannerViewModel(
                title="Внимание",
                message=warning_message,
                tone=BannerTone.WARNING,
            )
        elif machine.exact_change_only:
            banner = BannerViewModel(
                title="Точная сумма",
                message="Сдача не гарантируется. Внесите точную стоимость товара.",
                tone=BannerTone.WARNING,
            )
        return PaymentScreenViewModel(
            title="Оплата наличными",
            subtitle="Внесите купюры в купюроприемник",
            product_name=transaction.product_name,
            price_text=format_money(transaction.price_minor_units, transaction.currency_code),
            accepted_text=format_money(transaction.accepted_minor_units, transaction.currency_code),
            remaining_text=format_money(remaining_minor, transaction.currency_code),
            change_text=format_money(transaction.change_due_minor_units, transaction.currency_code),
            help_text="Товар выдается только после подтвержденной оплаты и завершения выдачи сдачи.",
            banner=banner,
            cancel_action=ActionButtonViewModel("cancel_purchase", "Отменить покупку"),
            quick_insert_actions=tuple(
                ActionButtonViewModel(
                    action_id=f"insert_bill:{denomination}",
                    label=f"+{format_money(denomination, transaction.currency_code)}",
                )
                for denomination in quick_insert_denominations
            ),
        )
