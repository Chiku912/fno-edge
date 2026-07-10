import asyncio
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# BSE API is the most reliable source for both NSE/BSE filings
HEADERS = {"User-Agent": "Mozilla/5.0"}
cache = {"signals": [], "calendar": []}

def fetch_data():
    while True:
        try:
            # 1. Signals (Announcements)
            ann_url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C"
            cache["signals"] = requests.get(ann_url, headers=HEADERS, timeout=10).json().get('Table', [])
            
            # 2. Corporate Actions (Calendar)
            cal_url = "https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode="
            cache["calendar"] = requests.get(cal_url, headers=HEADERS, timeout=10).json().get('Table', [])
        except: pass
        time.sleep(120)

@app.on_event("startup")
async def startup():
    asyncio.create_task(asyncio.to_thread(fetch_data))

@app.get("/api/signals")
async def get_signals(): return {"data": cache["signals"][:50]}

@app.get("/api/calendar")
async def get_calendar(): return {"data": cache["calendar"][:50]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
