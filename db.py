from collections.abc import Iterable
import psycopg
from psycopg.rows import TupleRow
from models import StoredEvent


class Db:
    def __init__(self) -> None:
        self.conn = psycopg.connect()
        self.cursor = self.conn.cursor()

    def get_events(self, token: str) -> Iterable[StoredEvent]:
        def get_event(row: TupleRow) -> StoredEvent:
            return StoredEvent(
                id=row[0],
                title=row[1],
                start_at=row[2],
                end_at=row[3],
                location=row[4],
                description=row[5],
            )

        self.cursor.execute(
            """
            SELECT id, title, start_at, end_at, location, description
            FROM events
            WHERE token = %s
            """,
            (token,),
        )
        return map(lambda row: get_event(row), self.cursor.fetchall())
