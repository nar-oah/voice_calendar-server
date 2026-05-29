# Voice Calendar Gemini Server

Small FastAPI service for extracting calendar events from natural language with Gemini.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `/home/admin/voice_calendar/.env` for deployment:

```bash
GEMINI_API_KEY=your-api-key
```

## Run

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Example

```bash
curl -X POST "http://127.0.0.1:8000/event?text=明天下午两点在肯德基吃饭"
```

## Systemd Service

The service file is `deploy/voice_calendar.service` and expects the app to live in `/home/admin/voice_calendar`.

Install and start it with:

```bash
sudo cp deploy/voice_calendar.service /etc/systemd/system/voice_calendar.service
sudo systemctl daemon-reload
sudo systemctl enable --now voice_calendar
sudo systemctl status voice_calendar
```
