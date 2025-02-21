import logging
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import random
import uvicorn 

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rest_server.log"),
    ]
)

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Data structures
connected_users: Dict[int, Dict] = {}  # {user_id: {"tags": [], "ip": "", "geo": {}, "browser_info": ""}}
waiting_users: List[tuple] = []  # [(user_id, tags)]
partner_map: Dict[int, int] = {}  # {user_id: partner_id}
message_queue: Dict[int, List[Dict]] = {}  # {user_id: [{"from": sender_id, "message": text}, ...]}

# Pydantic models for request validation
class ConnectRequest(BaseModel):
    tags: List[str] = []

class MessageRequest(BaseModel):
    message: str

def get_geolocation(ip: str) -> dict:
    """Fetch geolocation data based on IP address."""
    try:
        response = requests.get(f'http://ipinfo.io/{ip}/json')
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching geolocation for IP {ip}: {e}")
        return {}

# Serve index.html
@app.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Connect a user and find a partner
@app.post("/connect/{user_id}")
async def connect_user_endpoint(user_id: int, request: Request, connect_data: ConnectRequest):
    if user_id in connected_users:
        return {"status": "already_connected"}

    ip_address = request.client.host
    geo_data = get_geolocation(ip_address)
    city = geo_data.get('city', 'Unknown')
    region = geo_data.get('region', 'Unknown')
    country = geo_data.get('country', 'Unknown')
    browser_info = request.headers.get("user-agent", "Unknown")

    connected_users[user_id] = {
        "tags": [tag for tag in connect_data.tags if tag != "isTrusted"],
        "ip": ip_address,
        "geo": {"city": city, "region": region, "country": country},
        "browser_info": browser_info,
    }
    message_queue[user_id] = []  # Initialize message queue
    logging.info(f"User {user_id} connected. IP: {ip_address}, Location: {city}, {region}, {country}, Browser: {browser_info}")

    matched_partner = None
    for (waiting_user_id, waiting_tags) in waiting_users[:]:
        if not connect_data.tags or not waiting_tags or set(connect_data.tags).intersection(set(waiting_tags)):
            matched_partner = waiting_user_id
            waiting_users.remove((waiting_user_id, waiting_tags))
            break

    if matched_partner:
        partner_map[user_id] = matched_partner
        partner_map[matched_partner] = user_id
        common_tags = list(set(connect_data.tags).intersection(set(connected_users[matched_partner]["tags"])))
        logging.info(f"User {user_id} paired with {matched_partner}. Common Tags: {common_tags}")
        return {"status": "connected", "partner_id": matched_partner, "tags": common_tags}
    else:
        waiting_users.append((user_id, connect_data.tags))
        return {"status": "waiting"}

# Send a message to the partner
@app.post("/message/{user_id}")
async def send_message_endpoint(user_id: int, message_data: MessageRequest):
    if user_id not in connected_users:
        raise HTTPException(status_code=404, detail="User not connected")
    
    partner_id = partner_map.get(user_id)
    if not partner_id or partner_id not in connected_users:
        raise HTTPException(status_code=400, detail="No partner connected")
    
    message = message_data.message
    logging.info(f"Message from {user_id} to {partner_id}: {message}")
    message_queue[partner_id].append({"from": user_id, "message": message})
    return {"status": "message_sent"}

# Poll for messages and status updates
@app.get("/poll/{user_id}")
async def poll_endpoint(user_id: int):
    if user_id not in connected_users:
        raise HTTPException(status_code=404, detail="User not connected")
    
    response = {
        "online_count": len(connected_users),
        "messages": message_queue[user_id],
        "status": "waiting" if (user_id, connected_users[user_id]["tags"]) in waiting_users else "connected" if user_id in partner_map else "disconnected",
        "partner_id": partner_map.get(user_id),
    }
    message_queue[user_id] = []  # Clear messages after polling
    return response

# Disconnect a user
@app.post("/disconnect/{user_id}")
async def disconnect_endpoint(user_id: int):
    if user_id not in connected_users:
        return {"status": "not_connected"}

    partner_id = partner_map.get(user_id)
    if partner_id and partner_id in connected_users:
        message_queue[partner_id].append({"type": "disconnected", "message": "Partner disconnected."})
        del partner_map[partner_id]

    waiting_users[:] = [(uid, tags) for uid, tags in waiting_users if uid != user_id]
    if user_id in connected_users:
        del connected_users[user_id]
    if user_id in partner_map:
        del partner_map[user_id]
    if user_id in message_queue:
        del message_queue[user_id]

    logging.info(f"User {user_id} disconnected.")
    return {"status": "disconnected"}
   
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
