"""
Модуль для работы с московским временем (UTC+3)
"""

from datetime import datetime, timezone, timedelta

# Московский часовой пояс (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))


def now() -> datetime:
    """Получить текущее московское время"""
    return datetime.now(MOSCOW_TZ)


def now_naive() -> datetime:
    """Получить текущее московское время без timezone info (для совместимости)"""
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


def today() -> datetime:
    """Получить начало сегодняшнего дня по Москве"""
    msk = now_naive()
    return msk.replace(hour=0, minute=0, second=0, microsecond=0)


def to_moscow(dt: datetime) -> datetime:
    """Конвертировать datetime в московское время"""
    if dt.tzinfo is None:
        # Если время без timezone - считаем что это UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MOSCOW_TZ)


def from_utc(dt: datetime) -> datetime:
    """Конвертировать UTC в московское время"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MOSCOW_TZ).replace(tzinfo=None)


def format_time(dt: datetime = None, fmt: str = "%H:%M") -> str:
    """Форматировать время (по умолчанию - текущее московское)"""
    if dt is None:
        dt = now_naive()
    return dt.strftime(fmt)


def format_date(dt: datetime = None, fmt: str = "%d.%m.%Y") -> str:
    """Форматировать дату (по умолчанию - сегодня по Москве)"""
    if dt is None:
        dt = now_naive()
    return dt.strftime(fmt)


def format_datetime(dt: datetime = None, fmt: str = "%d.%m.%Y %H:%M") -> str:
    """Форматировать дату и время (по умолчанию - текущее московское)"""
    if dt is None:
        dt = now_naive()
    return dt.strftime(fmt)
