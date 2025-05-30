from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import requests
import hashlib
import time

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
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    fbp: Optional[str] = None
    fbc: Optional[str] = None
    external_id: Optional[str] = None
    event_source_url: Optional[str] = None

# Hash seguro para e-mail e nome (não vai usar agora, mas deixei)
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
    user_agent = request.headers.get("user-agent", "")
    location = get_geolocation(client_ip)

    payload = {
        "data": [
            {
                "event_name": event.event,
                "event_time": int(time.time()),
                "action_source": "website",
                "event_source_url": event.event_source_url,  # Corrigido para vir do frontend!
                "user_data": {
                    "client_ip_address": client_ip,
                    "client_user_agent": user_agent,
                    "fbp": event.fbp,
                    "fbc": event.fbc,
                    "external_id": event.external_id
                },
                "custom_data": {
                    "utm_source": event.utm_source,
                    "utm_medium": event.utm_medium,
                    "utm_campaign": event.utm_campaign,
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

    # Salva no painel
    eventos_recebidos.append({
        "hora": time.strftime("%H:%M:%S"),
        "evento": event.event,
        "ip": client_ip,
        "cidade": location.get("city"),
        "estado": location.get("regionName"),
        "pais": location.get("country"),
        "utm_source": event.utm_source
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
        <title>Monitor de Eventos</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }
            h1 { text-align: center; color: #333; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px 15px; border: 1px solid #ccc; text-align: center; }
            th { background-color: #4CAF50; color: white; position: sticky; top: 0; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            tr:hover { background-color: #ddd; }
            .container { max-width: 1200px; margin: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Eventos Recebidos</h1>
            <table>
                <thead>
                    <tr>
                        <th>Hora</th>
                        <th>Evento</th>
                        <th>IP</th>
                        <th>Cidade</th>
                        <th>Estado</th>
                        <th>País</th>
                        <th>UTM Source</th>
                    </tr>
                </thead>
                <tbody>
    """
    for ev in reversed(eventos_recebidos[-50:]):
        html += f"""
        <tr>
            <td>{ev['hora']}</td>
            <td>{ev['evento']}</td>
            <td>{ev['ip']}</td>
            <td>{ev['cidade']}</td>
            <td>{ev['estado']}</td>
            <td>{ev['pais']}</td>
            <td>{ev['utm_source']}</td>
        </tr>
        """
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html
