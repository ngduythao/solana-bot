
stop=False

def _stop_sig(*_):
    global stop; stop=True
signal.signal(signal.SIGTERM, _stop_sig)
signal.signal(signal.SIGINT, _stop_sig)
import signal, sys

import os, asyncio, json, websockets, redis, time

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
RPC_WS    = os.getenv("RPC_WS","wss://api.mainnet-beta.solana.com")
r = redis.from_url(REDIS_URL)

async def ws_loop():
    while not stop:
        try:
            async with websockets.connect(RPC_WS, ping_interval=20) as ws:
                print("[ws_rpc] connected")
                # subscribe blockhash and slot updates
                # getLatestBlockhash isn't a subscribe method; we'll poll via RPC-over-WS periodically
                sub_id = None
                # subscribe slots
                await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"slotSubscribe"}))
                while not stop:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        r.setex("rpcws:last_raw", 30, msg)
                        j = json.loads(msg)
                        if j.get("method") == "slotNotification":
                            slot = j["params"]["result"]["slot"]
                            r.setex("rpcws:slot", 10, str(slot))
                    except asyncio.TimeoutError:
                        # poll blockhash
                        req = {"jsonrpc":"2.0","id":2,"method":"getLatestBlockhash","params":[{"commitment":"processed"}]}
                        await ws.send(json.dumps(req))
                        try:
                            rep = await asyncio.wait_for(ws.recv(), timeout=2.0)
                            d = json.loads(rep)
                            bh = d.get("result",{}).get("value",{}).get("blockhash")
                            if bh:
                                r.setex("rpcws:blockhash", 10, bh)
                        except Exception:
                            pass
        except Exception as e:
            print("[ws_rpc] reconnect in 2s", e)
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(ws_loop())
