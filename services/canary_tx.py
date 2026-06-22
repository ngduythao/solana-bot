
import os, time, json, base58, redis, httpx, asyncio
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

ENABLE_CANARY=os.getenv("ENABLE_CANARY","0")=="1"
PUBLIC_FALLBACK=os.getenv("PUBLIC_RPC_FALLBACK","0")=="1"
WHITELIST=set((os.getenv("PUBLIC_FALLBACK_WHITELIST","127.0.0.1,::1").split(",")))
RPC_PRIMARY=os.getenv("RPC_PRIMARY","https://api.mainnet-beta.solana.com")

async def send_private(tx_b58):
    from services.jito_client import fanout_send_bundle
    return await fanout_send_bundle([tx_b58])

def send_public(tx_b58):
    # Only allow when source IP is in whitelist (best-effort — here we just enforce env flag)
    if not PUBLIC_FALLBACK: return False
    if not PUBLIC_FALLBACK: return False
    try:
        with httpx.Client(timeout=2) as c:
            res=c.post(RPC_PRIMARY,json={"jsonrpc":"2.0","id":1,"method":"sendTransaction","params":[tx_b58,{"skipPreflight":True}]})
            return res.status_code==200
    except Exception: return False

def make_canary_tx():
    # Placeholder: empty tx (not broadcast). In real use, build a small no-op.
    return "3b58canary"

async def main():
    if not ENABLE_CANARY: 
        print("[canary] disabled"); return
    print("[canary] running")
    while True:
        try:
            tx=make_canary_tx()
            ok=await send_private(tx)
            if not ok: ok=send_public(tx)
            r.lpush("solbot:canary", json.dumps({"ok":bool(ok),"ts":time.time()})); r.ltrim("solbot:canary",0,100)
        except Exception: pass
        await asyncio.sleep(30)

if __name__=="__main__":
    asyncio.run(main())
