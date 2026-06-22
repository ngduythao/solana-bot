
import os, time, redis, yaml

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

FLAG_RUN=os.getenv("CONTROL_FLAG_KEY","solbot:enabled")
SIZE_MULT_KEY=os.getenv("SIZE_MULT_KEY","trade:size_mult")
FAIL_RATE_KEY=os.getenv("FAIL_RATE_KEY","hb:fail_rate")
REJECT_RATE_KEY=os.getenv("REJECT_RATE_KEY","bundle:reject_rate")
PNL_KEY="hb:pnl:day"
FEE_KEY="hb:fee_burn:day"

CFG_PATH=os.getenv("CONFIG_PATH","config.yaml")
cfg=yaml.safe_load(open(CFG_PATH,'r'))

NAV=float(cfg.get("portfolio",{}).get("nav_usd",10000))
DAILY_WARN = float(os.getenv("DAILY_WARN_BPS","50"))     # -0.5% NAV warn
DAILY_STOP = float(os.getenv("DAILY_STOP_BPS","100"))    # -1.0% NAV stop
FEE_BURN_CAP=float(os.getenv("FEE_BURN_CAP_PCT","0.4"))  # 40% of gross pnl
FAIL_CAP=float(os.getenv("FAIL_CAP","0.15"))             # 15%
REJECT_CAP=float(os.getenv("REJECT_CAP","0.20"))         # 20%

def getf(key, default=0.0):
    try: return float(r.get(key) or default)
    except: return default

def pause_bot():
    r.set(FLAG_RUN, 0)

def resume_bot():
    r.set(FLAG_RUN, 1)

def set_size_mult(v: float):
    r.set(SIZE_MULT_KEY, max(0.1, min(v, 1.0)))

if __name__=="__main__":
    print("[ALERT] watcher start")
    set_size_mult(1.0)
    while True:
        pnl = getf(PNL_KEY, 0.0)            # USD
        fee = getf(FEE_KEY, 0.0)            # USD
        fail = getf(FAIL_RATE_KEY, 0.0)     # 0..1
        rej  = getf(REJECT_RATE_KEY, 0.0)   # 0..1

        dd_bps = 0.0
        if NAV>0: dd_bps = max(0.0, -pnl/NAV)*1e4

        # Daily loss guard
        if dd_bps >= DAILY_STOP:
            pause_bot()
            print("[ALERT] Daily stop triggered. Paused bot.")
        elif dd_bps >= DAILY_WARN:
            set_size_mult(0.5)
            print("[ALERT] Drawdown warn. Reduced size to 50%.")

        # Fee burn cap (needs gross pnl published somewhere; we approximate by comparing fee vs |pnl| )
        if abs(pnl)>0 and fee/abs(pnl) > FEE_BURN_CAP:
            set_size_mult(0.5)
            print("[ALERT] Fee burn high. Reduced size.")

        # Fail/Reject rate guards
        if fail > FAIL_CAP or rej > REJECT_CAP:
            set_size_mult(0.5)
            print("[ALERT] Fail/reject high. Reduced size.")

        time.sleep(5)


FEE_BURN_MAX_RATIO = float(os.getenv("FEE_BURN_MAX_RATIO","0.40"))
FEE_BURN_ACTION = os.getenv("FEE_BURN_ACTION","reduce").lower()
FEE_BURN_REDUCE_MULT = float(os.getenv("FEE_BURN_REDUCE_MULT","0.5"))
FEE_BURN_ALERT_KEY = os.getenv("FEE_BURN_ALERT_KEY","alert:fee_burn")
PNL_GROSS_KEY = os.getenv("PNL_GROSS_KEY","hb:pnl:day")  # fallback gross PnL key
FEE_BURN_DAY_KEY = os.getenv("FEE_BURN_DAY_KEY","hb:fee_burn:day")
SIZE_MULT_KEY = os.getenv("SIZE_MULT_KEY","trade:size_mult")
PAUSE_KEY = os.getenv("PAUSE_KEY","solbot:enabled")

def _guard_fee_burn(r):
    try:
        fee = float(r.get(FEE_BURN_DAY_KEY) or 0.0)
        pnl = float(r.get(PNL_GROSS_KEY) or 0.0)
        if pnl <= 0:
            return
        ratio = fee / max(1e-9, pnl)
        if ratio >= FEE_BURN_MAX_RATIO:
            if FEE_BURN_ACTION == "pause":
                r.set(PAUSE_KEY, "0")
                r.set(FEE_BURN_ALERT_KEY, json.dumps({"ts": time.time(), "ratio": ratio, "action": "pause"}))
            else:
                # reduce
                r.set(SIZE_MULT_KEY, str(FEE_BURN_REDUCE_MULT))
                r.set(FEE_BURN_ALERT_KEY, json.dumps({"ts": time.time(), "ratio": ratio, "action": "reduce", "new_mult": FEE_BURN_REDUCE_MULT}))
    except Exception as e:
        try:
            r.set(FEE_BURN_ALERT_KEY, json.dumps({"ts": time.time(), "err": str(e)}))
        except Exception:
            pass

# Hook guard in watcher loop if available
