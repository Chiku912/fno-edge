import asyncio
import json
import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

connected_clients = set()
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_exchange_data():
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C&critearea=&scripcode=&Flag=0&Promoter=&SequenceSort="
        response = requests.get(url, headers=HEADERS, timeout=15)
        data = response.json()
        print(f"DEBUG: BSE Ann Data: {json.dumps(data)[:200]}...") # Logs first 200 chars to Render Logs
        return data.get('Table', []) or data.get('data', [])
    except Exception as e:
        print(f"DEBUG: Backend Fetch Error: {e}")
        return []

def fetch_calendar_data():
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode=&fromDate=&toDate=&Flag=0&Industry=&SequenceSort="
        response = requests.get(url, headers=HEADERS, timeout=15)
        data = response.json()
        print(f"DEBUG: BSE Cal Data: {json.dumps(data)[:200]}...")
        return data.get('Table', []) or data.get('data', [])
    except Exception as e:
        print(f"DEBUG: Calendar Fetch Error: {e}")
        return []

@app.get("/api/calendar")
async def get_calendar():
    return {"data": fetch_calendar_data()}

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    # Immediate fetch on connection
    data = fetch_exchange_data()
    for item in reversed(data[:30]):
        payload = {
            "type": "NEW_SIGNAL",
            "data": {
                "id": str(item.get('NEWSID', time.time())),
                "symName": item.get('SLONGNAME') or item.get('Security_Name') or 'MARKET',
                "title": item.get('HEADLINE') or item.get('NEWS_SUB', 'No details'),
                "body": item.get('HEADLINE', ''),
                "pdf": f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{item.get('ATTACHMENTNAME','')}"
            }
        }
        await websocket.send_text(json.dumps(payload))
    
    # Keep alive
    try:
        while True: await asyncio.sleep(60)
    except: connected_clients.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
