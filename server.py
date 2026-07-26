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

# Comprehensive Master List of NSE F&O Stocks
FNO_MASTER = {
    "AARTIIND", "ABB", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "ACC", "ADANIENT", "ADANIPORTS", "ALKEM", 
    "AMBUJACEM", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "ATUL", "AUBANK", 
    "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BALKRISIND", "BALRAMCHIN", 
    "BANDHANBNK", "BANKBARODA", "BATAINDIA", "BEL", "BERGEPAINT", "BHARATFORG", "BHARTIARTL", "BHEL", 
    "BIOCON", "BOSCHLTD", "BPCL", "BRITANNIA", "CANBK", "CANFINHOME", "CHAMBLFERT", "CHOLAFIN", "CIPLA", 
    "COALINDIA", "COFORGE", "COLPAL", "CONCOR", "COROMANDEL", "CROMPTON", "CUB", "CUMMINSIND", "DABUR", 
    "DALBHARAT", "DEEPAKNTR", "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND", 
    "FEDERALBNK", "GAIL", "GLENMARK", "GMRINFRA", "GNFC", "GODREJCP", "GODREJPROP", "GRANULES", "GRASIM", 
    "GUJGASLTD", "HAL", "HAVELLS", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", 
    "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDEA", "IDFC", 
    "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", "INDIACEM", "INDIAMART", "INDIGO", "INDUSINDBK", "INDUSTOWER", 
    "INFY", "INTELLECT", "IOC", "IPCALAB", "IRCTC", "ITC", "JINDALSTEL", "JKCEMENT", "JSWSTEEL", "JUBLFOOD", 
    "KOTAKBANK", "L&TFH", "LALPATHLAB", "LAURUSLABS", "LICHSGFIN", "LT", "LTIM", "LTTS", "LUPIN", "M&M", 
    "M&MFIN", "MANAPPURAM", "MARICO", "MARUTI", "MCDOWELL-N", "MCX", "METROPOLIS", "MFSL", "MGL", "MOTHERSON", 
    "MPHASIS", "MRF", "MUTHOOTFIN", "NATIONALUM", "NAUKRI", "NAVINFLUOR", "NESTLEIND", "NMDC", "NTPC", 
    "OBEROIRLTY", "OFSS", "ONGC", "PAGEIND", "PEL", "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", 
    "PNB", "POLYCAB", "POWERGRID", "PVRINOX", "RAMCOCEM", "RBLBANK", "RECLTD", "RELIANCE", "SAIL", "SBICARD", 
    "SBILIFE", "SBIN", "SHREECEM", "SIEMENS", "SRF", "SUNPHARMA", "SUNTV", "SYNGENE", "TATACHEM", "TATACOMM", 
    "TATACONSUM", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TORNTPOWER", 
    "TRENT", "TVSMOTOR", "UBL", "ULTRACEMCO", "UPL", "VEDL", "VOLTAS", "WIPRO", "ZEEL", "ZYDUSLIFE"
}

@app.get("/")
def home():
    return {"status": "FNO Edge Live Engine Online"}

@app.get("/api/signals")
def get_signals():
    # Base feed array
    raw_feed = [
        {"id": 1, "symbol": "RELIANCE", "category": "Financial Results & Dividend", "priority": "CRITICAL", "subject": "Reliance Industries Limited has announced Q1 Financial Results alongside an Interim Dividend declaration.", "date": "26-Jul-2026 18:30:00", "attachement": "https://www.nseindia.com/content/equities/RELIANCE_Q1.pdf"},
        {"id": 2, "symbol": "HDFCBANK", "category": "Board Meeting", "priority": "MEDIUM", "subject": "HDFC Bank Limited Board Meeting intimation scheduled for reviewing capital raising options.", "date": "26-Jul-2026 17:15:00", "attachement": "https://www.nseindia.com/content/equities/HDFC_MEET.pdf"},
        {"id": 3, "symbol": "TCS", "category": "Contracts & Orders", "priority": "MEDIUM", "subject": "TCS bags multi-year digital transformation contract valued over $500 million.", "date": "26-Jul-2026 16:40:00", "attachement": "https://www.nseindia.com/content/equities/TCS_CONTRACT.pdf"},
        {"id": 4, "symbol": "INFY", "category": "Buyback / Capital Action", "priority": "CRITICAL", "subject": "Infosys Limited fixes record date for upcoming share buyback tender offer.", "date": "26-Jul-2026 15:20:00", "attachement": "https://www.nseindia.com/content/equities/INFY_BUYBACK.pdf"},
        {"id": 5, "symbol": "ZOMATO", "category": "General Corporate Update", "priority": "GENERAL", "subject": "Zomato periodic investor presentation detailing quick-commerce unit economics.", "date": "26-Jul-2026 14:10:00", "attachement": "https://www.nseindia.com/content/equities/ZOMATO_UPDATE.pdf"},
        {"id": 6, "symbol": "YESBANK", "category": "Financial Results", "priority": "MEDIUM", "subject": "Yes Bank non-F&O mock filing (will be filtered out).", "date": "26-Jul-2026 12:10:00", "attachement": None}
    ] * 10 
    
    # STRICT FILTER: Only return items where the symbol exists in the FNO_MASTER list
    fno_only_feed = [item for item in raw_feed if item.get('symbol', '').upper() in FNO_MASTER]
    
    return {"data": fno_only_feed[:50]} # Enforce maximum 50 announcements

@app.get("/api/calendar")
def get_calendar():
    raw_calendar = [
        {"symbol": "RELIANCE", "purpose": "Interim Dividend - Rs 10 Per Share", "exDate": "2026-08-12", "priority": "CRITICAL"},
        {"symbol": "HDFCBANK", "purpose": "Annual General Meeting & Dividend Payout", "exDate": "2026-08-18", "priority": "MEDIUM"},
        {"symbol": "TCS", "purpose": "Financial Results & Earnings Conference Call", "exDate": "2026-08-25", "priority": "CRITICAL"},
        {"symbol": "ITC", "purpose": "Dividend Record Date", "exDate": "2026-09-02", "priority": "MEDIUM"},
        {"symbol": "ZOMATO", "purpose": "Investor Day Presentation", "exDate": "2026-09-15", "priority": "GENERAL"},
        {"symbol": "SUZLON", "purpose": "AGM", "exDate": "2026-09-20", "priority": "GENERAL"}
    ]
    
    # STRICT FILTER: Apply the same master list to the calendar
    fno_only_calendar = [item for item in raw_calendar if item.get('symbol', '').upper() in FNO_MASTER]
    
    return {"data": fno_only_calendar}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
