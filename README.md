# Voice Calendar Gemini Server

Small FastAPI service for extracting calendar events from natural language with Gemini.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"
```

## Run

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Example

```bash
curl -X POST http://127.0.0.1:8000/calendar/events \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Book a project sync tomorrow at 10am for 45 minutes with Alex.",
    "timezone": "Asia/Shanghai",
    "now": "2026-05-29T15:00:00+08:00"
  }'
```
