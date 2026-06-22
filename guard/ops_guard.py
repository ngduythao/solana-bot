
import os, time, redis, requests

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
PAUSE_KEY=os.getenv("OPS_PAUSE_KEY","ops:pause")
SIZE_MULT_KEY=os.getenv("OPS_SIZE_MULT","trade:size_mult")
SLACK_WEBHOOK=os.getenv("SLACK_WEBHOOK","")

P95_THR=float(os.getenv("OPS_RPC_P95_THR","150"))
ACC_THR=float(os.getenv("OPS_ACCEPT_THR","0.6"))
LOSS_CAP=float(os.getenv("OPS_LOSS_CAP","-0.01"))
FEE_BURN_CAP=float(os.getenv("OPS_FEE_BURN_CAP","0.4"))  # 40% of gross/day

r=redis.from_url(REDIS_URL)

def alert(msg:str):
    if SLACK_WEBHOOK:
        try: requests.post(SLACK_WEBHOOK, json={"text":msg}, timeout=2)
        except: pass
    print("[ALERT]", msg)

def loop():
    size_mult=float(r.get(SIZE_MULT_KEY) or 1.0)
    while True:
        try:
            p95=float(r.get("rpc:best_p95") or 120.0)
            acc=float(r.get("bundle:accept_rate") or 0.8)
            pnl=float(r.get("hb:pnl:day") or 0.0)
            fee=float(r.get("hb:fee_burn:day") or 0.0)
            nav=float(r.get("hb:nav:usd") or 10000.0)
            loss_ratio = pnl/max(nav,1e-9)

            if p95>P95_THR and size_mult>0.5:
                size_mult=0.5; r.set(SIZE_MULT_KEY,size_mult); alert(f"RPC p95={p95}ms → size_mult=0.5")

            if acc<ACC_THR:
                r.set("fee:raise_hint","1")

            # Rule 2b: fee burn cap
            gross = pnl + fee
            if gross>0 and (fee/gross) > FEE_BURN_CAP:
                r.set("fee:raise_hint","1")
                r.set("ops:reduce_size","1")

            if loss_ratio<=LOSS_CAP:
                r.set(PAUSE_KEY,"1"); alert(f"Loss day {loss_ratio*100:.2f}% → PAUSE")

            r.hset("ops_guard:state","size_mult", size_mult)
            r.hset("ops_guard:state","paused", r.get(PAUSE_KEY) or b"0")
        except Exception as e:
            r.lpush("ops_guard:err", str(e))
        time.sleep(5)

if __name__=="__main__":
    loop()
