from datetime import date, datetime, time, timedelta
from secrets import token_urlsafe
from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from radicale import Radicale, add_user
from db import Db
from models import Action, Event, StoredEvent
from parser import get_parser
from service import get_event


db = Db()
app = FastAPI(title="Voice Calendar Gemini Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://calendar.naroah.top",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CalendarResponse(Response):
    media_type = "text/calendar"


def get_token(token: str) -> str:
    def fail() -> str:
        raise HTTPException(status_code=400, detail="token must not be empty")

    return token if len(token.strip()) > 0 else fail()


@app.get("/token", response_model=str)
def create_token() -> str:
    return token_urlsafe(32)


@app.post("/events", response_model=list[StoredEvent])
def read_events(token: str) -> list[StoredEvent]:
    token = get_token(token)
    return list(db.get_events(token))


@app.post("/parser", response_model=Event | None)
def get_events(token: str, text: str) -> Event | None:
    token = get_token(token)
    data = parser if isinstance(parser := get_parser(text), Event) else get_event(text)
    return data if data.action == Action.create else db.get_blur_event(token, data)


@app.post("/add", response_model=StoredEvent | None)
def add_event(token: str, event: Event, tasks: BackgroundTasks) -> StoredEvent | None:
    def sync_event() -> None:
        add_user(token)
        Radicale(token).add_event(result)

    token = get_token(token)
    result = db.add_event(token, event)
    if isinstance(result, StoredEvent):
        tasks.add_task(sync_event)
    return result


@app.post("/del", response_model=None)
def del_event(token: str, id: int, tasks: BackgroundTasks) -> None:
    token = get_token(token)
    tasks.add_task(lambda: Radicale(token).del_event(id))
    db.del_event(token, id)


@app.post("/export", response_class=CalendarResponse)
def export_ics(token: str, date: date) -> CalendarResponse:
    token = get_token(token)
    start = datetime.combine(date, time.min)
    ics = Radicale(token).get_calendar(start, start + timedelta(days=1))
    return CalendarResponse(
        content=ics,
        headers={
            "Content-Disposition": 'attachment; filename="calendar.ics"',
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
