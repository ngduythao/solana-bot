
import os, asyncio, json, websockets, redis
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)
RPC_WS=os.getenv("RPC_WS","wss://api.mainnet-beta.solana.com")

async def main():
    print("[wsrpc] connect", RPC_WS)
    async with websockets.connect(RPC_WS) as ws:
        sub={"jsonrpc":"2.0","id":1,"method":"blockSubscribe","params":[{"commitment":"finalized"}]}
        await ws.send(json.dumps(sub))
        while True:
            msg=await ws.recv()
            try:
                j=json.loads(msg)
                if "result" in j or "params" in j:
                    r.set("solbot:ws:last",msg,ex=30)
            except: pass

if __name__=="__main__":
    asyncio.run(main())
