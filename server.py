import asyncio
import json
import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

app = FastAPI()

# Allow the frontend to securely access this backend without CORS errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients = set()

# Native browser spoofing to bypass Exchange firewalls
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://www.bseindia.com",
    "Referer": "https://www.bseindia.com/"
}

def fetch_exchange_data():
    """Fetches Live Announcements"""
    try:
        url = f"https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C&critearea=&scripcode=&Flag=0&Promoter=&SequenceSort=&_rnd={time.time()}"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            return response.json().get('Table', [])
    except Exception as e:
        print(f"Announcement Fetch Error: {e}")
    return []

def fetch_calendar_data():
    """Fetches Upcoming Corporate Actions"""
    try:
        url = f"https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode=&fromDate=&toDate=&Flag=0&Industry=&SequenceSort=&_rnd={time.time()}"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            return response.json().get('Table', [])
    except Exception as e:
        print(f"Calendar Fetch Error: {e}")
    return []

@app.get("/")
async def root():
    return {"status": "🟢 FNO Edge Live Engine Active (Plan B)"}

@app.get("/api/calendar")
async def get_calendar():
    """Hosts the calendar data securely for the frontend to consume"""
    return {"data": fetch_calendar_data()}

def format_payload(item):
    raw_desc = item.get('HEADLINE') or item.get('NEWS_SUB') or ''
    # Send the full name so the frontend can securely map it to the F&O list
    sym_name = (item.get('SLONGNAME') or item.get('Security_Name') or item.get('scrip_name') or 'MARKET').upper()
    news_id = item.get('NEWSID', str(int(time.time())))
    dt_str = item.get('NEWS_DT', '')
    
    try:
        epoch_ms = int(time.mktime(time.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")) * 1000)
    except:
        epoch_ms = int(time.time() * 1000)

    pdf_file = item.get('ATTACHMENTNAME', '')
    pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_file}" if pdf_file else ""
    impact = "C" if any(x in raw_desc.lower() for x in ['dividend', 'result', 'earnings', 'merger', 'acquisition', 'profit', 'loss']) else "M"

    return {
        "type": "NEW_SIGNAL",
        "data": {
            "id": f"bse_{news_id}",
            "symName": sym_name,
            "title": raw_desc,
            "body": raw_desc,
            "impact": impact,
            "ts": epoch_ms,
            "pdf": pdf_url
        }
    }

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    
    initial_data = fetch_exchange_data()
    if initial_data:
        # Pushes the latest 30 announcements immediately on load
        for item in reversed(initial_data[:30]):
            payload = format_payload(item)
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.01)
            
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

async def instant_fetcher():
    last_news_id = None
    while True:
        if connected_clients:
            data = fetch_exchange_data()
            if data:
                latest = data[0]
                current_id = latest.get('NEWSID')
                
                if current_id != last_news_id and last_news_id is not None:
                    payload = format_payload(latest)
                    for client in connected_clients:
                        try:
                            await client.send_text(json.dumps(payload))
                        except:
                            pass
                last_news_id = current_id
        await asyncio.sleep(20)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(instant_fetcher())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
