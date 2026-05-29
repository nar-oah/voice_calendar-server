from fastapi import FastAPI
from models import Event
from service import get_event

app = FastAPI(title="Voice Calendar Gemini Server")


@app.post("/event", response_model=Event)
def get_health(text: str) -> Event:
    return get_event(text)


# @app.post("/add", response_model=None)
# def get_events(event: Event) -> None:


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
