from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
import hashlib
import time  # <- você esqueceu de importar isso

app = FastAPI()

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou especifique ["https://glicopharma.shop"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Credenciais da Meta
PIXEL_ID = "1837485547102159"
ACCESS_TOKEN = "EAAYhO7ITkRQBOwQdf6B0FONgfHlfoS1cSYbqAkuVVl0badqUqkQy5HO4d3WMywfU5Q8JeKiFTqfWXif11JjkdWEDHXPBBB8JTBS6JAc0NuBUFfuZCJYsUg3PbaPOdgBrn8ZB6zn2ZCg53Hfa1ezHe9Cq8tAtZAoPOyzrkyxK5ZCZBm3ZAU4hBGiWbZAZCf19EPJ3dMgZDZD"

# Modelo de dados recebido
class EventData(BaseModel):
    event: str
    email: Optional[str] = None
    name: Optional[str] = None

# Função de hash SHA-256
def hash_sha256(data: Optional[str]) -> Optional[str]:
    if data:
        return hashlib.sha256(data.strip().lower().encode()).hexdigest()
    return None

# Rota que recebe os eventos
@app.post("/event")
async def receive_event(event: EventData, request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    payload = {
        "data": [
            {
                "event_name": event.event,
                "event_time": int(time.time()),
                "action_source": "website",
                "event_source_url": str(request.url),
                "user_data": {
                    "em": [hash_sha256(event.email)],
                    "fn": [hash_sha256(event.name.split()[0]) if event.name else None],
                    "ln": [hash_sha256(event.name.split()[-1]) if event.name else None],
                    "client_ip_address": client_ip,
                    "client_user_agent": user_agent
                }
            }
        ]
    }

    url = f"https://graph.facebook.com/v18.0/{PIXEL_ID}/events?access_token={ACCESS_TOKEN}"
    response = requests.post(url, json=payload)
    return {
        "status": response.status_code,
        "meta_response": response.text
    }
