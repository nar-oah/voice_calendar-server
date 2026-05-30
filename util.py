from models import Time
from datetime import datetime
from zoneinfo import ZoneInfo


def get_datetime(value: Time) -> datetime:
    return datetime(
        year=value.year,
        month=value.month,
        day=value.day,
        hour=value.hour,
        minute=value.minute,
        second=value.second,
        tzinfo=ZoneInfo("Asia/Shanghai"),
    )


def get_time(dt: datetime) -> Time:
    return Time(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        second=dt.second,
    )
