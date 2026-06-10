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
    def get_login(line: str) -> str:
        return line.split(":", 1)[0]

    def has_user(file) -> bool:
        file.seek(0)
        return token in map(get_login, filter(lambda line: ":" in line, file))

    def write_user(file) -> bool:
        password = bcrypt.hashpw(token.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        file.seek(0, 2)
        file.write(f"{token}:{password}\n")
        file.flush()
        return True

    with USERS_FILE.open("a+", encoding="utf-8") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        write_user(file) if not has_user(file) else None
        Radicale(token).add_calendar(CALENDAR)
        fcntl.flock(file, fcntl.LOCK_UN)


class Radicale:
    def __init__(self, token: str) -> None:
        with DAVClient(url=URL, username=token, password=token) as client:
            self.principal = client.principal()

    def _get_calendar(self, name: str):
        def is_calendar(calendar) -> bool:
            return calendar.get_display_name() == name

        calendars = list(filter(is_calendar, self.principal.get_calendars()))
        return calendars[0] if len(calendars) > 0 else self.principal.make_calendar(name=name)

    def add_calendar(self, name: str) -> None:
        self._get_calendar(name)

    def _add_clalendar_head(self, calendar: Calendar) -> None:
        calendar.add("prodid", "-//voice-calendar//naroah.top//")
        calendar.add("version", "2.0")

    def get_calendar(self, start: datetime, end: datetime) -> bytes:
        def add_vevent(calendar: Calendar, event: Event) -> None:
            source_calendar = Calendar.from_ical(event.data)
            vevents = filter(lambda c: c.name == "VEVENT", source_calendar.walk())
            list(map(lambda vevent: calendar.add_component(vevent), vevents))

        calendar = self._get_calendar(CALENDAR)
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

        calendar = self._get_calendar(CALENDAR)
        calendar.add_event(get_event(event))

    def del_event(self, id: int) -> None:
        calendar = self._get_calendar(CALENDAR)
        events = calendar.search(uid=f"{id}{UID_SUFFIX}", event=True)
        events[0].delete() if len(events) > 0 else None  # type: ignore

if __name__ == "__main__":
    from secrets import token_urlsafe

    token = token_urlsafe(32)
    add_user(token)
    print(token)
