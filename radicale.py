from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
import bcrypt
import fcntl
from caldav.davclient import DAVClient
from caldav import Event
from icalendar import Calendar, Event as ICalEvent
from models import StoredEvent


USERS_FILE = Path("/etc/radicale/users")
URL = "http://127.0.0.1:5232/"
CALENDAR = "Voice Calendar"
UID_SUFFIX = "@voice-calendar"


def add_user(token: str) -> None:
    password = bcrypt.hashpw(token.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    line = f"{token}:{password}\n"
    with USERS_FILE.open("a+", encoding="utf-8") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        file.write(line)
        fcntl.flock(file, fcntl.LOCK_UN)
    Radicale(token).add_calendar(CALENDAR)


class Radicale:
    def __init__(self, token: str) -> None:
        with DAVClient(url=URL, username=token, password=token) as client:
            self.principal = client.principal()

    def add_calendar(self, name: str) -> None:
        self.principal.make_calendar(name=name)

    def _add_clalendar_head(self, calendar: Calendar) -> None:
        calendar.add("prodid", "-//voice-calendar//naroah.top//")
        calendar.add("version", "2.0")

    def get_calendar(self, start: datetime, end: datetime) -> bytes:
        def add_vevent(calendar: Calendar, event: Event) -> Iterable[None]:
            source_calendar = Calendar.from_ical(event.data)
            vevents = filter(lambda c: c.name == "VEVENT", source_calendar.walk())
            return map(lambda vevent: calendar.add_component(vevent), vevents)

        calendar = self.principal.calendar(CALENDAR)
        events = calendar.search(event=True, start=start, end=end, expand=False)
        output = Calendar()
        self._add_clalendar_head(output)
        list(map(lambda event: add_vevent(output, event), events))  # type: ignore
        return output.to_ical()

    def add_event(self, event: StoredEvent) -> None:
        def get_event(event: StoredEvent) -> str:
            calendar = Calendar()
            self._add_clalendar_head(calendar)
            vevent = ICalEvent()
            vevent.add("uid", f"{event.id}{UID_SUFFIX}")
            vevent.add("summary", event.title)
            vevent.add("dtstart", event.start_at)
            vevent.add("dtend", event.end_at)
            if event.location:
                vevent.add("location", event.location)
            if event.description:
                vevent.add("description", event.description)
            calendar.add_component(vevent)
            return calendar.to_ical().decode("utf-8")

        calendar = self.principal.calendar(CALENDAR)
        calendar.add_event(get_event(event))

    def del_event(self, id: int) -> None:
        calendar = self.principal.calendar(CALENDAR)
        events = calendar.search(uid=f"{id}{UID_SUFFIX}", event=True)
        events[0].delete()  # type: ignore


if __name__ == "__main__":
    from secrets import token_urlsafe

    token = token_urlsafe(32)
    add_user(token)
    print(token)
