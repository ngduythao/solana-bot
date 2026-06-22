
import os, time, json, threading, httpx
import redis, yaml
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")

# Queues
Q_ARB = os.getenv("Q_ARB","hsbot:opps")
Q_BACKRUN = os.getenv("Q_BACKRUN","hsbot:backrun")
Q_FUND = os.getenv("Q_FUND","hb:opps:funding")
Q_LIQ = os.getenv("Q_LIQ","hb:opps:liq")

# Dispatch queues
DQ_DEX = os.getenv("DQ_DEX","hb:dispatch:dex")
DQ_CEX = os.getenv("DQ_CEX","hb:dispatch:cex")
DQ_HEDGE = os.getenv("DQ_HEDGE","hb:dispatch:hedge")

CONFIG_PATH = os.getenv("CONFIG_PATH","config.yaml")

r = redis.from_url(REDIS_URL)
cfg = yaml.safe_load(open(CONFIG_PATH,'r'))
SIZE_MULT_KEY=os.getenv('SIZE_MULT_KEY','trade:size_mult')
AIFEE_URL=os.getenv('AIFEE_URL','http://ai-fee:8092/tick')
PRIO_URL=os.getenv('PRIOFEE_URL','http://priority-fee:8093/tick')
CONG_KEY=os.getenv('NET_CONGESTION_KEY','net:congestion')
RUN_FLAG_KEY=os.getenv('CONTROL_FLAG_KEY','solbot:enabled')

# Basic risk & caps from config
risk = cfg.get("risk",{})
portfolio = cfg.get("portfolio",{})
evcfg = cfg.get("ev",{})
hybrid = cfg.get("hybrid",{})

MAX_NAV_BPS = float(risk.get("max_nav_per_trade_bps",50))
FIRE_THR_BPS = float(evcfg.get("fire_threshold_bps",3))

def nav_usd():
    # placeholder: pull from portfolio config; in production, query wallet/cex balances
    return float(portfolio.get("nav_usd",10000))

def cap_per_trade_usd():
    size_mult = 1.0
    try:
        v = r.get(SIZE_MULT_KEY)
        if v is not None:
            size_mult = max(0.1, min(float(v), 1.0))
    except Exception:
        pass
    return nav_usd() * (MAX_NAV_BPS/1e4) * size_mult

def good_ev(ev_bps):
    return ev_bps is not None and ev_bps >= FIRE_THR_BPS

def route_rank(op):
    # Simple rank: EV bps first, then notional / latency if available
    ev = float(op.get("ev_bps",0))
    size = float(op.get("size_usd",0))
    return (ev, size)

def dispatch(qname, msg):
    if (r.get(RUN_FLAG_KEY) or b'1') != b'1':
        return  # paused
    
    r.lpush(qname, json.dumps(msg))

def handle_arb(op):
    if not good_ev(op.get("ev_bps",0)): return
    op["type"] = "DEX_ARB"
    op["max_notional_usd"] = min(cap_per_trade_usd(), float(op.get("size_usd",0)))
    dispatch(DQ_DEX, op)

def handle_backrun(op):
    op["type"] = "DEX_BACKRUN"
    op["max_notional_usd"] = cap_per_trade_usd()
    dispatch(DQ_DEX, op)

def handle_funding(batch):
    if not hybrid.get("enable_funding", False): return
    cands = batch.get("candidates",[])
    if not cands: return
    # Choose highest |funding| symbol (placeholder policy)
    top = sorted(cands, key=lambda x: abs(x.get("funding_pct_8h",0)), reverse=True)[0]
    msg = {"type":"CEX_FUNDING","venue":top.get("ex"),"symbol":top.get("symbol"),
           "funding_pct_8h": top.get("funding_pct_8h"), "size_usd": cap_per_trade_usd()*0.5}
    dispatch(DQ_CEX, msg)

def handle_liq(op):
    if not hybrid.get("enable_liquidation", False): return
    # Placeholder: forward to hedge executor or DEX executor depending on opportunity shape
    msg = {"type":"DEX_LIQ","raw": op}
    dispatch(DQ_DEX, msg)

def pop_blocking(q):
    it = r.brpop(q, timeout=1)
    if not it: return None
    return json.loads(it[1])

def loop(q, handler):
    while True:
        try:
            msg = pop_blocking(q)
            if not msg: continue
            handler(msg)
        except Exception as e:
            print("[ORCH] error:", e)
            time.sleep(0.1)

if __name__=="__main__":
    print("[ORCH] start; caps per trade USD:", cap_per_trade_usd())
    threads = [
        threading.Thread(target=loop, args=(Q_ARB, handle_arb), daemon=True),
        threading.Thread(target=loop, args=(Q_BACKRUN, handle_backrun), daemon=True),
        threading.Thread(target=loop, args=(Q_FUND, handle_funding), daemon=True),
        threading.Thread(target=loop, args=(Q_LIQ, handle_liq), daemon=True),
    ]
    [t.start() for t in threads]
    while True:
        time.sleep(5)


def priofee_ticker():
    # lightweight periodic tick inside orchestrator to avoid relying solely on scheduler
    with httpx.Client(timeout=2.0) as client:
        while True:
            try:
                # Estimate congestion from accept-rate if available
                ar = float(r.get("bundle:accept_rate") or 0.75)
                cong = max(0.0, min(1.0, 1.0 - ar))
                r.set(CONG_KEY, cong)
                client.post(AIFEE_URL)
                client.post(PRIO_URL)
            except Exception as e:
                print("[ORCH] priofee tick err", e)
            time.sleep(5)
