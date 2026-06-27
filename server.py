import asyncio
import json
import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Fetches latest 30 announcements
def get_announcements():
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C&critearea=&scripcode=&Flag=0&Promoter=&SequenceSort="
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.json().get('Table', [])[:30]
    except: return []

# Fetches Corporate Actions
def get_calendar():
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode=&fromDate=&toDate=&Flag=0&Industry=&SequenceSort="
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.json().get('Table', [])[:30]
    except: return []

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = get_announcements()
        for item in reversed(data):
            await websocket.send_json({
                "type": "NEW_SIGNAL",
                "data": {
                    "id": str(item.get('NEWSID')),
                    "sym": (item.get('SLONGNAME') or 'MARKET').split(' ')[0],
                    "title": item.get('HEADLINE', ''),
                    "body": item.get('HEADLINE', ''),
                    "pdf": f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{item.get('ATTACHMENTNAME','')}"
                }
            })
        await asyncio.sleep(60)

@app.get("/api/calendar")
async def calendar_api():
    return {"data": get_calendar()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
