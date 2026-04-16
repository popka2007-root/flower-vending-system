"""Formatting helpers shared by UI presenters."""

from __future__ import annotations


def format_money(minor_units: int, currency_code: str) -> str:
    currency = currency_code.upper()
    if currency == "RUB":
        sign = "-" if minor_units < 0 else ""
        absolute_minor = abs(minor_units)
        rubles, kopeks = divmod(absolute_minor, 100)
        ruble_text = f"{rubles:,}".replace(",", " ")
        if kopeks:
            ruble_text = f"{ruble_text},{kopeks:02d}"
        return f"{sign}{ruble_text} ₽"

    major = minor_units / 100
    return f"{major:,.2f} {currency}".replace(",", " ")
