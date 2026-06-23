import asyncio
import json
from fastapi import FastAPI, WebSocket
import uvicorn
import requests

app = FastAPI()
connected_clients = set()

# Headers to bypass basic NSE blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*"
}

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

async def instant_nse_fetcher():
    """
    This loop constantly monitors the NSE wire. 
    In a true production environment, this would connect to a Broker WebSocket.
    """
    last_filing_time = None
    
    while True:
        try:
            # Fetching today's filings instantly
            url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
            response = requests.get(url, headers=HEADERS, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                latest_announcement = data[0] if data else None
                
                # If there's a new filing we haven't seen yet, push it INSTANTLY
                if latest_announcement and latest_announcement.get('an_dt') != last_filing_time:
                    last_filing_time = latest_announcement.get('an_dt')
                    
                    # Format the payload
                    payload = {
                        "type": "NEW_SIGNAL",
                        "data": {
                            "sym": latest_announcement.get('symbol', 'NSE'),
                            "title": latest_announcement.get('desc', 'Corporate Update')[:70],
                            "body": latest_announcement.get('desc', ''),
                            "impact": "C" if "dividend" in str(latest_announcement).lower() else "M"
                        }
                    }
                    
                    # Broadcast instantly to all connected UI dashboards
                    for client in connected_clients:
                        await client.send_text(json.dumps(payload))
                        
        except Exception as e:
            pass # Ignore connection drops and retry instantly
            
        # Poll every 3 seconds (Aggressive background fetching)
        await asyncio.sleep(3)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(instant_nse_fetcher())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
