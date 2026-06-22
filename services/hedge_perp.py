
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
ENABLE=os.getenv("HEDGE_ENABLE","0")=="1"
MAX_HEDGE_USD=float(os.getenv("HEDGE_MAX_USD","0"))
def main():
    if not ENABLE: 
        print("[hedge_perp] disabled"); return
    print("[hedge_perp] running")
    while True:
        try:
            inv=json.loads(r.get("solbot:inventory") or b'{}')  # expected: {pair: base_units}
            # TODO: connect to Drift/Zeta using API keys when provided; place small futures positions to neutralize delta
            # Placeholder: emit target hedge notional
            target={k:min(MAX_HEDGE_USD, abs(v)*0.5) for k,v in inv.items()}
            r.setex("solbot:hedge:target", 20, json.dumps(target))
        except Exception: pass
        time.sleep(5)
if __name__=="__main__":
    main()
