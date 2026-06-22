
import os, time, json, httpx, redis, asyncio
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
RPCS = [x.strip() for x in os.getenv("RPC_CANDIDATES","").split(",") if x.strip()]
RELAYS = [x.strip() for x in os.getenv("JITO_RELAYS_CANDIDATES","").split(",") if x.strip()]

async def ping_rpc(client, url):
    t0 = time.perf_counter()
    try:
        payload = {"jsonrpc":"2.0","id":1,"method":"getHealth"}
        res = await client.post(url, json=payload, timeout=1.0)
        res.raise_for_status()
        _ = res.json()
        return (time.perf_counter()-t0)*1000
    except Exception:
        return 1e9

async def ping_relays(client, url):
    t0 = time.perf_counter()
    try:
        await asyncio.sleep(0.02)
        return (time.perf_counter()-t0)*1000
    except Exception:
        return 1e9

async def main():
    async with httpx.AsyncClient() as client:
        while True:
            if RPCS:
                rpcrt = [(await ping_rpc(client,u),u) for u in RPCS]
                rpcrt.sort()
                if rpcrt:
                    r.set("hsbot:cfg:rpc_primary", rpcrt[0][1])
                    r.set("hsbot:cfg:rpc_ranked", json.dumps([u for _,u in rpcrt]))
            if RELAYS:
                relrt = [(await ping_relays(client,u),u) for u in RELAYS]
                relrt.sort()
                if relrt:
                    r.set("hsbot:cfg:jito_relays", json.dumps([u for _,u in relrt]))
            await asyncio.sleep(5)
if __name__=="__main__":
    asyncio.run(main())
