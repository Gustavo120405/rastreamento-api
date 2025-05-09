from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
import hashlib
import datetime

app = FastAPI()

# Substitua com seus dados reais
PIXEL_ID = "1837485547102159"
ACCESS_TOKEN = "EAAYhO7ITkRQBOwQdf6B0FONgfHlfoS1cSYbqAkuVVl0badqUqkQy5HO4d3WMywfU5Q8JeKiFTqfWXif11JjkdWEDHXPBBB8JTBS6JAc0NuBUFfuZCJYsUg3PbaPOdgBrn8ZB6zn2ZCg53Hfa1ezHe9Cq8tAtZAoPOyzrkyxK5ZCZBm3ZAU4hBGiWbZAZCf19EPJ3dMgZDZD"

class EventData(BaseModel):
    event: str
    email: str = ""
    name: str = ""

def sha256_hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()

@app.post("/event")
async def receive_event(data: EventData, request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get('user-agent', '')

    payload = {
        "data": [
            {
                "event_name": data.event,
                "event_time": int(datetime.datetime.utcnow().timestamp()),
                "action_source": "website",
                "user_data": {
                    "em": [sha256_hash(data.email)] if data.email else [],
                    "fn": [sha256_hash(data.name.split()[0])] if data.name else [],
                    "ln": [sha256_hash(data.name.split()[-1])] if data.name and " " in data.name else [],
                    "client_ip_address": client_ip,
                    "client_user_agent": user_agent
                }
            }
        ]
    }

    response = requests.post(
        f"https://graph.facebook.com/v18.0/{PIXEL_ID}/events?access_token={ACCESS_TOKEN}",
        json=payload
    )

    return {"status": response.status_code, "meta_response": response.text}
