from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
import hashlib
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PIXEL_ID = "1837485547102159"
ACCESS_TOKEN = "EAAYhO7ITkRQBOwQdf6B0FONgfHlfoS1cSYbqAkuVVl0badqUqkQy5HO4d3WMywfU5Q8JeKiFTqfWXif11JjkdWEDHXPBBB8JTBS6JAc0NuBUFfuZCJYsUg3PbaPOdgBrn8ZB6zn2ZCg53Hfa1ezHe9Cq8tAtZAoPOyzrkyxK5ZCZBm3ZAU4hBGiWbZAZCf19EPJ3dMgZDZD"

class EventData(BaseModel):
    event: str
    email: Optional[str] = None
    name: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

def hash_sha256(data: Optional[str]) -> Optional[str]:
    if data:
        return hashlib.sha256(data.strip().lower().encode()).hexdigest()
    return None

@app.post("/event")
async def receive_event(event: EventData, request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    timestamp = int(time.time())

    payload = {
        "data": [
            {
                "event_name": event.event,
                "event_time": timestamp,
                "action_source": "website",
                "event_source_url": str(request.url),
                "user_data": {
                    "em": [hash_sha256(event.email)],
                    "fn": [hash_sha256(event.name.split()[0]) if event.name else None],
                    "ln": [hash_sha256(event.name.split()[-1]) if event.name else None],
                    "client_ip_address": client_ip,
                    "client_user_agent": user_agent
                },
                "custom_data": {
                    "utm_source": event.utm_source,
                    "utm_medium": event.utm_medium,
                    "utm_campaign": event.utm_campaign
                }
            }
        ]
    }

    url = f"https://graph.facebook.com/v18.0/{PIXEL_ID}/events?access_token={ACCESS_TOKEN}"
    response = requests.post(url, json=payload)

    print(f"[Facebook CAPI] {response.status_code}: {response.text}")

    return {
        "status": response.status_code,
        "meta_response": response.text
    }
