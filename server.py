import asyncio
import json
from fastapi import FastAPI, WebSocket
import uvicorn
import requests

app = FastAPI()
connected_clients = set()

# Act like a real Chrome browser to bypass NSE bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

def fetch_nse_data():
    """Fetches data using a session to manage cookies properly"""
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        # Step 1: Hit the homepage to get valid session cookies
        session.get("https://www.nseindia.com", timeout=5)
        
        # Step 2: Hit the actual API
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        response = session.get(url, timeout=5)
        
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Fetch error: {e}")
    return []

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    
    # As soon as you open the app, push the last 50 announcements immediately
    print("New client connected. Fetching initial batch of 50...")
    initial_data = fetch_nse_data()
    
    if initial_data:
        # Send the top 50 recent announcements
        for item in initial_data[:50]:
            payload = {
                "type": "NEW_SIGNAL",
                "data": {
                    "sym": item.get('symbol', 'NSE'),
                    "title": str(item.get('desc', 'Corporate Update'))[:70] + "...",
                    "body": str(item.get('desc', '')),
                    "impact": "C" if "dividend" in str(item).lower() or "result" in str(item).lower() else "M"
                }
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.05) # Sped up the render delay so 50 items load quickly
            
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

async def instant_nse_fetcher():
    """Background loop waiting for brand NEW announcements"""
    last_filing_time = None
    
    while True:
        if connected_clients: # Only fetch if someone has the app open
            data = fetch_nse_data()
            if data:
                latest = data[0]
                
                # If there is a brand new filing, push it instantly
                if latest.get('an_dt') != last_filing_time and last_filing_time is not None:
                    print(f"🚨 NEW SIGNAL DETECTED: {latest.get('symbol')}")
                    payload = {
                        "type": "NEW_SIGNAL",
                        "data": {
                            "sym": latest.get('symbol', 'NSE'),
                            "title": str(latest.get('desc', 'Corporate Update'))[:70] + "...",
                            "body": str(latest.get('desc', '')),
                            "impact": "C" if "dividend" in str(latest).lower() or "result" in str(latest).lower() else "M"
                        }
                    }
                    for client in connected_clients:
                        await client.send_text(json.dumps(payload))
                
                last_filing_time = latest.get('an_dt')
                
        await asyncio.sleep(15) # Check every 15 seconds

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(instant_nse_fetcher())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
