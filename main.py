from secrets import token_urlsafe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from radicale import add_user
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


@app.get("/token", response_model=str)
def create_token() -> str:
    return token_urlsafe(32)


@app.post("/events", response_model=list[StoredEvent])
def read_events(token: str) -> list[StoredEvent]:
    return list(db.get_events(token))


@app.post("/parser", response_model=Event | None)
def get_events(token: str, text: str) -> Event | None:
    data = parser if isinstance(parser := get_parser(text), Event) else get_event(text)
    return data if data.action == Action.create else db.get_blur_event(token, data)


@app.post("/add", response_model=StoredEvent | None)
def add_event(token: str, event: Event) -> StoredEvent | None:
    if len(db.get_data(token)) == 0:
        add_user(token)
    return db.add_event(token, event)


@app.post("/del", response_model=None)
def del_event(token: str, id: int) -> None:
    return db.del_event(token, id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
