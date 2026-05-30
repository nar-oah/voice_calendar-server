from secrets import token_urlsafe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import Db
from models import Event, StoredEvent
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


@app.post("/event", response_model=Event)
def get_events(text: str) -> Event:
    return parser if isinstance(parser := get_parser(text), Event) else get_event(text)


@app.post("/add", response_model=StoredEvent | None)
def add_event(token: str, event: Event) -> StoredEvent | None:
    return db.add_event(token, event)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
