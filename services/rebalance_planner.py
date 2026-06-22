
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
THRESH=float(os.getenv("REBALANCE_THRESH_PCT","0.60"))

def main():
    print("[rebalance_planner] running")
    while True:
        try:
            bal=json.loads(r.get("solbot:balances") or b'{}')  # expect {'nj-us':{'USDC':..., 'SOL':...}, 'sg-apac':{...}}
            if not bal:
                time.sleep(5); continue
            plan={"ts": time.time(), "actions":[]}
            for asset in ("USDC","SOL"):
                total=sum([v.get(asset,0) for v in bal.values()])
                if total<=0: continue
                for region,vals in bal.items():
                    frac = vals.get(asset,0)/total
                    if frac>THRESH:
                        # move excess to others evenly (placeholder amounts)
                        move = int(vals.get(asset,0) - total*(1-THRESH))
                        if move>0:
                            targets=[r for r in bal.keys() if r!=region]
                            if targets:
                                each=move//len(targets)
                                for t in targets:
                                    plan["actions"].append({"asset":asset,"from":region,"to":t,"amount":each})
            r.setex("solbot:rebalance:plan", 30, json.dumps(plan))
        except Exception:
            pass
        time.sleep(10)

if __name__=="__main__":
    main()
