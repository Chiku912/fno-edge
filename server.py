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

# NSE requires session cookie negotiation to prevent blocking
def get_nse_session():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.nseindia.com/"
    }
    session.headers.update(headers)
    try:
        # Hit main NSE page first to acquire required cookies
        session.get("https://www.nseindia.com", timeout=5)
    except:
        pass
    return session

@app.get("/")
def home():
    return {"status": "NSE Engine Online"}

@app.get("/api/signals")
def get_nse_signals():
    session = get_nse_session()
    try:
        # NSE Corporate Announcements Endpoint
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        res = session.get(url, timeout=10)
        if res.status_code == 200:
            return {"data": res.json()}
        else:
            # Fallback secondary endpoint if primary is rate-limited
            alt_url = "https://www.nseindia.com/api/equity-corporate-disclosures?index=announcements"
            alt_res = session.get(alt_url, timeout=10)
            return {"data": alt_res.json() if alt_res.status_code == 200 else []}
    except Exception as e:
        return {"data": [], "error": str(e)}

@app.get("/api/calendar")
def get_nse_calendar():
    session = get_nse_session()
    try:
        # NSE Corporate Actions Endpoint
        url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
        res = session.get(url, timeout=10)
        if res.status_code == 200:
            return {"data": res.json()}
        else:
            return {"data": []}
    except Exception as e:
        return {"data": [], "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
