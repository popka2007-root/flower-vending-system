"""Presentation logic for machine status, blocking, and delivery screens."""

from __future__ import annotations

from flower_vending.ui.facade import MachineUiSnapshot
from flower_vending.ui.viewmodels.common import ActionButtonViewModel, BannerTone, BannerViewModel
from flower_vending.ui.viewmodels.screens import DeliveryScreenViewModel, StatusScreenViewModel


class StatusPresenter:
    def present_exact_change_only(self) -> StatusScreenViewModel:
        return StatusScreenViewModel(
            title="Только точная сумма",
            message="Автомат временно работает без гарантированной сдачи.",
            details=("Каталог доступен. При оплате внесите ровно стоимость выбранного букета.",),
            banner=BannerViewModel(
                title="Сдача ограничена",
                message="Покупка безопасна только при точной сумме.",
                tone=BannerTone.WARNING,
            ),
            primary_action=ActionButtonViewModel("show_catalog", "Показать каталог"),
            secondary_action=ActionButtonViewModel("open_service", "Сервис"),
        )

    def present_no_change(self, *, message: str) -> StatusScreenViewModel:
        return StatusScreenViewModel(
            title="Сдача недоступна",
            message=self._humanize_blocker(message),
            details=("Выберите букет на точную сумму или обратитесь к оператору.",),
            banner=BannerViewModel(
                title="Оплата не начата",
                message="Автомат не примет деньги, пока не сможет безопасно завершить покупку.",
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
                title="Покупка остановлена",
                message="Нужно устранить причину блокировки перед продажей.",
                tone=BannerTone.ERROR,
            ),
            secondary_action=ActionButtonViewModel("open_service", "Открыть сервис"),
        )

    def present_restricted_mode(self, *, details: tuple[str, ...]) -> StatusScreenViewModel:
        return StatusScreenViewModel(
            title="Нужна проверка оператора",
            message="Автомат сохранил небезопасное состояние и ждет сервисного подтверждения.",
            details=tuple(self._humanize_blocker(item) for item in details),
            banner=BannerViewModel(
                title="Сервисная проверка",
                message="Клиентская продажа остановлена до восстановления автомата.",
                tone=BannerTone.ERROR,
            ),
            primary_action=ActionButtonViewModel("open_service", "Открыть сервисный экран"),
            secondary_action=ActionButtonViewModel("show_home", "На главный экран"),
        )

    def present_error(
        self,
        *,
        title: str,
        message: str,
        details: tuple[str, ...] = (),
    ) -> StatusScreenViewModel:
        human_message = self._humanize_blocker(message)
        return StatusScreenViewModel(
            title=title,
            message=human_message,
            details=details,
            banner=BannerViewModel(
                title="Требуется внимание",
                message=human_message,
                tone=BannerTone.ERROR,
            ),
            primary_action=ActionButtonViewModel("show_home", "На главный экран"),
            secondary_action=ActionButtonViewModel("open_service", "Сервис"),
        )

    def present_dispensing(self, *, product_name: str) -> DeliveryScreenViewModel:
        return DeliveryScreenViewModel(
            title="Букет выдаётся",
            message=f"Автомат готовит к выдаче: {product_name}.",
            details=("Окно получения откроется после завершения механизма выдачи.",),
            banner=BannerViewModel(
                title="Идёт выдача",
                message="Пожалуйста, оставайтесь у автомата.",
                tone=BannerTone.INFO,
            ),
        )

    def present_pickup(
        self,
        *,
        product_name: str,
        pickup_timeout_active: bool = False,
        pickup_timeout_remaining_s: float | None = None,
    ) -> DeliveryScreenViewModel:
        timeout_status = self._pickup_timeout_status(
            active=pickup_timeout_active,
            remaining_s=pickup_timeout_remaining_s,
        )
        return DeliveryScreenViewModel(
            title="Заберите букет",
            message=f"Ваш букет готов: {product_name}.",
            details=(
                "Окно выдачи открыто. Симуляторное подтверждение находится ниже.",
                timeout_status,
            ),
            banner=BannerViewModel(
                title="Окно выдачи открыто",
                message="Заберите букет до автоматического закрытия окна.",
                tone=BannerTone.SUCCESS,
            ),
            primary_action=ActionButtonViewModel("confirm_pickup", "Симулятор: букет забран"),
        )

    def _pickup_timeout_status(self, *, active: bool, remaining_s: float | None) -> str:
        if not active:
            return "Окно закроется автоматически, если букет не забрать."
        if remaining_s is None:
            return "Окно закроется автоматически, если букет не забрать."
        return f"Окно закроется автоматически через {max(0, round(remaining_s))} с."

    def _humanize_blocker(self, blocker: str) -> str:
        normalized = blocker.lower()
        mapping = {
            "critical_temperature": "Температура в охлаждаемой камере вышла за безопасный диапазон.",
            "device_fault": "Обнаружена неисправность устройства.",
            "service_door_open": "Открыта сервисная дверь.",
            "recovery_pending": "Ожидается безопасное восстановление транзакции.",
            "validator_fault": "Купюроприемник временно недоступен.",
            "manual_review_required": "Нужна ручная проверка результата операции.",
            "partial_payout": "Сдача выдана не полностью.",
            "pickup_timeout": "Время получения истекло, окно выдачи закрывается.",
        }
        if normalized in mapping:
            return mapping[normalized]
        if "validator unavailable" in normalized or "validator" in normalized:
            return "Купюроприемник временно недоступен."
        if "bill rejected" in normalized or "rejected" in normalized:
            return "Купюра не принята. Проверьте купюру или попробуйте другую."
        if "bill jam" in normalized or "jam" in normalized:
            return "Купюра застряла. Нужна проверка автомата."
        if "change" in normalized or "payout" in normalized:
            return "Автомат не может безопасно выдать сдачу."
        if "pickup timeout" in normalized:
            return "Время получения истекло, окно выдачи закрывается."
        return blocker.replace("_", " ")
