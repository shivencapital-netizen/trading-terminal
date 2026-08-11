from datetime import datetime, time
from zoneinfo import ZoneInfo


EASTERN_TZ = ZoneInfo("America/New_York")
REGULAR_MARKET_OPEN = time(9, 30)
REGULAR_MARKET_CLOSE = time(16, 0)


def ny_now() -> datetime:
    return datetime.now(EASTERN_TZ)


def is_regular_market_hours(current_time: datetime | None = None) -> bool:
    now = current_time.astimezone(EASTERN_TZ) if current_time else ny_now()

    if now.weekday() >= 5:
        return False

    current_clock = now.time().replace(tzinfo=None)
    return REGULAR_MARKET_OPEN <= current_clock < REGULAR_MARKET_CLOSE