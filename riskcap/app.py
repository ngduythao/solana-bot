
import os, time, json, redis, yaml
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
CONFIG_PATH = os.getenv("CONFIG_PATH","config.yaml")

r = redis.from_url(REDIS_URL)
cfg = yaml.safe_load(open(CONFIG_PATH,'r'))

# Simple in-redis counters
KEY_PNL_DAY = "hb:pnl:day"
KEY_FEE_BURN_DAY = "hb:fee_burn:day"

app = FastAPI(title="RiskCap")

@app.get("/metrics")
def metrics():
    pnl = float(r.get(KEY_PNL_DAY) or 0)
    burn = float(r.get(KEY_FEE_BURN_DAY) or 0)
    return {"pnl_day": pnl, "fee_burn_day": burn, "limits": cfg.get("risk",{})}

@app.post("/acc/pnl/{delta}")
def acc_pnl(delta: float):
    r.incrbyfloat(KEY_PNL_DAY, delta); 
    return {"ok": True, "pnl_day": float(r.get(KEY_PNL_DAY) or 0)}

@app.post("/acc/fee/{delta}")
def acc_fee(delta: float):
    r.incrbyfloat(KEY_FEE_BURN_DAY, delta); 
    return {"ok": True, "fee_burn_day": float(r.get(KEY_FEE_BURN_DAY) or 0)}
