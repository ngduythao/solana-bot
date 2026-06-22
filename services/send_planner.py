
import os, json, time, random, redis

r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def plan_send(relays, total_parts:int=3, base_stagger_ms:int=3):
    rnd = random.Random(time.time_ns())
    order = relays[:]
    rnd.shuffle(order)
    parts = max(1, min(8, int(total_parts)))
    plan = []
    for i in range(parts):
        rel = order[i % len(order)] if order else None
        delay_ms = int((i*base_stagger_ms) + rnd.random()*base_stagger_ms)
        fee_bump = 1.0 + rnd.random()*0.02  # ±2%
        plan.append({"relay": rel, "delay_ms": delay_ms, "fee_bump": fee_bump})
    r.setex("solbot:send_plan:last", 60, json.dumps(plan))
    return plan
