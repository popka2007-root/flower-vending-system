"""Presentation logic for machine status, blocking, and delivery screens."""

from __future__ import annotations

from flower_vending.ui.facade import MachineUiSnapshot
from flower_vending.ui.viewmodels.common import ActionButtonViewModel, BannerTone, BannerViewModel
from flower_vending.ui.viewmodels.screens import DeliveryScreenViewModel, StatusScreenViewModel


class StatusPresenter:
    def present_exact_change_only(self) -> StatusScreenViewModel:
        return StatusScreenViewModel(
            title="Только точная сумма",
            message="Автомат временно работает в режиме без гарантированной сдачи.",
            details=("Вы можете посмотреть каталог, но оплата останется в безопасном simulator-safe режиме.",),
            banner=BannerViewModel(
                title="Режим exact change only",
                message="Это безопасный режим, пока выдача сдачи ограничена.",
                tone=BannerTone.WARNING,
            ),
            primary_action=ActionButtonViewModel("show_catalog", "Показать каталог"),
            secondary_action=ActionButtonViewModel("open_service", "Сервис"),
        )

    def present_no_change(self, *, message: str) -> StatusScreenViewModel:
        return StatusScreenViewModel(
            title="Нет сдачи",
            message=message,
            details=("Проверьте настройки симулятора или выберите другой сценарий оплаты.",),
            banner=BannerViewModel(
                title="Сессия оплаты не начата",
                message="Автомат не будет принимать оплату, пока не сможет безопасно завершить выдачу.",
                tone=BannerTone.WARNING,
            ),
            primary_action=ActionButtonViewModel("show_catalog", "Назад к каталогу"),
            secondary_action=ActionButtonViewModel("open_service", "Сервис"),
        )

    def present_sales_blocked(self, machine: MachineUiSnapshot) -> StatusScreenViewModel:
        humanized = tuple(self._humanize_blocker(item) for item in machine.sale_blockers)
        return StatusScreenViewModel(
            title="Продажа временно недоступна",
            message="Автомат переведен в безопасный режим и не принимает оплату.",
            details=humanized,
            banner=BannerViewModel(
                title="Продажи заблокированы",
                message="Причина должна быть устранена до возобновления работы.",
                tone=BannerTone.ERROR,
            ),
            secondary_action=ActionButtonViewModel("open_service", "Диагностика"),
        )

    def present_restricted_mode(self, *, details: tuple[str, ...]) -> StatusScreenViewModel:
        return StatusScreenViewModel(
            title="Recovery / restricted mode",
            message="Автомат требует безопасного вмешательства сервисного инженера.",
            details=details,
            banner=BannerViewModel(
                title="Manual review required",
                message="Runtime сохранил ограниченный режим и не пытается скрыть неоднозначное состояние.",
                tone=BannerTone.ERROR,
            ),
            primary_action=ActionButtonViewModel("open_service", "Открыть сервисный экран"),
            secondary_action=ActionButtonViewModel("show_home", "На главный экран"),
        )

    def present_error(self, *, title: str, message: str, details: tuple[str, ...] = ()) -> StatusScreenViewModel:
        return StatusScreenViewModel(
            title=title,
            message=message,
            details=details,
            banner=BannerViewModel(
                title="Требуется внимание",
                message=message,
                tone=BannerTone.ERROR,
            ),
            primary_action=ActionButtonViewModel("show_home", "На главный экран"),
            secondary_action=ActionButtonViewModel("open_service", "Сервис"),
        )

    def present_dispensing(self, *, product_name: str) -> DeliveryScreenViewModel:
        return DeliveryScreenViewModel(
            title="Товар выдается",
            message=f"Подготавливаем выдачу: {product_name}.",
            details=("Пожалуйста, не отходите от автомата до завершения операции.",),
            banner=BannerViewModel(
                title="Идет выдача",
                message="Сначала завершится транзакция, затем откроется окно выдачи.",
                tone=BannerTone.INFO,
            ),
        )

    def present_pickup(self, *, product_name: str) -> DeliveryScreenViewModel:
        return DeliveryScreenViewModel(
            title="Заберите товар",
            message=f"Ваш заказ готов: {product_name}.",
            details=("После получения подтвердите завершение операции на экране.",),
            banner=BannerViewModel(
                title="Окно выдачи открыто",
                message="Заберите товар и подтвердите завершение операции.",
                tone=BannerTone.SUCCESS,
            ),
            primary_action=ActionButtonViewModel("confirm_pickup", "Забрал(а)"),
        )

    def _humanize_blocker(self, blocker: str) -> str:
        mapping = {
            "critical_temperature": "Критическая температура в охлаждаемой камере.",
            "device_fault": "Обнаружена критическая неисправность устройства.",
            "service_door_open": "Открыта сервисная дверь.",
            "recovery_pending": "Ожидается безопасное восстановление транзакции.",
            "validator_fault": "Купюроприемник недоступен.",
        }
        return mapping.get(blocker, blocker.replace("_", " "))
