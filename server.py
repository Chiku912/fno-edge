import asyncio
import json
import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

HEADERS = {"User-Agent": "Mozilla/5.0"}
cache = {"signals": [], "calendar": []}

def update_data():
    while True:
        try:
            # BSE Signals Fetch
            ann_url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C"
            data = requests.get(ann_url, headers=HEADERS, timeout=15).json().get('Table', [])
            cache["signals"] = data[:40]
            print(f"BSE Fetch Success: {len(data)} signals")
            
            # BSE Calendar Fetch
            cal_url = "https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode="
            cache["calendar"] = requests.get(cal_url, headers=HEADERS, timeout=15).json().get('Table', [])[:30]
        except Exception as e:
            print(f"Backend Fetch Error: {e}")
        time.sleep(60)

@app.on_event("startup")
async def startup():
    asyncio.create_task(asyncio.to_thread(update_data))

@app.get("/api/signals")
async def get_signals(): return {"data": cache["signals"]}

@app.get("/api/calendar")
async def get_calendar(): return {"data": cache["calendar"]}

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Push initial cache to new client
    for item in cache["signals"]:
        await websocket.send_json({"type": "NEW_SIGNAL", "data": {"id": str(item.get('NEWSID')), "sym": (item.get('SLONGNAME') or 'MARKET').split(' ')[0], "title": item.get('HEADLINE', ''), "pdf": f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{item.get('ATTACHMENTNAME','')}"}})
    try:
        while True: await asyncio.sleep(60)
    except: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
