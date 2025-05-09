from fastapi import FastAPI, Request
import requests
import hashlib
import os

app = FastAPI()

# Substitua pelos seus dados
PIXEL_ID = "1837485547102159"
ACCESS_TOKEN = "EAAYhO7ITkRQBOwQdf6B0FONgfHlfoS1cSYbqAkuVVl0badqUqkQy5HO4d3WMywfU5Q8JeKiFTqfWXif11JjkdWEDHXPBBB8JTBS6JAc0NuBUFfuZCJYsUg3PbaPOdgBrn8ZB6zn2ZCg53Hfa1ezHe9Cq8tAtZAoPOyzrkyxK5ZCZBm3ZAU4hBGiWbZAZCf19EPJ3dMgZDZD"
API_VERSION = "v17.0"

@app.post("/event")
async def receive_event(request: Request):
    data = await request.json()
    event_name = data.get("event", "evento_desconhecido")
    email = data.get("email", "")
    name = data.get("name", "")

    # Hash SHA256 do e-mail (recomendado pelo Meta)
    email_hashed = hashlib.sha256(email.strip().lower().encode()).hexdigest() if email else ""

    payload = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(request.scope["time"].timestamp()),
                "action_source": "website",
                "user_data": {
                    "em": [email_hashed] if email_hashed else [],
                }
            }
        ]
    }

    url = f"https://graph.facebook.com/{API_VERSION}/{PIXEL_ID}/events?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=payload)

    print(f"[Facebook CAPI] {response.status_code}: {response.text} | {event_name}")

    return {"status": response.status_code, "meta_response": response.text}
