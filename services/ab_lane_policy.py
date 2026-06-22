
import os, time, json, redis, random
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
EXP_RATE=float(os.getenv("AB_EXP_RATE","0.1"))  # 10% explore
def choose_lane(relays):
    if not relays: return None
    if random.random() < EXP_RATE:
        return random.choice(relays)  # explore
    # exploit: pick best from scheduler hour table
    hour = int(time.time()//3600)%24
    sched = json.loads(r.get("solbot:lane_schedule") or b"{}")
    row = sched.get(str(hour), {})
    scored = [(row.get(rel,0), rel) for rel in relays]
    scored.sort(reverse=True)
    return scored[0][1] if scored else relays[0]
def main():
    print("[ab_lane] running")
    while True:
        try:
            plan_raw=r.get("solbot:send_plan:last")
            if plan_raw:
                plan=json.loads(plan_raw)
                rels=list({p.get("relay") for p in plan if p.get("relay")})
                top=choose_lane(rels)
                if top:
                    # annotate best relay for first chunk
                    plan[0]["relay"]=top; r.setex("solbot:send_plan:last", 60, json.dumps(plan))
        except Exception: pass
        time.sleep(1)
if __name__=="__main__":
    main()
