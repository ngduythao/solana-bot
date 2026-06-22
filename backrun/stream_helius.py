
import os, json, asyncio, websockets, redis, time
from dotenv import load_dotenv
load_dotenv()

HELIUS_KEY = os.getenv("HELIUS_KEY","")
REDIS_URL  = os.getenv("REDIS_URL","redis://localhost:6379/0")
OUT_Q      = os.getenv("Q_BACKRUN","hsbot:backrun")

# Raydium/Orca/Meteora program ids (example mainnet)
PROGRAMS = [
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8", # Raydium AMM v4
    "whirLbMiicVdio4qvUfM5sq6rD7NK8YwPfCwZ4bGJ6E", # Orca Whirlpool (placeholder)
    "MeteoraDLMM11111111111111111111111111111111",   # placeholder, replace with real
]

r = redis.from_url(REDIS_URL)

async def run():
    if not HELIUS_KEY:
        print("[BR-WS] HELIUS_KEY missing, emit heartbeat only")
        i=0
        while True:
            i+=1
            r.lpush(OUT_Q, json.dumps({"type":"heartbeat","i":i,"ts":time.time()}))
            await asyncio.sleep(5)
    else:
        url = f"wss://stream.helius.xyz/v0/transactions?api-key={HELIUS_KEY}"
        subs = [{"programId": pid} for pid in PROGRAMS]
        payload = json.dumps({"type":"subscribe", "commitment":"processed", "filters": subs})
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
            await ws.send(payload)
            print("[BR-WS] subscribed")
            async for raw in ws:
                try:
                    data = json.loads(raw)
                    # Push raw tx for orchestrator to evaluate as backrun candidate
                    r.lpush(OUT_Q, json.dumps({"type":"swap_tx","data":data,"ts":time.time()}))
                except Exception as e:
                    print("[BR-WS] err", e)

if __name__=="__main__":
    asyncio.run(run())
