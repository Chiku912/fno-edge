import asyncio
import json
import os
import time
from fastapi import FastAPI, WebSocket
import uvicorn
import requests
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

app = FastAPI()
connected_clients = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive"
}

def fetch_nse_data():
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=5)
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def generate_ai_summary(text):
    if not ai_model or len(text) < 30:
        return text
    try:
        prompt = f"Summarize this stock filing in 1 crisp sentence focusing on price impact and metrics: {text}"
        response = ai_model.generate_content(prompt)
        return "🤖 AI Summary: " + response.text.replace('\n', ' ').strip()
    except Exception:
        return text

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    
    initial_data = fetch_nse_data()
    if initial_data:
        # Loop backwards from oldest to newest to preserve chronological stack execution order
        for item in reversed(initial_data[:50]):
            raw_desc = str(item.get('desc', ''))
            symbol = item.get('symbol', 'NSE')
            an_dt = item.get('an_dt', '')
            
            # FIXED: Create an unalterable stable unique ID using the official exchange filing timestamp
            stable_id = f"nse_{symbol}_{an_dt}".replace(" ", "_").replace(":", "-")
            
            # Map structural epoch milliseconds from exchange string representation
            try:
                epoch_ms = int(time.mktime(time.strptime(an_dt, "%Y-%m-%d %H:%M:%S")) * 1000)
            except Exception:
                epoch_ms = int(time.time() * 1000)

            payload = {
                "type": "NEW_SIGNAL",
                "data": {
                    "id": stable_id,
                    "sym": symbol,
                    "title": raw_desc[:70] + "...",
                    "body": generate_ai_summary(raw_desc),
                    "impact": "C" if "dividend" in raw_desc.lower() or "result" in raw_desc.lower() else "M",
                    "ago": item.get('attchmntText', 'Filing'),
                    "ts": epoch_ms,
                    "l3": an_dt[11:16] # Extract HH:MM directly
                }
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.02)
            
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

async def instant_nse_fetcher():
    last_filing_time = None
    while True:
        if connected_clients: 
            data = fetch_nse_data()
            if data:
                latest = data[0]
                if latest.get('an_dt') != last_filing_time and last_filing_time is not None:
                    raw_desc = str(latest.get('desc', ''))
                    symbol = latest.get('symbol', 'NSE')
                    an_dt = latest.get('an_dt', '')
                    stable_id = f"nse_{symbol}_{an_dt}".replace(" ", "_").replace(":", "-")
                    
                    payload = {
                        "type": "NEW_SIGNAL",
                        "data": {
                            "id": stable_id,
                            "sym": symbol,
                            "title": raw_desc[:70] + "...",
                            "body": generate_ai_summary(raw_desc),
                            "impact": "C" if "dividend" in raw_desc.lower() or "result" in raw_desc.lower() else "M",
                            "ago": "Just now",
                            "ts": int(time.time() * 1000),
                            "l3": an_dt[11:16]
                        }
                    }
                    for client in connected_clients:
                        await client.send_text(json.dumps(payload))
                last_filing_time = latest.get('an_dt')
        await asyncio.sleep(15) 

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(instant_nse_fetcher())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
