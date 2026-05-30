import re
from datetime import datetime
from typing import cast

import jionlp as jio

from models import Action, Event, Time


_DANGEROUS_RE = re.compile(
    r"(说|告诉|听说|提到|表示|通知|问|让|叫|如果|假如|要是|否则|"
    r"取消|删除|改|修改|更新|推迟|提前|延期|延后|改天|每[天周月年]|"
    r"之前|之后|以前|以后|那天|当天|到时候|顺便|另外|还有|然后)"
)
_EVENT_WORDS = {
    "开会",
    "吃饭",
    "见面",
    "面试",
    "上课",
    "会议",
    "聚餐",
    "运动",
    "健身",
    "看电影",
    "办事",
}
_LOCATION_RE = re.compile(
    r"(?:在|到|去|前往|于)(?P<location>[^，。,.；;]+?)"
    r"(?=(?:开会|吃饭|见面|面试|上课|会议|聚餐|运动|健身|看电影|办事|参加|$))"
)
_DESCRIPTION_RE = re.compile(r"(?:备注|描述|说明|内容)[:：为是]?(?P<description>[^，。,.；;]+)")
_TIME_TEXT_RE = re.compile(
    r"(大前天|前天|昨天|今天|明天|后天|大后天|今晚|明早|明晚|"
    r"上周|本周|这周|下周|下下周|周[一二三四五六日天]|星期[一二三四五六日天]|"
    r"[0-9０-９一二三四五六七八九十两]+月[0-9０-９一二三四五六七八九十两]+[日号]?|"
    r"[0-9０-９一二三四五六七八九十两]+[日号]|"
    r"(?:上午|下午|中午|晚上|凌晨|早上)?[0-9０-９一二三四五六七八九十两]+[点时]"
    r"(?:半|[0-9０-９一二三四五六七八九十两]+分?)?)"
)
_COMMAND_RE = re.compile(
    r"(帮我|请|给我|我要|我想|安排|新增|创建|添加|提醒我|提醒一下|"
    r"提醒|记一下|记下|设置|日程|一个|一下)"
)
_LEADING_CONNECTOR_RE = re.compile(r"^[到至去和跟与、，。,.；;：:\s]+")


def can_parse_lightweight(text: str) -> bool:
    req = text.strip()
    parsed = _parse_time(req)
    return bool(req and _get_time_bounds(parsed) and _is_simple_structure(req))


def parse_local_event(text: str) -> Event | None:
    req = text.strip()
    parsed = _parse_time(req)
    bounds = _get_time_bounds(parsed)
    if bounds is None or not _is_simple_structure(req):
        return None

    description = _extract_description(req)
    location = _extract_location(req)
    title = _extract_title(req, location)
    return Event(
        action=Action.create,
        title=title,
        start=_to_time(bounds[0]),
        end=_to_time(bounds[1]),
        location=location,
        description=description,
    )


def _is_simple_structure(text: str) -> bool:
    return _DANGEROUS_RE.search(text) is None


def _parse_time(text: str) -> dict[str, object] | None:
    if not text:
        return None
    try:
        parsed = jio.parse_time(
            text,
            time_base=datetime.now().timestamp(),
            ret_future=True,
        )
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _get_time_bounds(parsed: dict[str, object] | None) -> list[str] | None:
    times = parsed.get("time") if isinstance(parsed, dict) else None
    valid = isinstance(times, list) and len(times) == 2
    return cast(list[str], times) if valid and all(isinstance(item, str) for item in times) else None


def _to_time(value: str) -> Time:
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return Time(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        second=dt.second,
    )


def _extract_description(text: str) -> str | None:
    match = _DESCRIPTION_RE.search(text)
    return match.group("description").strip() if match else None


def _extract_location(text: str) -> str | None:
    match = _LOCATION_RE.search(text)
    if match is None:
        return None
    location = match.group("location").strip()
    return None if location in _EVENT_WORDS else location


def _extract_title(text: str, location: str | None) -> str:
    title = text
    title = _DESCRIPTION_RE.sub("", title)
    title = _TIME_TEXT_RE.sub("", title)
    title = _COMMAND_RE.sub("", title)
    if location:
        title = re.sub(rf"(?:在|到|去|前往|于){re.escape(location)}", "", title, count=1)
    title = _LEADING_CONNECTOR_RE.sub("", title)
    return title.strip(" ，。,.；;：:的了")
