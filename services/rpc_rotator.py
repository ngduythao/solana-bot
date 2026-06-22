
import os, time, json, redis
from services.common.secrets import load_system_env
from services.common.logging_json import get_logger

log = get_logger("rpc_rotator")
load_system_env()
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

# Provide list via env (comma-separated); keep current in redis key "rpc:primary"
RPC_CANDIDATES = [x.strip() for x in os.getenv("RPC_CANDIDATES","https://api.mainnet-beta.solana.com").split(",") if x.strip()]
KEY="rpc:primary"

def score_endpoint(url: str) -> float:
    # combine health & recent p95 (from slo/relay stats) if any
    import requests, time
    t0=time.time()
    try:
        res = requests.post(url, json={"jsonrpc":"2.0","id":1,"method":"getHealth"}, timeout=1.5)
        ok = (res.status_code==200)
    except Exception:
        ok = False
    dt = (time.time()-t0)*1000.0
    return (1000.0 - dt) if ok else -1e6

def main():
    cur = r.get(KEY); cur = cur.decode() if cur else RPC_CANDIDATES[0]
    r.set(KEY, cur)
    log.info(f"start with {cur}")
    while True:
        try:
            best = max(RPC_CANDIDATES, key=score_endpoint)
            if best != cur:
                r.set(KEY, best); cur=best
                log.info(f"rotate RPC_PRIMARY -> {best}")
        except Exception as e:
            log.error(f"rotator err: {e}")
        time.sleep(15)

if __name__=="__main__":
    main()
