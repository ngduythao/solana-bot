
import os, time, json, math
import redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
PF_MIN = float(os.getenv("PF_MIN_MULT","0.5"))
PF_MAX = float(os.getenv("PF_MAX_MULT","5.0"))
PF_MULT = float(os.getenv("PF_INIT_MULT","1.0"))
DECAY = float(os.getenv("PF_TUNER_DECAY","0.9"))
BURN_CAP = float(os.getenv("FEE_BURN_CAP_PCT","0.4"))  # of gross pnl

def get_stats():
    # read rolling pnl & fee burn from Redis keys (updated by executor/orchestrator)
    gross = float(r.get("hsbot:stats:gross_pnl") or 0.0)
    burn = float(r.get("hsbot:stats:fee_burn") or 0.0)
    hit = float(r.get("hsbot:stats:hit") or 1.0)
    miss = float(r.get("hsbot:stats:miss") or 1.0)
    return gross, burn, hit, miss

def bandit_step(pf):
    gross, burn, hit, miss = get_stats()
    acceptance = hit / max(1.0, hit+miss)
    # utility = pnl_after_burn * acceptance (simplified)
    pnl_eff = max(0.0, gross - burn)
    util = pnl_eff * acceptance
    # adjust pf multiplicatively toward better acceptance, penalize burn
    tilt = (acceptance - 0.5) - 0.5*min(1.0, burn/max(1.0, gross))  # rough heuristic
    pf *= (1.0 + 0.2*tilt)
    return max(PF_MIN, min(PF_MAX, pf))

def main():
    global PF_MULT
    while True:
        mode = (os.getenv("PF_TUNER","bandit") or "off").lower()
        if mode == "off":
            time.sleep(2); continue
        PF_MULT = bandit_step(PF_MULT)
        r.set("hsbot:cfg:pf_mult", PF_MULT)
        # enforce fee-burn cap
        gross, burn, *_ = get_stats()
        if gross > 0 and burn/gross > BURN_CAP:
            # lower pf to minimum to protect pnl
            PF_MULT = max(PF_MIN, PF_MULT*0.5)
            r.set("hsbot:cfg:pf_mult", PF_MULT)
            r.publish("hsbot:alerts", json.dumps({"type":"fee_burn_cap", "pf_mult": PF_MULT, "gross":gross,"burn":burn}))
        time.sleep(5)

if __name__=="__main__":
    print("[fee_tuner] running")
    main()
