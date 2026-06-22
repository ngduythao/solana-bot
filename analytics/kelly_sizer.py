
#!/usr/bin/env python3
# Periodically compute Kelly-based caps using recent WR/volatility and write overrides to Redis.
import os, csv, time, math, redis
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
METRICS_PATH=os.getenv("METRICS_PATH","metrics.csv")
TTL=int(os.getenv("KELLY_TTL_SEC","300"))
W=int(os.getenv("KELLY_WINDOW_SEC","3600"))
BASE=float(os.getenv("BASE_ORDER_USD","50"))
CAP=float(os.getenv("KELLY_CAP_USD","1500"))
MINTS=[s.strip().upper() for s in os.getenv("KELLY_MINTS","SOL,JUP,WIF,BONK").split(",")]

def stdev(v):
    if len(v)<2: return 0.0
    m=sum(v)/len(v)
    var=sum((x-m)**2 for x in v)/ (len(v)-1)
    return var**0.5

def run():
    r=redis.from_url(REDIS_URL)
    while True:
        try:
            with open(METRICS_PATH,'r',encoding='utf-8') as f:
                rows=list(csv.DictReader(f))
        except: rows=[]
        now=time.time()
        pnl=[float(a.get("pnl_usd") or 0) for a in rows if now-float(a.get("ts",now))<=W]
        wr=sum(1 for v in pnl if v>0)/len(pnl) if pnl else 0.5
        vol=stdev(pnl) if pnl else 1.0
        # simplified edge estimate
        edge=max(-0.5, min(0.5, (wr-0.5)*2.0))
        f=max(0.1, min(1.0, edge/(vol/100.0 + 1e-6)))
        per_trade=max(BASE*0.25, min(CAP, BASE*f))
        r.setex("hsbot:kelly:notional_usd", TTL, f"{per_trade:.2f}")
        for m in MINTS:
            r.setex(f"hsbot:hedge:cfg:min_notional_usd:{m}", TTL, f"{per_trade:.2f}")
        time.sleep(30)

if __name__=="__main__":
    run()
