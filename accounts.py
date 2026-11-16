from __future__ import annotations

import re

_STEAM64_BASE = 76561197960265728
_MAX_STEAM32 = 4_294_967_295
_PROFILE_PATTERNS = (
    re.compile(r"steamcommunity\.com/profiles/(\d+)", re.IGNORECASE),
    re.compile(r"opendota\.com/players/(\d+)", re.IGNORECASE),
    re.compile(r"dotabuff\.com/players/(\d+)", re.IGNORECASE),
    re.compile(r"stratz\.com/players/(\d+)", re.IGNORECASE),
)


class AccountIdError(ValueError):
    pass


def parse_account_id(raw: str) -> int:
    value = (raw or "").strip()
    if not value:
        raise AccountIdError("Введите Steam32 ID или ссылку на профиль.")

    if "steamcommunity.com/id/" in value.lower():
        raise AccountIdError(
            "Короткие ссылки /id/ не поддерживаются. Укажите числовой Steam32 ID."
        )

    digits: str | None = None
    if value.isdigit():
        digits = value
    else:
        for pattern in _PROFILE_PATTERNS:
            match = pattern.search(value)
            if match:
                digits = match.group(1)
                break
    if digits is None:
        raise AccountIdError(
            "Не удалось найти ID. Введите число, Steam64 ID или ссылку на профиль."
        )

    try:
        number = int(digits)
    except ValueError as error:
        raise AccountIdError("ID должен быть числом.") from error

    if number >= _STEAM64_BASE:
        number -= _STEAM64_BASE

    if not 1 <= number <= _MAX_STEAM32:
        raise AccountIdError("ID вне допустимого диапазона Steam32.")

    return number
