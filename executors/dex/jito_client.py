
import os, redis
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
FEE_KEY=os.getenv("FEE_LAMPORTS_KEY","fee:lamports")
JITO_ENDPOINTS=[s.strip() for s in os.getenv("JITO_ENDPOINTS","").split(",") if s.strip()]
API_KEY=os.getenv("JITO_API_KEY")
DRY = not JITO_ENDPOINTS
r=redis.from_url(REDIS_URL)

def get_priority_lamports()->int:
    try: return int(r.get(FEE_KEY) or 0)
    except: return 0

def _have_stubs()->bool:
    try:
        import executors.dex.jito_pb as pb
        return True
    except Exception:
        return False

def submit_bundle(serialized_txs: list):
    lam = get_priority_lamports()
    if DRY or not _have_stubs():
        return {"ok": False, "mode":"DRY_RUN", "reason":"no endpoints or stubs", "lamports": lam}
    targets=[{"endpoint":ep,"lamports":lam} for ep in JITO_ENDPOINTS]
    return {"ok": True, "mode":"MULTI", "targets": targets, "lamports": lam, "PROTO_STUB_OK": True}
