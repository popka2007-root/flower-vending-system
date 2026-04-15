"""Formatting helpers shared by UI presenters."""

from __future__ import annotations


def format_money(minor_units: int, currency_code: str) -> str:
    major = minor_units / 100
    suffix = "₽" if currency_code.upper() == "RUB" else currency_code.upper()
    return f"{major:,.2f} {suffix}".replace(",", " ")
