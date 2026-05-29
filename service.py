from datetime import datetime
from google import genai
from models import Event


def get_event(req: str) -> Event:
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=req,
        config=genai.types.GenerateContentConfig(
            system_instruction=f"当前时间为：{datetime.now()}",
            response_mime_type="application/json",
            response_json_schema=Event.model_json_schema(),
        ),
    )
    text: str = value if isinstance(value := response.text, str) else ""
    return Event.model_validate_json(text)


if __name__ == "__main__":
    print(get_event("明天下午两点在肯德基吃饭"))
