from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Event
from parser import get_parser
from service import get_event

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


@app.post("/event", response_model=Event)
def get_events(text: str) -> Event:
    return parser if isinstance(parser := get_parser(text), Event) else get_event(text)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
