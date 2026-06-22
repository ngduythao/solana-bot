
# Fee bandit: tune fee:lamports by hour-of-day and congestion, under fee burn cap.
import os, time, math, redis, json, random

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
LAM_KEY=os.getenv("FEE_LAMPORTS_KEY","fee:lamports")
BASE=int(os.getenv("FEE_BASE_LAMPORTS","8000"))
MIN_LAM=int(os.getenv("FEE_MIN_LAMPORTS","2000"))
MAX_LAM=int(os.getenv("FEE_MAX_LAMPORTS","40000"))
STEP=int(os.getenv("FEE_STEP_LAMPORTS","1000"))
FEE_BURN_MAX=float(os.getenv("FEE_BURN_MAX_RATIO","0.40"))
BUDGET_KEY=os.getenv("FEE_BURN_DAY_KEY","hb:fee_burn:day")
PNL_KEY=os.getenv("PNL_GROSS_KEY","hb:pnl:day")
ACCEPT_KEY=os.getenv("BUNDLE_ACCEPT_KEY","bundle:accept_rate")
REJECT_KEY=os.getenv("BUNDLE_REJECT_KEY","bundle:reject_rate")
CONG_KEY=os.getenv("NET_CONGESTION_KEY","net:congestion")
SIZE_MULT_KEY=os.getenv("SIZE_MULT_KEY","trade:size_mult")

r=redis.from_url(REDIS_URL)

def getf(k,default=0.0):
    try: return float(r.get(k) or default)
    except: return default

def main():
    # init lamports if not set
    if r.get(LAM_KEY) is None: r.set(LAM_KEY, str(BASE))
    while True:
        lam = int(float(r.get(LAM_KEY) or BASE))
        fee = getf(BUDGET_KEY,0.0); pnl = getf(PNL_KEY,0.0)
        acc = getf(ACCEPT_KEY,0.0); rej = getf(REJECT_KEY,0.0)
        cong= getf(CONG_KEY,0.0)
        ratio = fee/max(pnl,1e-9) if pnl>0 else 0.0

        # budget guard – if burning too much, reduce size or lamports
        if pnl>0 and ratio > FEE_BURN_MAX:
            # prefer reducing size multiplier; if already small, cut lamports
            sm = getf(SIZE_MULT_KEY,1.0)
            if sm>0.3:
                r.set(SIZE_MULT_KEY, str(round(sm*0.7,2)))
            lam = max(MIN_LAM, lam-STEP*2)

        # Bandit-ish adjust: if accept low or reject high → bump lamports; else decay
        if acc and acc < 0.6:
            lam = min(MAX_LAM, lam + STEP)
        elif rej and rej > 0.2:
            lam = min(MAX_LAM, lam + STEP)
        else:
            # mild decay by congestion
            decay = STEP if cong<0.5 else int(STEP*0.5)
            lam = max(MIN_LAM, lam - decay)

        r.set(LAM_KEY, str(lam))
        # sleep ~20s between adjustments
        time.sleep(int(os.getenv("FEE_BANDIT_INTERVAL_SEC","20")))

if __name__=="__main__":
    main()
