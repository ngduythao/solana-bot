
import os, json, time, redis, math
from orchestrator.sim_client import simulate_clmm, simulate_dlmm, SimError

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
EVCFG_THR=float(os.getenv("SIM_GATE_EV_THR_BPS","3"))
MAX_HOPS=int(os.getenv("SIM_GATE_MAX_HOPS","3"))
SRC_Q=os.getenv("SIM_GATE_SRC","hsbot:opps")
DST_Q=os.getenv("SIM_GATE_DST","hsbot:exec")

r=redis.from_url(REDIS_URL)

def ev_from_route(route)->float:
    # fallback EV if precomputed
    if "ev_bps" in route: return float(route["ev_bps"])
    return 0.0

def normalize_leg(leg):
    # expected leg model fields from preselector/executor
    return {
        "type": leg.get("type","CLMM"),
        "dex": leg.get("dex","Unknown"),
        "meta": leg.get("meta",{})
    }

def resim_route(route)->dict:
    # route example: {"legs":[{type:"CLMM"|"DLMM", meta:{ state or bins, amount_in, is_a_in/is_base_in }}], "pair":"SOL/USDC", ...}
    legs = route.get("legs") or []
    if not legs or len(legs)>MAX_HOPS:
        raise SimError("invalid legs")
    ev_bps = 0.0
    out_multiplier = 1.0
    for leg in legs:
        L = normalize_leg(leg)
        m = L["meta"]
        if L["type"].upper()=="CLMM":
            st = m["state"]
            res = simulate_clmm(st, m["amount_in"], m.get("is_token_a_in", True), m.get("limit_tick"))
            m["sim"]=res
            # approximate edge per leg from amount_out/amount_in
            ain=max(res.get("amount_in_consumed",0),1)
            aout=max(res.get("amount_out",0),1)
            out_multiplier *= (aout/ain)
        else:
            bins = m["bins"]
            res = simulate_dlmm(bins, m["amount_in"], m.get("is_base_in", True))
            m["sim"]=res
            ain=max(m["amount_in"],1e-9)
            aout=max(res.get("amount_out",0.0),1e-9)
            out_multiplier *= (aout/ain)
    ev_bps = (out_multiplier - 1.0) * 1e4
    route["ev_bps_sim"]=round(ev_bps,3)
    return route

def main():
    while True:
        item = r.lpop(SRC_Q)
        if not item:
            time.sleep(0.05); continue
        try:
            opp = json.loads(item)
        except Exception:
            continue
        try:
            opp = resim_route(opp)
            if opp.get("ev_bps_sim",0.0) >= EVCFG_THR:
                r.lpush(DST_Q, json.dumps(opp))
                r.hincrby("sim_gate:stats","passed",1)
            else:
                r.hincrby("sim_gate:stats","skipped",1)
        except SimError as e:
            r.hincrby("sim_gate:stats","error",1)
            r.lpush("sim_gate:errors", json.dumps({"err":str(e),"opp":opp}) )
        except Exception as e:
            r.hincrby("sim_gate:stats","panic",1)
            r.lpush("sim_gate:errors", json.dumps({"err":str(e),"opp":opp}) )

if __name__=="__main__":
    main()
