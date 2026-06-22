
import os, json, time, asyncio, random, redis
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception:
    pass

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
MICRO_STAGGER_US=int(os.getenv("FAST_STAGGER_US","700"))   # microseconds between parallel paths
MAX_RELAYS=int(os.getenv("FAST_MAX_RELAYS","2"))
FAST_LOG=os.getenv("FAST_LOG","0")=="1"

async def send_one(relay: str, bundle_b64: str):
    # Placeholder: integrate real Jito gRPC here. We just sleep a few ms to emulate send.
    await asyncio.sleep(0.001)
    return {"relay": relay, "ok": True, "ts": time.time()}

async def fastpath(plan: dict):
    # Extract relay candidates & build parallel tasks
    rels = (plan.get("relay_candidates") or [])[:MAX_RELAYS]
    if not rels:
        return {"ok": False, "reason": "no_relays"}
    bundle = plan.get("bundle_b64","") or "AA=="  # placeholder
    tasks = []
    for i, rel in enumerate(rels):
        delay = (i * MICRO_STAGGER_US) / 1_000_000.0
        async def run(rel=rel, delay=delay):
            if delay>0: await asyncio.sleep(delay)
            return await send_one(rel, bundle)
        tasks.append(asyncio.create_task(run()))
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=0.300)
    res = list(done)[0].result() if done else {"ok": False, "reason": "timeout"}
    # cancel others
    for t in pending: t.cancel()
    return res

async def prewarm_relays():
    # touch relay set to warm cache / DNS / TLS (placeholder pings)
    relset=set()
    for k in r.scan_iter(match="jito:relay_stats:*"):
        relset.add(k.decode())
    for rel in list(relset)[:6]:
        try:
            await asyncio.create_task(send_one(rel, "AA=="))
        except Exception:
            pass

async def main_loop():
    last_prewarm=0
    while True:
        try:
            if time.time()-last_prewarm>10:
                await prewarm_relays(); last_prewarm=time.time()
            raw = r.get("solbot:bundle_plan:stealth")
            if not raw:
                await asyncio.sleep(0.0008); continue
            plan = json.loads(raw)
            res = await fastpath(plan)
            if FAST_LOG:
                r.lpush("solbot:fast_res", json.dumps({"ts":time.time(),"res":res})); r.ltrim("solbot:fast_res",0,999)
            # write landing decision
            r.setex("solbot:last_send", 5, json.dumps(res))
            r.delete("solbot:bundle_plan:stealth")
        except Exception:
            await asyncio.sleep(0.0005)

if __name__=="__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        pass
