
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
REGION=os.getenv("REGION","nj-us")
SOL_MIN=float(os.getenv("SOL_GAS_MIN","0.5"))
SOL_TARGET=float(os.getenv("SOL_GAS_TARGET","1.5"))
SOL_MAX=float(os.getenv("SOL_GAS_MAX","2.0"))

def get_balances():
    try:
        bal=json.loads(r.get("solbot:balances") or b"{}")
        return bal.get(REGION,{})
    except Exception:
        return {}

def plan_swap(kind, amount_sol):
    # kind: topup (USDC->SOL) or bleed (SOL->USDC)
    p={"ts":time.time(),"region":REGION,"kind":kind,"amount_sol":round(float(amount_sol),6)}
    r.setex("solbot:gas_topup:plan", 30, json.dumps(p))

def forecast_need():
    # crude forecast from last N results: if send rate high, keep closer to SOL_MAX
    N=60; sends=0
    for i in range(N):
        it=r.lindex("solbot:fast_res", i)
        if it: sends+=1
    # map sends to buffer
    if sends>40: return SOL_MAX
    if sends>20: return (SOL_TARGET+SOL_MAX)/2
    return SOL_TARGET

def main():
    print("[gas_keeper] running for", REGION)
    while True:
        try:
            b=get_balances()
            sol=float(b.get("SOL",0))
            target=forecast_need()
            if sol < SOL_MIN:
                plan_swap("topup", target - sol)
            elif sol > SOL_MAX:
                plan_swap("bleed", sol - SOL_TARGET)
            r.setex("solbot:gas_status", 20, json.dumps({"region":REGION,"sol":sol,"min":SOL_MIN,"target":target,"max":SOL_MAX}))
        except Exception:
            pass
        time.sleep(5)

if __name__=="__main__":
    main()
