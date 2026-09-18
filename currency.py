from enum import Enum

from validators import ensure_number


class Currency(Enum):
    USD = "USD"
    RUB = "RUB"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


RATES = {
    Currency.USD: 1.0,
    Currency.EUR: 1.09,
    Currency.RUB: 0.011,
    Currency.KZT: 0.0019,
    Currency.CNY: 0.14,
}


def convert(amount, from_currency, to_currency):
    ensure_number(amount, "amount")

    if not isinstance(from_currency, Currency):
        raise TypeError(
            f"from_currency must be a Currency member, got {from_currency!r}; "
            f"try Currency({from_currency!r})"
        )

    if not isinstance(to_currency, Currency):
        raise TypeError(
            f"to_currency must be a Currency member, got {to_currency!r}; "
            f"try Currency({to_currency!r})"
        )

    in_usd = amount * RATES[from_currency]
    return round(in_usd / RATES[to_currency], 2)
