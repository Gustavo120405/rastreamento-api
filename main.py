from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import requests
import hashlib
import time
import pytz
from datetime import datetime

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Meta Conversion API
PIXEL_ID = "1837485547102159"
ACCESS_TOKEN = "EAAYhO7ITkRQBOwQdf6B0FONgfHlfoS1cSYbqAkuVVl0badqUqkQy5HO4d3WMywfU5Q8JeKiFTqfWXif11JjkdWEDHXPBBB8JTBS6JAc0NuBUFfuZCJYsUg3PbaPOdgBrn8ZB6zn2ZCg53Hfa1ezHe9Cq8tAtZAoPOyzrkyxK5ZCZBm3ZAU4hBGiWbZAZCf19EPJ3dMgZDZD"

# Armazenamento local
eventos_recebidos = []

# Modelo dos dados recebidos
class EventData(BaseModel):
    event: str
    email: Optional[str] = None
    name: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    referrer: Optional[str] = None
    page_url: Optional[str] = None
    user_agent: Optional[str] = None
    language: Optional[str] = None
    screen_width: Optional[int] = None
    fbp: Optional[str] = None
    fbc: Optional[str] = None

# Hash seguro para e-mail e nome
def hash_sha256(data: Optional[str]) -> Optional[str]:
    if data:
        return hashlib.sha256(data.strip().lower().encode()).hexdigest()
    return None

# Função de geolocalização por IP
def get_geolocation(ip: str) -> dict:
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=country,regionName,city")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return {}

# Endpoint de rastreamento
@app.post("/event")
async def receive_event(event: EventData, request: Request):
    client_ip = request.client.host
    user_agent = event.user_agent or request.headers.get("user-agent", "")
    first_name = event.name.split()[0] if event.name else None
    last_name = event.name.split()[-1] if event.name else None
    location = get_geolocation(client_ip)

    payload = {
        "data": [
            {
                "event_name": event.event,
                "event_time": int(time.time()),
                "action_source": "website",
                "event_source_url": event.page_url,
                "user_data": {
                    "em": [hash_sha256(event.email)],
                    "fn": [hash_sha256(first_name)],
                    "ln": [hash_sha256(last_name)],
                    "client_ip_address": client_ip,
                    "client_user_agent": user_agent,
                    "fbc": event.fbc,
                    "fbp": event.fbp
                },
                "custom_data": {
                    "utm_medium": event.utm_medium,
                    "utm_term": event.utm_term,
                    "utm_content": event.utm_content
                }
            }
        ]
    }

    # Print no terminal da Render
    print("Evento recebido:", event.event)
    print("Localização:", location.get("city"), "-", location.get("regionName"), "-", location.get("country"))
    print("Payload:", payload)

    # Envia para Meta
    response = requests.post(
        f"https://graph.facebook.com/v18.0/{PIXEL_ID}/events?access_token={ACCESS_TOKEN}",
        json=payload
    )

    # Horário com timezone de Brasília
    hora_brasilia = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%H:%M:%S")

    # Salva no painel
    eventos_recebidos.append({
        "hora": hora_brasilia,
        "evento": event.event,
        "nome": event.name,
        "email": event.email,
        "ip": client_ip,
        "cidade": location.get("city"),
        "estado": location.get("regionName"),
        "pais": location.get("country"),
        "utm": event.utm_source
    })

    return {
        "status": response.status_code,
        "meta_response": response.text
    }

# Painel de visualização
@app.get("/monitor", response_class=HTMLResponse)
async def painel():
    html = """
    <html>
    <head>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial; background-color: #f2f2f5; padding: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; background: white; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
    </head>
    <body>
    <h1>Eventos Recebidos</h1>
    <table>
        <tr><th>Hora</th><th>Evento</th><th>IP</th><th>Cidade</th><th>Estado</th><th>País</th><th>UTM Source</th></tr>
    """
    for ev in reversed(eventos_recebidos[-50:]):
        html += f"<tr><td>{ev['hora']}</td><td>{ev['evento']}</td><td>{ev['ip']}</td><td>{ev['cidade']}</td><td>{ev['estado']}</td><td>{ev['pais']}</td><td>{ev['utm']}</td></tr>"
    html += """</table></body></html>"""
    return html
