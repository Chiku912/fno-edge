import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/"
}

@app.get("/")
def home():
    return {"status": "FNO Edge Engine Online"}

@app.get("/api/signals")
def get_signals():
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C"
        res = requests.get(url, headers=HEADERS, timeout=15)
        data = res.json()
        # Handle various BSE JSON key structures
        items = data.get('Table', []) or data.get('Table1', []) or data.get('data', [])
        return {"data": items}
    except Exception as e:
        return {"data": [], "error": str(e)}

@app.get("/api/calendar")
def get_calendar():
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode="
        res = requests.get(url, headers=HEADERS, timeout=15)
        data = res.json()
        items = data.get('Table', []) or data.get('Table1', []) or data.get('data', [])
        return {"data": items}
    except Exception as e:
        return {"data": [], "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
