from collections.abc import Iterable
from datetime import datetime
from zoneinfo import ZoneInfo
import psycopg
from psycopg.rows import TupleRow
from models import Event, StoredEvent, Time


class Db:
    def __init__(self) -> None:
        self.conn = psycopg.connect()
        self.cursor = self.conn.cursor()

    def _get_datetime(self, value: Time) -> datetime:
        return datetime(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            tzinfo=ZoneInfo("Asia/Shanghai"),
        )

    def _get_event(self, row: TupleRow) -> StoredEvent:
        return StoredEvent(
            id=row[0],
            title=row[1],
            start_at=row[2],
            end_at=row[3],
            location=row[4],
            description=row[5],
        )

    def get_events(self, token: str) -> Iterable[StoredEvent]:

        self.cursor.execute(
            """
            SELECT id, title, start_at, end_at, location, description
            FROM events
            WHERE token = %s
            """,
            (token,),
        )
        return map(lambda row: self._get_event(row), self.cursor.fetchall())

    def get_blur_event(self, token: str, event: Event) -> StoredEvent | None:
        fields = [
            ("title", event.title),
            ("location", event.location),
            ("description", event.description),
        ]
        blur_fields = [
            (column, value)
            for column, value in fields
            if isinstance(value, str) and value.strip()
        ]
        if not blur_fields:
            return None

        values = [value for _, value in blur_fields]
        matches = [f"{column} %% %s" for column, _ in blur_fields]
        scores = [
            f"COALESCE(similarity({column}, %s), 0)"
            for column, _ in blur_fields
        ]

        self.cursor.execute(
            f"""
            SELECT id, title, start_at, end_at, location, description
            FROM events
            WHERE token = %s
                AND start_at >= %s
                AND end_at <= %s
                AND ({" OR ".join(matches)})
            ORDER BY {" + ".join(scores)} DESC, start_at ASC
            LIMIT 1
            """,
            (
                token,
                self._get_datetime(event.start),
                self._get_datetime(event.end),
                *values,
                *values,
            ),
        )
        row = self.cursor.fetchone()
        return self._get_event(row) if isinstance(row, tuple) else None

    def add_event(self, token: str, event: Event) -> StoredEvent | None:
        self.cursor.execute(
            """
            INSERT INTO events (
                token, title, start_at, end_at, location, description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, start_at, end_at, location, description
            """,
            (
                token,
                event.title,
                self._get_datetime(event.start),
                self._get_datetime(event.end),
                event.location,
                event.description,
            ),
        )
        row = self.cursor.fetchone()
        self.conn.commit()
        return self._get_event(row) if isinstance(row, tuple) else None
