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

def fetch_nse(endpoint: str):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }
    session.headers.update(headers)
    try:
        session.get("https://www.nseindia.com", timeout=6)
        url = f"https://www.nseindia.com/api/{endpoint}"
        res = session.get(url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            return data.get('data', data if isinstance(data, list) else [])
    except Exception as e:
        print(f"NSE Fetch Error: {e}")
    return []

@app.get("/")
def home():
    return {"status": "NSE Direct Stream Active"}

@app.get("/api/signals")
def get_signals():
    items = fetch_nse("corporate-announcements?index=equities")
    # Slice up to 50 latest items
    return {"data": items[:50]}

@app.get("/api/calendar")
def get_calendar():
    items = fetch_nse("corporates-corporateActions?index=equities")
    return {"data": items}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
