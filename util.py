from models import Time
from datetime import datetime
from zoneinfo import ZoneInfo

LOCAL_ZONE = ZoneInfo("Asia/Shanghai")


def get_datetime(value: Time) -> datetime:
    return datetime(
        year=value.year,
        month=value.month,
        day=value.day,
        hour=value.hour,
        minute=value.minute,
        second=value.second,
        tzinfo=LOCAL_ZONE,
    )


def get_time(dt: datetime) -> Time:
    value = dt.astimezone(LOCAL_ZONE) if dt.tzinfo is not None else dt
    return Time(
        year=value.year,
        month=value.month,
        day=value.day,
        hour=value.hour,
        minute=value.minute,
        second=value.second,
    )
