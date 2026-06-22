import os, time, asyncio, httpx
from dotenv import load_dotenv

load_dotenv()

# Simple funding scanner stub (Binance/Bybit public endpoints as placeholders)
# Production should use authenticated endpoints & perps list via exchange SDK.
BINANCE_FUNDING = "https://fapi.binance.com/fapi/v1/premiumIndex"
BYBIT_FUNDING = "https://api.bybit.com/v5/market/tickers?category=linear"

MIN_ABS_FUNDING_PCT = float(os.getenv("FUNDING_MIN_ABS_PCT", "0.02"))  # 0.02% per 8h
SCAN_INTERVAL_SEC = int(os.getenv("FUNDING_SCAN_SEC", "30"))

async def binance_scan(client):
    try:
        r = await client.get(BINANCE_FUNDING, timeout=5)
        r.raise_for_status()
        data = r.json()
        out = []
        for row in data:
            s = row.get("symbol","")
            fr = float(row.get("lastFundingRate","0")) * 100
            if abs(fr) >= MIN_ABS_FUNDING_PCT:
                out.append((s, fr))
        return out
    except Exception as e:
        print("binance_scan error:", e)
        return []

async def bybit_scan(client):
    try:
        r = await client.get(BYBIT_FUNDING, timeout=5)
        r.raise_for_status()
        data = r.json().get("result",{}).get("list",[])
        # Funding rate not always included in this endpoint; placeholder logic
        return []
    except Exception as e:
        print("bybit_scan error:", e)
        return []

async def main():
    async with httpx.AsyncClient() as client:
        while True:
            b = await binance_scan(client)
            if b:
                print("[FUNDING] Binance candidates:", b[:10])
            y = await bybit_scan(client)
            if y:
                print("[FUNDING] Bybit candidates:", y[:10])
            await asyncio.sleep(SCAN_INTERVAL_SEC)

if __name__ == "__main__":
    asyncio.run(main())
