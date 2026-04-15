"""Shared view models for touch-friendly screens."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BannerTone(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class BannerViewModel:
    title: str
    message: str
    tone: BannerTone = BannerTone.INFO


@dataclass(frozen=True, slots=True)
class ActionButtonViewModel:
    action_id: str
    label: str
    enabled: bool = True
