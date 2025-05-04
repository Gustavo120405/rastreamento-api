from fastapi import FastAPI
from pydantic import BaseModel
import hashlib

app = FastAPI()

class EventData(BaseModel):
    event: str
    email: str
    phone: str
    name: str

def hash_sha256(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()

@app.post("/event")
async def receive_event(data: EventData):
    hashed_email = hash_sha256(data.email)
    hashed_phone = hash_sha256(data.phone)
    hashed_name = hash_sha256(data.name)

    print({
        "hashed_email": hashed_email,
        "hashed_phone": hashed_phone,
        "hashed_name": hashed_name,
        "event": data.event
    })

    return {"status": "received", "event": data.event}
