
# Cross-venue arbitrage (CEX ↔ DEX) stub: compares CEX price vs DEX quote; if EV >= threshold, dispatch legs.
import os, time, json, httpx, redis
from dotenv import load_dotenv

load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
DQ_DEX=os.getenv("DQ_DEX","hb:dispatch:dex")
DQ_CEX=os.getenv("DQ_CEX","hb:dispatch:cex")
JUP_BASE=os.getenv("JUP_BASE","https://quote-api.jup.ag")
PAIRS=os.getenv("CROSS_ROUTES","SOLUSDT:SOL/USDC,JUPUSDT:JUP/USDC,WIFUSDT:WIF/USDC,BONKUSDT:BONK/USDC")
EV_THR=float(os.getenv("CROSS_EV_THR_BPS","5"))
SLIP_BPS=float(os.getenv("CROSS_SLIPPAGE_BPS","15"))
SIZE_USD=float(os.getenv("CROSS_SIZE_USD","500"))
ONLY_DIRECT=os.getenv("CROSS_ONLY_DIRECT","true").lower()=="true"
VENUES=[s.strip().upper() for s in os.getenv("CROSS_VENUE","BINANCE,BYBIT").split(",") if s.strip()]

r=redis.from_url(REDIS_URL)
routes=[x for x in (s.strip() for s in PAIRS.split(',')) if x]

MINTS = {
  "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "SOL": "So11111111111111111111111111111111111111112",
  "JUP": "JUP2jxvGmG2h3zWZ1j5qS9gGZ7wS9Vt7d1b7W5HYi",
  "WIF": "WifQ1RZ1xWifxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "BONK": "DezXAZ8z7Pnrn974i1qAqE9v6zE2fqBeH5bC7Z7x8Px"
}
PAIR_MAP = {
  "SOL/USDC": (MINTS["USDC"], MINTS["SOL"]),
  "JUP/USDC": (MINTS["USDC"], MINTS["JUP"]),
  "WIF/USDC": (MINTS["USDC"], MINTS["WIF"]),
  "BONK/USDC": (MINTS["USDC"], MINTS["BONK"]),
}

def bn_price(client, sym):
    url = "https://api.binance.com/api/v3/ticker/price"
    res = client.get(url, params={"symbol": sym}, timeout=2)
    res.raise_for_status()
    return float(res.json()["price"])

def bybit_price(client, sym):
    url = "https://api.bybit.com/v5/market/tickers"
    # try linear
    res = client.get(url, params={"category":"linear","symbol": sym}, timeout=2)
    res.raise_for_status()
    lst = res.json().get("result",{}).get("list",[])
    if lst:
        return float(lst[0]["lastPrice"])
    # fallback spot
    res = client.get(url, params={"category":"spot","symbol": sym}, timeout=2)
    res.raise_for_status()
    lst = res.json().get("result",{}).get("list",[])
    if not lst:
        raise RuntimeError("Bybit no ticker")
    return float(lst[0]["lastPrice"])

def jup_quote(client, pair, amount_usd):
    if pair not in PAIR_MAP:
        return None
    inp, out = PAIR_MAP[pair]
    params = {
        "inputMint": inp,
        "outputMint": out,
        "amount": int(amount_usd * 1_000_000),
        "slippageBps": int(SLIP_BPS),
        "onlyDirectRoutes": ONLY_DIRECT,
    }
    res = client.get(f"{JUP_BASE}/v6/quote", params=params, timeout=3)
    res.raise_for_status()
    data = res.json().get("data", [])
    return data[0] if data else None

def get_cex_price(client, sym):
    for v in VENUES:
        try:
            if v == "BINANCE":
                return bn_price(client, sym)
            elif v == "BYBIT":
                return bybit_price(client, sym)
        except Exception:
            continue
    return None

def run():
    with httpx.Client() as client:
        while True:
            for item in routes:
                try:
                    sym, pair = item.split(':')
                    cpx = get_cex_price(client, sym)
                    if cpx is None:
                        continue
                    q = jup_quote(client, pair, SIZE_USD)
                    if not q:
                        continue
                    in_amt = float(q.get("inAmount",0))/1e6
                    if in_amt <= 0:
                        continue
                    # Effective DEX quote price in USDC terms
                    dex_px = SIZE_USD / in_amt
                    spread_bps = ((cpx - dex_px) / max(1e-9, dex_px)) * 1e4
                    ev_bps = spread_bps - SLIP_BPS
                    if ev_bps >= EV_THR:
                        lam = 0
                        try:
                            lam = int(r.get("fee:lamports") or 0)
                        except Exception:
                            pass
                        r.lpush(DQ_DEX, json.dumps({
                            "type":"DEX_TRADE","pair":pair,"size_usd":SIZE_USD,
                            "priority_lamports": lam, "reason":"CROSS_ARB"
                        }))
                        venue_type = "FUTURES" if sym in ("SOLUSDT","BTCUSDT","ETHUSDT") else "SPOT"
                        r.lpush(DQ_CEX, json.dumps({
                            "type":"CEX_HEDGE","venue":"BINANCE","venue_type":venue_type,
                            "symbol": sym, "side":"SELL","size_usd": SIZE_USD, "reason":"CROSS_ARB"
                        }))
                        print("[CROSS] fired", sym, pair, "ev_bps=", round(ev_bps,2))
                except Exception as e:
                    print("[CROSS] err", item, e)
            time.sleep(0.8)

if __name__ == "__main__":
    run()
