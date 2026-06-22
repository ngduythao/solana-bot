
import os, time, json, random, redis
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
KEY="fee:prio_mult"
BANDS=[0.8, 1.0, 1.2, 1.5, 2.0]
EPS=float(os.getenv("BANDIT_EPSILON","0.1"))
r=redis.from_url(REDIS_URL)
app=FastAPI(title="AI Fee Bandit")

def get_stats():
    # read simplistic stats we might store later
    return {"accept_rate": float(r.get("bundle:accept_rate") or 0.0)}

def choose_band():
    # epsilon-greedy over bands; placeholder uses accept_rate to nudge up/down
    stats=get_stats()
    if random.random()<EPS:
        return random.choice(BANDS)
    ar=stats["accept_rate"]
    if ar<0.6: return min(2.0, 1.2)
    if ar>0.85: return 0.8
    return 1.0

@app.get("/metrics")
def metrics():
    v=float(r.get(KEY) or 1.0)
    return {"prio_mult": v, "epsilon": EPS}

@app.post("/tick")
def tick():
    v=choose_band()
    r.set(KEY, v)
    return {"ok":True,"prio_mult":v}
