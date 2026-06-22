
import os, json, time, redis
from typing import List, Dict

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

JITO_MODE=os.getenv("JITO_MODE","grpc")
JITO_ENDPOINTS=[s.strip() for s in os.getenv("JITO_ENDPOINTS","").split(",") if s.strip()]
JITO_AUTH_TOKEN=os.getenv("JITO_AUTH_TOKEN")
FEE_KEY=os.getenv("FEE_LAMPORTS_KEY","fee:lamports")

def get_priority_lamports()->int:
    try: return int(r.get(FEE_KEY) or 0)
    except: return 0

def congestion_hint()->float:
    p95 = float(r.get("rpc:best_p95") or 150.0)
    hint = max(0.0, min(1.0, (p95-60)/140))
    return hint

def bandit_fee(base:int)->int:
    cong = congestion_hint()
    acc = float(r.get("bundle:accept_rate") or 0.7)
    scale = 1.0 + cong*0.8 + (0.8-acc)*0.5
    return int(max(0, base*scale))

def submit_bundle(serialized_txs: List[str])->Dict:
    fee = bandit_fee(get_priority_lamports())
    if not JITO_ENDPOINTS or JITO_MODE!="grpc":
        return {"ok": False, "mode":"DRY_RUN", "reason":"no endpoints", "lamports": fee}
    ts=int(time.time())
    targets=[{"relay":ep,"fee":fee} for ep in JITO_ENDPOINTS]
    r.lpush("jito:intents", json.dumps({"ts":ts,"targets":targets,"n":len(serialized_txs)}))
    for ep in JITO_ENDPOINTS:
        r.hincrby(f"bundle:sent", ep, 1)
    return {"ok": True, "mode":"MULTI_RELAY_STUB", "targets": targets, "lamports": fee}
