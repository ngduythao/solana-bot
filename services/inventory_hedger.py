
import os, time, json, redis, httpx
from analytics.metrics_utils import write_metric
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
JUP = os.getenv("JUP_BASE","https://quote-api.jup.ag")
EXPO_THRESH = float(os.getenv("HEDGE_EXPO_THRESH_USD","200.0"))
HEDGE_RATIO = float(os.getenv("HEDGE_RATIO","0.6"))
HEDGE_PER_MINT_LIMIT = os.getenv("HEDGE_PER_MINT_LIMIT_USD","SOL:1000,BONK:500")
HEDGE_MIN_INTERVAL_SEC = int(os.getenv("HEDGE_MIN_INTERVAL_SEC","3"))
HEDGE_MIN_INTERVAL_SEC_MAP = os.getenv("HEDGE_MIN_INTERVAL_SEC_MAP","SOL:2,BONK:5")
HEDGE_RATIO_MAP = os.getenv("HEDGE_RATIO_MAP","SOL:0.7,BONK:0.5")
async def get_balance_usd(mint):
    px = float((r.get(f"price:{mint}") or b"0").decode() or 0)
    bal = float((r.get(f"balance:{mint}") or b"0").decode() or 0)
    return bal*px
async def hedge_reverse(inp_mint, out_mint, amount):
    async with httpx.AsyncClient() as client:
        p = {"inputMint": out_mint, "outputMint": inp_mint, "amount": int(amount), "onlyDirectRoutes": True, "swapMode":"ExactIn"}
        try:
            res = await client.get(f"{JUP}/v6/quote", params=p, timeout=2.0)
            data = res.json().get("data",[])
            if not data: return False
            write_metric("hedge_attempt", route=f"{out_mint}->{inp_mint}", pnl_usd=0.0, latency_ms=0, note="EXEC")
            # push real order to executor queue
            r.rpush("hsbot:orders", json.dumps({"type":"hedge","size_usd": float(amount)/1_000_000, "from": out_mint, "to": inp_mint, "to":"USDC", "priority":"hedge", "from_symbol": baseU, "size_usd": float(usd_amt)}))
            return True
        except Exception:
            return False


def _parse_map(env_val, cast=float):
    out={}
    try:
        for part in (env_val or "").split(","):
            if not part.strip(): continue
            k,v = part.split(":")
            out[k.strip().upper()] = cast(v)
    except Exception:
        pass
    return out

def _limit_map():

    out={}
    try:
        for part in (HEDGE_PER_MINT_LIMIT or "").split(","):
            if not part.strip(): continue
            k,v = part.split(":")
            out[k.strip().upper()] = float(v)
    except Exception:
        pass
    return out

async def loop():

    import asyncio
    hot = [x.decode() for x in (r.lrange("hsbot:hotpairs", 0, -1) or [])]
    while True:
        for pair in hot:
            try:
                base, quote, _ = (pair.split(":")+["","", "0"])[:3]
                expo = await get_balance_usd(base)
                if expo > EXPO_THRESH:
                    await hedge_reverse(base, quote, int(expo*HEDGE_RATIO))
            except Exception:
                pass
        await asyncio.sleep(2.0)
if __name__=="__main__":
    import asyncio
    asyncio.run(loop())
