from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import requests
import hashlib
import time

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

# Armazena os eventos localmente (para o painel)
eventos_recebidos = []

# Modelo de dados
class EventData(BaseModel):
    event: str
    email: Optional[str] = None
    name: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None

def hash_sha256(data: Optional[str]) -> Optional[str]:
    if data:
        return hashlib.sha256(data.strip().lower().encode()).hexdigest()
    return None

@app.post("/event")
async def receive_event(event: EventData, request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    first_name = event.name.split()[0] if event.name else None
    last_name = event.name.split()[-1] if event.name else None

    print("Evento recebido:", event.event)
    print("Nome:", event.name)
    print("Email:", event.email)
    print("UTMs:", event.utm_source, event.utm_medium, event.utm_campaign, event.utm_term, event.utm_content)

    payload = {
        "data": [
            {
                "event_name": event.event,
                "event_time": int(time.time()),
                "action_source": "website",
                "event_source_url": str(request.url),
                "user_data": {
                    "em": [hash_sha256(event.email)],
                    "fn": [hash_sha256(first_name)],
                    "ln": [hash_sha256(last_name)],
                    "client_ip_address": client_ip,
                    "client_user_agent": user_agent,
                    "fbc": event.utm_campaign,
                    "fbp": event.utm_source
                },
                "custom_data": {
                    "utm_medium": event.utm_medium,
                    "utm_term": event.utm_term,
                    "utm_content": event.utm_content
                }
            }
        ]
    }

    print("Payload para Meta:", payload)

    response = requests.post(
        f"https://graph.facebook.com/v18.0/{PIXEL_ID}/events?access_token={ACCESS_TOKEN}",
        json=payload
    )

    eventos_recebidos.append({
        "evento": event.event,
        "nome": event.name,
        "email": event.email,
        "ip": client_ip,
        "utm_source": event.utm_source,
        "utm_medium": event.utm_medium,
        "utm_campaign": event.utm_campaign,
        "utm_term": event.utm_term,
        "utm_content": event.utm_content,
        "user_agent": user_agent,
        "hora": time.strftime("%H:%M:%S")
    })

    return {
        "status": response.status_code,
        "meta_response": response.text
    }

@app.get("/monitor", response_class=HTMLResponse)
async def painel():
    html = "<h1>Eventos recebidos</h1><table border=1><tr><th>Hora</th><th>Evento</th><th>Nome</th><th>Email</th><th>IP</th><th>UTM Source</th></tr>"
    for ev in reversed(eventos_recebidos[-50:]):
        html += f"<tr><td>{ev['hora']}</td><td>{ev['evento']}</td><td>{ev['nome']}</td><td>{ev['email']}</td><td>{ev['ip']}</td><td>{ev['utm_source']}</td></tr>"
    html += "</table>"
    return html
