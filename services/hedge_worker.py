
import os, time, json, httpx
import redis

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
r = redis.from_url(REDIS_URL)
JUP = os.getenv("JUP_BASE","https://quote-api.jup.ag")
SLIPPAGE_BPS = int(os.getenv("HEDGE_SLIPPAGE_BPS","30"))
QUOTE_TOKEN = os.getenv("QUOTE_TOKEN","USDC")

MINTS = {
  "SOL": "So11111111111111111111111111111111111111112",
  "USDC":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "JUP":"JUP2jxvGmG2h3zWZ1j5qS9gGZ7wS9Vt7d1b7W5HYi",
  "BONK":"DezXAZ8z7Pnrn974i1qAqE9v6zE2fqBeH5bC7Z7x8Px",
  "WIF":"WifQ1RZ1xWifxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}

def best_route(inp_mint, out_mint, amount_usd):
    # Simplified: assume USDC decimals 6; size is USD
    amt = int(amount_usd * 1_000_000)
    with httpx.Client(timeout=5.0) as c:
        q = c.get(f"{JUP}/v6/quote", params={
            "inputMint": MINTS["USDC"] if inp_mint==MINTS["USDC"] else inp_mint,
            "outputMint": out_mint,
            "amount": amt,
            "slippageBps": SLIPPAGE_BPS,
            "onlyDirectRoutes": True
        })
        q.raise_for_status()
        data = q.json().get("data",[])
        return data[0] if data else None

def main():
    print("[hedge_worker] running")
    while True:
        raw = r.brpop("hsbot:hedge", timeout=1)
        if not raw: 
            continue
        _, payload = raw
        job = json.loads(payload)
        size = float(job.get("size_usd",0))
        to = (job.get("to") or QUOTE_TOKEN).upper()
        if size<=0 or to not in MINTS:
            continue
        route = best_route(MINTS["USDC"], MINTS[to], size) if to!="USDC" else None
        order = {
            "type":"hedge",
            "size_usd": size,
            "to": to,
            "route": route,
            "ts": time.time()
        }
        r.lpush("hsbot:orders", json.dumps(order))
        r.publish("hsbot:alerts", json.dumps({"type":"hedge_order", "size_usd": size, "to": to}))

if __name__=="__main__":
    main()
