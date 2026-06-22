
import os, time, redis
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
KEY_MULT=os.getenv("FEE_REC_KEY","fee:prio_mult")
KEY_LAMPORTS=os.getenv("FEE_LAMPORTS_KEY","fee:lamports")
BASE_LAMPORTS=int(os.getenv("FEE_BASE_LAMPORTS","8000"))
CONG_KEY=os.getenv("NET_CONGESTION_KEY","net:congestion")  # 0..1

r=redis.from_url(REDIS_URL)
app=FastAPI(title="PriorityFee")

def calc_lamports():
    try:
        mult=float(r.get(KEY_MULT) or 1.0)
    except:
        mult=1.0
    try:
        cong=float(r.get(CONG_KEY) or 0.5)
    except:
        cong=0.5
    lam = int(BASE_LAMPORTS * (0.5+cong) * mult)
    lam = max(1000, min(lam, 1_000_000))
    return lam

@app.post("/tick")
def tick():
    lam = calc_lamports()
    r.set(KEY_LAMPORTS, lam)
    return {"ok": True, "lamports": lam}

@app.get("/metrics")
def metrics():
    v=int(r.get(KEY_LAMPORTS) or 0)
    return {"lamports": v}
