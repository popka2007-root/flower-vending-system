"""Navigation state for kiosk screen flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ScreenId(StrEnum):
    HOME = "home"
    CATALOG = "catalog"
    PRODUCT_DETAILS = "product_details"
    PAYMENT = "payment"
    EXACT_CHANGE = "exact_change"
    NO_CHANGE = "no_change"
    DISPENSING = "dispensing"
    PICKUP = "pickup"
    ERROR = "error"
    SALES_BLOCKED = "sales_blocked"
    RESTRICTED = "restricted"
    SERVICE = "service"
    DIAGNOSTICS = "diagnostics"


@dataclass(slots=True)
class NavigationState:
    current_screen: ScreenId = ScreenId.HOME
    history: list[ScreenId] = field(default_factory=list)

    def go_to(self, screen_id: ScreenId) -> ScreenId:
        if self.current_screen != screen_id:
            self.history.append(self.current_screen)
            self.current_screen = screen_id
        return self.current_screen

    def reset(self, screen_id: ScreenId = ScreenId.HOME) -> ScreenId:
        self.history.clear()
        self.current_screen = screen_id
        return self.current_screen

    def back(self) -> ScreenId:
        if not self.history:
            return self.current_screen
        self.current_screen = self.history.pop()
        return self.current_screen
