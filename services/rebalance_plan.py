
import os, time, json, redis, random
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
THRESH=float(os.getenv("REBAL_THRESH","0.6"))
REGIONS=os.getenv("REGIONS","nj-us,sg-apac").split(",")
def main():
    print("[rebalance_plan] running, regions=",REGIONS)
    while True:
        try:
            bals=json.loads(r.get("solbot:balances") or b'{}')  # expect {region: {USDC:val,SOL:val}}
            tot_usdc=sum((bals.get(reg,{}).get("USDC",0) for reg in REGIONS))
            plan={}
            for reg in REGIONS:
                bal=bals.get(reg,{}).get("USDC",0)
                share=(bal/max(1,tot_usdc))
                if share>THRESH:
                    plan[reg]={"action":"rebalance_out","usdc":int(bal-tot_usdc/len(REGIONS))}
            if plan: r.setex("solbot:rebalance:plan",30,json.dumps(plan))
        except Exception: pass
        time.sleep(10)
if __name__=="__main__": main()
