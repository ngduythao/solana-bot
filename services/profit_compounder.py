
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
REGION=os.getenv("REGION","nj-us")
STEP=float(os.getenv("COMPOUND_STEP","0.10"))           # move up to 10% of measured profits per step
MAX_HOT_RATIO=float(os.getenv("COMPOUND_MAX_HOT","0.45")) # cap hot share of USDC to 45% when compounding
DD_SOFT=float(os.getenv("COMPOUND_DD_SOFT","-500"))      # pause compound if rolling PnL < -500 USDC
DD_HARD=float(os.getenv("COMPOUND_DD_HARD","-2000"))     # force decompound if deep drawdown

def get_float(k, d=0.0):
    try:
        v=r.get(k)
        return float(v) if v else d
    except Exception:
        return d

def main():
    print("[compounder] running")
    last=0.0
    while True:
        try:
            # Read treasury split
            tre = json.loads(r.get("solbot:treasury:status") or b"{}")
            usdc=float(tre.get("usdc",0.0)); hot=float(tre.get("hot",0.0)); vault=float(tre.get("vault",0.0))
            if usdc<=0: time.sleep(5); continue

            # Rolling PnL from attrib
            attrib = json.loads(r.get("solbot:pnl_attrib") or b"{}").get("total", {})
            pnl = float(attrib.get("ev", 0.0))

            # Health signals: EV & SLO
            ev = json.loads(r.get("solbot:ev_pred") or b"{}").get("p_win", 0.5)
            slo = json.loads(r.get("solbot:slo") or b"{}")
            p95=float(slo.get("p95_ms", 0)); acc=float(slo.get("accept", 0.6))

            # Kelly-lite fraction: f ~ (2p-1)+ bonuses, clamped [0..0.15]
            f = max(0.0, min(0.15, (2*ev-1.0) + (0.05 if acc>0.7 else 0) - (0.05 if p95>1200 else 0)))
            # Profit since last step
            prof = max(0.0, pnl - last) if pnl>last else 0.0
            move = prof * min(STEP, f)  # compound a fraction of new profits

            # Guardrails
            # Soft drawdown: pause
            rolling = float(get_float("solbot:rolling_pnl", pnl))
            if rolling < DD_SOFT: move = 0.0
            # Hard drawdown: decompound (move hot -> vault)
            decomp = 0.0
            if rolling < DD_HARD:
                decomp = min(hot*0.10, hot)  # move 10% hot back to vault

            # Cap hot after compounding
            target_hot = min(usdc*MAX_HOT_RATIO, hot + move)
            if target_hot < hot:  # means we are at cap; no move
                move = 0.0

            # Emit plan (no signing)
            plan={"ts":time.time(),"region":REGION,"compound_move_usdc":round(move,2),"decompound_usdc":round(decomp,2),"kelly_like":round(f,4),"signals":{"p_win":ev,"p95":p95,"accept":acc}}
            r.setex("solbot:compound:plan", 60, json.dumps(plan))

            # Store last pnl for delta compounding
            last = pnl
            time.sleep(5)
        except Exception:
            time.sleep(3)

if __name__=="__main__":
    main()
