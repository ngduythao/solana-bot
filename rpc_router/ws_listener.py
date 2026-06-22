
import os, asyncio, json, redis, websockets, time

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
ONCHAIN_WS = os.getenv("ONCHAIN_WS","wss://api.mainnet-beta.solana.com")
r = redis.from_url(REDIS_URL)

async def main():
    while True:
        try:
            async with websockets.connect(ONCHAIN_WS, ping_interval=20) as ws:
                # Subscribe to slot notifications
                await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"slotSubscribe"}))
                while True:
                    msg = await ws.recv()
                    ts = int(time.time())
                    try:
                        data = json.loads(msg)
                        slot = data.get("params",{}).get("result",{}).get("slot")
                        if slot is not None:
                            r.set("slot:latest", str(slot))
                            r.set("slot:ts", str(ts))
                    except Exception:
                        pass
        except Exception:
            await asyncio.sleep(2.0)

if __name__=='__main__':
    asyncio.run(main())
