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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.bseindia.com",
    "Referer": "https://www.bseindia.com/",
    "Cache-Control": "no-cache",
}


def fetch_exchange_data():
    """Fetch live announcements from BSE with fallback"""
    urls = [
        f"https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C&critearea=&scripcode=&Flag=0&Promoter=&SequenceSort=&_rnd={time.time()}",
        f"https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?pageno=1&strType=C&Flag=0&_rnd={time.time()}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                table = data.get('Table') or data.get('data') or data.get('result') or []
                if table:
                    return table
        except Exception as e:
            print(f"Announce fetch attempt failed: {e}")
    return []


def fetch_calendar_data():
    """Fetch upcoming corporate actions and normalize field names"""
    urls = [
        f"https://api.bseindia.com/BseIndiaAPI/api/CorpAct/w?scripcode=&Purposecode=&fromDate=&toDate=&Flag=0&Industry=&SequenceSort=&_rnd={time.time()}",
        f"https://api.bseindia.com/BseIndiaAPI/api/CorpAction/w?scripcode=&Flag=0&_rnd={time.time()}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                raw = data.get('Table') or data.get('data') or data.get('result') or []
                if not raw:
                    continue
                # ─── NORMALIZE field names so frontend always finds Security_Name ───
                normalized = []
                for item in raw:
                    # BSE uses SM_NAME or LONG_NAME — map to Security_Name
                    sec_name = (
                        item.get('SM_NAME') or
                        item.get('LONG_NAME') or
                        item.get('Security_Name') or
                        item.get('scrip_name') or
                        item.get('SLONGNAME') or
                        item.get('scrip_id') or
                        str(item.get('SCRIP_CD', ''))
                    ).upper().strip()

                    purpose = (
                        item.get('Purpose') or
                        item.get('purpose') or
                        item.get('NEW_PURPOSE') or
                        item.get('HEADLINE') or ''
                    )

                    ex_date = (
                        item.get('ExDate') or
                        item.get('ex_date') or
                        item.get('EX_DATE') or
                        item.get('RecordDate') or
                        item.get('record_date') or
                        item.get('NEWS_DT') or ''
                    )

                    normalized.append({
                        'Security_Name': sec_name,
                        'Purpose': purpose,
                        'ExDate': ex_date,
                        'RecordDate': item.get('RecordDate') or item.get('record_date') or ex_date,
                        'SCRIP_CD': str(item.get('SCRIP_CD', '')),
                    })
                return normalized
        except Exception as e:
            print(f"Calendar fetch attempt failed: {e}")
    return []


def format_payload(item):
    raw_desc = item.get('HEADLINE') or item.get('NEWS_SUB') or item.get('subject') or ''
    sym_name = (
        item.get('SM_NAME') or
        item.get('SLONGNAME') or
        item.get('Security_Name') or
        item.get('scrip_name') or
        'MARKET'
    ).upper()
    news_id = item.get('NEWSID') or item.get('id') or str(int(time.time() * 1000))
    dt_str = item.get('NEWS_DT') or item.get('an_dt') or ''

    try:
        # Handle multiple date formats
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                epoch_ms = int(time.mktime(time.strptime(dt_str[:19], fmt)) * 1000)
                break
            except:
                continue
        else:
            epoch_ms = int(time.time() * 1000)
    except:
        epoch_ms = int(time.time() * 1000)

    pdf_file = item.get('ATTACHMENTNAME') or item.get('attchmntFile') or ''
    pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_file}" if pdf_file else ''

    desc_lower = raw_desc.lower()
    impact = 'C' if any(x in desc_lower for x in [
        'dividend', 'result', 'earnings', 'merger', 'acquisition',
        'profit', 'loss', 'buyback', 'npa', 'quarterly', 'q1', 'q2', 'q3', 'q4'
    ]) else 'M'

    return {
        "type": "NEW_SIGNAL",
        "data": {
            "id": f"bse_{news_id}",
            "symName": sym_name,
            "title": raw_desc[:300],
            "body": raw_desc[:500],
            "impact": impact,
            "ts": epoch_ms,
            "pdf": pdf_url,
            "src": "BSE Live"
        }
    }


@app.get("/")
async def root():
    return {"status": "🟢 FNO Edge Engine Active", "timestamp": int(time.time())}


@app.get("/health")
async def health():
    """Keep-alive endpoint — ping this every 10 min to prevent Render cold start"""
    return {"ok": True, "ts": int(time.time()), "clients": len(connected_clients)}


@app.get("/api/calendar")
async def get_calendar():
    data = fetch_calendar_data()
    return {"data": data, "count": len(data)}


@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"Client connected. Total: {len(connected_clients)}")

    # Send latest 30 announcements immediately on connect
    try:
        initial_data = fetch_exchange_data()
        if initial_data:
            for item in reversed(initial_data[:30]):
                payload = format_payload(item)
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(0.02)
        else:
            # Send a status message so frontend knows server is alive
            await websocket.send_text(json.dumps({
                "type": "STATUS",
                "data": {"message": "Engine connected. Waiting for exchange data..."}
            }))
    except Exception as e:
        print(f"Error sending initial data: {e}")

    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.discard(websocket)
        print(f"Client disconnected. Total: {len(connected_clients)}")


async def instant_fetcher():
    """Poll BSE every 20s and push new announcements to all connected clients"""
    last_news_id = None
    consecutive_failures = 0

    while True:
        try:
            if connected_clients:
                data = fetch_exchange_data()
                if data:
                    consecutive_failures = 0
                    latest = data[0]
                    current_id = latest.get('NEWSID') or latest.get('id')

                    if current_id and current_id != last_news_id and last_news_id is not None:
                        payload = format_payload(latest)
                        dead = set()
                        for client in connected_clients:
                            try:
                                await client.send_text(json.dumps(payload))
                            except:
                                dead.add(client)
                        connected_clients -= dead
                    if current_id:
                        last_news_id = current_id
                else:
                    consecutive_failures += 1
        except Exception as e:
            print(f"Fetcher error: {e}")
            consecutive_failures += 1

        # Back off if repeated failures
        wait = 20 if consecutive_failures < 3 else 60
        await asyncio.sleep(wait)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(instant_fetcher())
    print("✅ FNO Edge Engine started")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
