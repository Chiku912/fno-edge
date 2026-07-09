import asyncio
import json
import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# BSE data is public; no complex proxying needed on the server side
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_exchange_data():
    try:
        # Latest 40 announcements from BSE
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C&critearea=&scripcode=&Flag=0&Promoter=&SequenceSort="
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.json().get('Table', [])[:40]
    except Exception as e:
        print(f"BSE Fetch Error: {e}")
        return []

@app.get("/api/signals")
async def get_signals():
    return {"data": fetch_exchange_data()}

@app.get("/api/calendar")
async def get_calendar():
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode=&fromDate=&toDate=&Flag=0&Industry=&SequenceSort="
        response = requests.get(url, headers=HEADERS, timeout=10)
        return {"data": response.json().get('Table', [])[:30]}
    except: return {"data": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
