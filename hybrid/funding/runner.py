
import os, time, json, asyncio
import httpx, redis
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE = os.getenv("FUNDING_QUEUE", "hb:opps:funding")
MIN_ABS_FUNDING_PCT = float(os.getenv("FUNDING_MIN_ABS_PCT", "0.02"))  # 0.02% / 8h
SCAN_INTERVAL_SEC = int(os.getenv("FUNDING_SCAN_SEC", "30"))

r = redis.from_url(REDIS_URL)

BINANCE_FUNDING = "https://fapi.binance.com/fapi/v1/premiumIndex"  # public
BYBIT_TICKERS = "https://api.bybit.com/v5/market/tickers?category=linear"  # public; funding field may require another endpoint

async def binance_scan(client):
    try:
        res = await client.get(BINANCE_FUNDING, timeout=5)
        res.raise_for_status()
        data = res.json()
        cands=[]
        for row in data:
            s=row.get("symbol","")
            try:
                fr = float(row.get("lastFundingRate","0"))*100
            except:
                fr=0.0
            if abs(fr) >= MIN_ABS_FUNDING_PCT:
                cands.append({"ex":"BINANCE","symbol":s,"funding_pct_8h":fr})
        return cands
    except Exception as e:
        print("[FUND] binance error:", e)
        return []

async def bybit_scan(client):
    try:
        res = await client.get(BYBIT_TICKERS, timeout=5)
        res.raise_for_status()
        data = res.json().get("result",{}).get("list",[])
        # Placeholder: API may not include funding here; keep structure for future
        return []
    except Exception as e:
        print("[FUND] bybit error:", e)
        return []

async def main():
    async with httpx.AsyncClient() as client:
        while True:
            out=[]
            b=await binance_scan(client); out+=b
            y=await bybit_scan(client); out+=y
            if out:
                msg={"ts":time.time(),"candidates":out}
                r.lpush(QUEUE, json.dumps(msg))
                print("[FUND] queued", len(out), "candidates")
            await asyncio.sleep(SCAN_INTERVAL_SEC)

if __name__=="__main__":
    asyncio.run(main())
