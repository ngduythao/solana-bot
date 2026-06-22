
import os, json, time, random, redis, yaml
from pathlib import Path
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
CFG_PATH=os.getenv("STRATEGY_CFG", str(Path(__file__).resolve().parent.parent/'strategy/strategy.yaml'))

def load_cfg():
    try:
        return yaml.safe_load(open(CFG_PATH)) or {}
    except Exception:
        return {}

def lane_ok(cfg):
    # read per-relay stats and form a best subset
    rels=[]
    for k in r.scan_iter(match="jito:relay_stats:*"):
        h=r.hgetall(k)
        try:
            cnt=int(h.get(b'count',b'0') or 0); suc=int(h.get(b'success',b'0') or 0)
            p50=float(h.get(b'p50_ms',b'0') or 0); p95=float(h.get(b'p95_ms',b'0') or 0)
            acc=(suc/cnt) if cnt>0 else 0.0
            rels.append({"key":k.decode(),"acc":acc,"p95":p95,"p50":p50})
        except: pass
    rels.sort(key=lambda x: (-x["acc"], x["p95"]))
    return rels

def route_shuffle(chunks):
    random.shuffle(chunks); return chunks

def apply_jitter(ms_rng):
    lo, hi = ms_rng
    time.sleep(random.uniform(lo/1000.0, hi/1000.0))

def main():
    print("[stealth_exec] running")
    while True:
        try:
            cfg=load_cfg()
            plan_raw=r.get("solbot:bundle_plan:next")
            if not plan_raw: time.sleep(0.01); continue
            plan=json.loads(plan_raw)
            pair=plan.get("pair","")
            pset=cfg.get("pairs",{}).get(pair,{})
            if not pset.get("enabled",False):
                r.lpush("solbot:dropped:pair", json.dumps({"ts":time.time(),"pair":pair,"reason":"disabled"}))
                r.delete("solbot:bundle_plan:next"); continue

            # AI EV gate
            ev=json.loads(r.get("solbot:ev_pred") or b'{}').get("p_win",0.5)
            if ev < float(pset.get("ev_min",0.6)):
                r.lpush("solbot:dropped:ev", json.dumps({"ts":time.time(),"pair":pair,"p_win":ev}))
                r.delete("solbot:bundle_plan:next"); continue

            # Lane health
            sl=cfg.get("stealth",{}); rels=lane_ok(cfg)
            good=[x for x in rels if x["acc"]>=sl.get("min_accept",0.5) and x["p95"]<=sl.get("max_p95_ms",1400)]
            k=int(sl.get("relay_subset",2)) or 1
            chosen=good[:k] if len(good)>=k else rels[:k]
            if not chosen:
                r.lpush("solbot:dropped:lane", json.dumps({"ts":time.time(),"pair":pair,"reason":"no_good_relay"}))
                r.delete("solbot:bundle_plan:next"); continue

            # Size & surprise-burst (capped)
            alloc=json.loads(r.get("solbot:alloc:size_q0") or b'{}')
            size= int(alloc.get(pair, 0) or 0)
            size = min(size, int(pset.get("max_q0", size or 500000)))
            sb=cfg.get("surprise_burst",{})
            if sb.get("enable",True) and ev>=float(sb.get("ev_gate",0.72)):
                size = min(int(size*float(sb.get("boost_mult",1.35))), int(pset.get("max_q0", size)))
            plan["size_q0"] = size

            # Shadow mode
            if cfg.get("shadow_mode",{}).get("enable",False):
                plan["shadow"]=True

            # Stealth transforms
            if sl.get("route_shuffle",True):
                plan["routes"] = route_shuffle(plan.get("routes",[]))
            plan["private_bundle_only"]= sl.get("private_bundle_only",True)
            plan["split_parts"]= random.randint(int(sl.get("split_parts",[2,4])[0]), int(sl.get("split_parts",[2,4])[1]))

            # Attach relay candidates in plan (executor chooses exact relay per chunk)
            plan["relay_candidates"] = [x["key"] for x in chosen]

            # Apply jitter and publish transformed plan
            apply_jitter(sl.get("jitter_ms",[3,18]))
            r.setex("solbot:bundle_plan:stealth", 10, json.dumps(plan))
            r.delete("solbot:bundle_plan:next")
        except Exception as e:
            time.sleep(0.02)
            continue

if __name__=="__main__":
    main()
