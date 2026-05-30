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
_COMMAND_RE = re.compile(
    r"(帮我|请|给我|我要|我想|安排|新增|创建|添加|提醒我|提醒一下|"
    r"提醒|记一下|记下|设置|日程|一个|一下)"
)
_LEADING_CONNECTOR_RE = re.compile(r"^[到至去和跟与、，。,.；;：:\s]+")


def can_parse_lightweight(text: str) -> bool:
    req = text.strip()
    time_entity = _extract_time(req)
    return bool(req and _get_time_bounds(time_entity) and _is_simple_structure(req))


def parse_local_event(text: str) -> Event | None:
    req = text.strip()
    time_entity = _extract_time(req)
    bounds = _get_time_bounds(time_entity)
    if bounds is None or not _is_simple_structure(req):
        return None

    description = _extract_description(req)
    location = _extract_location(req)
    title = _extract_title(req, location, time_entity)
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


def _extract_time(text: str) -> dict[str, object] | None:
    if not text:
        return None
    try:
        entities = jio.ner.extract_time(
            text,
            time_base=datetime.now().timestamp(),
            ret_future=True,
        )
    except ValueError:
        return None
    if not isinstance(entities, list) or len(entities) != 1:
        return None
    return entities[0] if isinstance(entities[0], dict) else None


def _get_time_bounds(entity: dict[str, object] | None) -> list[str] | None:
    detail = entity.get("detail") if isinstance(entity, dict) else None
    times = detail.get("time") if isinstance(detail, dict) else None
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


def _extract_title(text: str, location: str | None, time_entity: dict[str, object] | None) -> str:
    title = text
    title = _remove_time_text(title, time_entity)
    title = _DESCRIPTION_RE.sub("", title)
    title = _COMMAND_RE.sub("", title)
    if location:
        title = re.sub(rf"(?:在|到|去|前往|于){re.escape(location)}", "", title, count=1)
    title = _LEADING_CONNECTOR_RE.sub("", title)
    return title.strip(" ，。,.；;：:的了")


def _remove_time_text(text: str, entity: dict[str, object] | None) -> str:
    offset = entity.get("offset") if isinstance(entity, dict) else None
    if not isinstance(offset, list) or len(offset) != 2:
        return text
    start, end = offset
    if not isinstance(start, int) or not isinstance(end, int):
        return text
    return text[:start] + text[end:]
