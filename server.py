import asyncio
import json
import time
from fastapi import FastAPI, WebSocket
import uvicorn
import requests

app = FastAPI()
connected_clients = set()

# Use a real browser header so BSE doesn't block the request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

def fetch_bse_data():
    try:
        # Direct BSE API fetch - No proxy needed here
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C&critearea=&scripcode=&Flag=0&Promoter=&SequenceSort="
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get('Table', [])
    except Exception as e:
        print(f"Backend Fetch Error: {e}")
    return []

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    data = fetch_bse_data()
    for item in reversed(data[:30]):
        payload = {
            "type": "NEW_SIGNAL",
            "data": {
                "id": str(item.get('NEWSID')),
                "sym": (item.get('SLONGNAME') or 'MARKET').split(' ')[0],
                "title": item.get('HEADLINE', ''),
                "body": item.get('HEADLINE', ''),
                "ts": int(time.time() * 1000),
                "pdf": f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{item.get('ATTACHMENTNAME','')}"
            }
        }
        await websocket.send_text(json.dumps(payload))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
