
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
P95_MAX=int(os.getenv("CB_P95_MAX_MS","1800"))     # if relay p95 too high
MISS_SLOT_MAX=float(os.getenv("CB_MISS_SLOT_MAX","0.25"))
DD_HARD=float(os.getenv("CB_DD_HARD","-3000"))     # hard drawdown stop
BUDGET_TIP_MAX=int(os.getenv("CB_TIP_LAM_MAX","800000000"))  # per-day lamports
ARM_TIMEOUT=int(os.getenv("CB_ARM_TIMEOUT","600"))

def set_flag(k, v, ttl=300):
    r.setex(k, ttl, json.dumps({"ts": time.time(), "reason": v}))

def getf(k): 
    v=r.get(k)
    try: return json.loads(v) if v else None
    except: return None

def main():
    print("[circuit_breaker] running")
    while True:
        try:
            # SLO p95 check from computed curve (max of current hour across relays)
            import datetime as _dt
            hour=_dt.datetime.utcnow().hour
            curve=json.loads(r.get("solbot:relay_tipcurve") or b"{}")
            p95max=0
            for rel, bh in curve.items():
                try: p95max=max(p95max, float(bh[str(hour)]["p95"]))
                except Exception: pass

            # miss-slot from guard (optional key)
            miss=float(r.get("solbot:miss_slot_ratio") or 0.0)

            # drawdown from rolling pnl
            roll=float(r.get("solbot:rolling_pnl") or 0.0)

            # tip/day used
            import datetime as dt
            today=dt.date.today().isoformat()
            used_tip=int(r.get(f"solbot:jup:day:{today}:usdc_tip_lam") or 0)  # compatible placeholder
            # trip conditions
            if p95max>P95_MAX:
                set_flag("solbot:cb:tripped", f"p95>{P95_MAX}ms")
            elif miss>MISS_SLOT_MAX:
                set_flag("solbot:cb:tripped", f"miss_slot>{MISS_SLOT_MAX}")
            elif roll<DD_HARD:
                set_flag("solbot:cb:tripped", f"drawdown<{DD_HARD}")
            elif used_tip>BUDGET_TIP_MAX:
                set_flag("solbot:cb:tripped", "tip budget exceeded")
            else:
                # auto-clear by resetting armed requirement
                pass

            # If tripped ⇒ clear arming of Jupiter/Bridge to freeze hot ops
            if r.get("solbot:cb:tripped"):
                r.delete("solbot:jup:armed")
                r.delete("solbot:bridge:armed")
        except Exception:
            pass
        time.sleep(3)

if __name__=="__main__":
    main()
