from fastapi import FastAPI
from pydantic import BaseModel
import hashlib
import requests
import datetime

app = FastAPI()

# ⚠️ Substitua abaixo pelos seus dados reais
PIXEL_ID = "1837485547102159"
ACCESS_TOKEN = "EAAYhO7ITkRQBOwQdf6B0FONgfHlfoS1cSYbqAkuVVl0badqUqkQy5HO4d3WMywfU5Q8JeKiFTqfWXif11JjkdWEDHXPBBB8JTBS6JAc0NuBUFfuZCJYsUg3PbaPOdgBrn8ZB6zn2ZCg53Hfa1ezHe9Cq8tAtZAoPOyzrkyxK5ZCZBm3ZAU4hBGiWbZAZCf19EPJ3dMgZDZD"

# Função para aplicar SHA256
def hash_sha256(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()

# Função que envia evento para a API do Meta
def enviar_para_facebook(nome: str, email: str, evento: str = "Lead"):
    url = f"https://graph.facebook.com/v18.0/{PIXEL_ID}/events?access_token={ACCESS_TOKEN}"
    
    payload = {
        "data": [
            {
                "event_name": evento,
                "event_time": int(datetime.datetime.now().timestamp()),
                "action_source": "website",
                "user_data": {
                    "em": [hash_sha256(email)],
                    "fn": [hash_sha256(nome)]
                }
            }
        ]
    }

    response = requests.post(url, json=payload)
    print(f"[Facebook CAPI] {response.status_code}: {response.text}")
    return response.status_code, response.text

# Modelo de entrada via POST
class EventData(BaseModel):
    event: str
    email: str
    name: str

@app.post("/event")
async def receive_event(data: EventData):
    status, resposta = enviar_para_facebook(data.name, data.email, data.event)
    return {"status": status, "meta_response": resposta}
