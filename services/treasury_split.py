
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
REGION=os.getenv("REGION","nj-us")
VAULT_RATIO=float(os.getenv("VAULT_RATIO","0.3"))  # fraction of total USDC used as HOT capital (0.3 => 30% hot)
MIN_HOT_USDC=float(os.getenv("MIN_HOT_USDC","500"))

def main():
    print("[treasury_split] running", REGION)
    while True:
        try:
            bal=json.loads(r.get("solbot:balances") or b"{}")
            reg=bal.get(REGION,{})
            usdc=float(reg.get("USDC",0.0))
            hot=max(MIN_HOT_USDC, usdc*VAULT_RATIO)
            vault=max(0.0, usdc - hot)
            r.mset({
                "solbot:treasury:hot_usdc": str(hot),
                "solbot:treasury:vault_usdc": str(vault),
            })
            # If a pair-wise alloc exists, scale it down/up to fit within hot budget (best-effort)
            alloc=json.loads(r.get("solbot:alloc:size_q0") or b"{}")
            if alloc:
                # assume 1 q0 ~= 1 USDC notional proxy (placeholder)
                total_q0=sum(alloc.values()) or 1.0
                scale=min(1.0, hot/total_q0)
                if scale<0.999:
                    for k in list(alloc.keys()):
                        alloc[k]=int(alloc[k]*scale)
                    r.setex("solbot:alloc:size_q0", 20, json.dumps(alloc))
            r.setex("solbot:treasury:status", 30, json.dumps({"region":REGION,"usdc":usdc,"hot":hot,"vault":vault,"ratio":VAULT_RATIO}))
        except Exception:
            pass
        time.sleep(6)

if __name__=="__main__":
    main()
