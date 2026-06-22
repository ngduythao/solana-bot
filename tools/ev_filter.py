
#!/usr/bin/env python3
import os, sys, json, math, time, redis

# Read quote JSON from stdin or path; output "ALLOW"/"DENY" and kelly_suggest_notional
# ENV thresholds
MIN_EDGE_BPS=float(os.getenv("EV_MIN_EDGE_BPS","6"))
MAX_SLIP_P95_BPS=float(os.getenv("EV_MAX_SLIP_P95_BPS","140"))
MAX_LAT_P95_MS=float(os.getenv("EV_MAX_LAT_P95_MS","140"))
FEE_BPS=float(os.getenv("EV_FEE_BPS","2"))
TIP_BPS=float(os.getenv("EV_TIP_BPS","1.5"))
VAR_SCALE=float(os.getenv("EV_VAR_SCALE","1.0"))
BASE_NOTIONAL=float(os.getenv("BASE_ORDER_USD","50"))
CAP_PER_TRADE=float(os.getenv("EV_CAP_PER_TRADE_USD","500"))
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")

r=redis.from_url(REDIS_URL)

def read_json():
    if len(sys.argv)>1 and sys.argv[1] != "-":
        return json.load(open(sys.argv[1],'r',encoding='utf-8'))
    try:
        return json.loads(sys.stdin.read())
    except Exception:
        return {}

def kelly(edge, var, base=BASE_NOTIONAL):
    # edge (in bps) -> convert to fraction; var approximate from slip/lat
    e=edge/10000.0
    v=max(1e-6, var*VAR_SCALE)
    f=max(0.0, min(1.0, e/v))  # simplified Kelly
    return min(CAP_PER_TRADE, max(base*0.25, base*f))

def main():
    data=read_json()
    # import context from Redis
    try:
        lat_p95=float(r.get("hsbot:notional:last_p95") or 0)
    except: lat_p95=0
    try:
        jito_p95=float(r.get("jito:rtt:best_p95") or 0)
    except: jito_p95=0
    # extract quote edge/slip
    edge_bps=float(data.get("expectedEdgeBps", 0))
    slip_p95=float(data.get("expectedSlipP95Bps", 0))
    # basic gates
    if edge_bps < MIN_EDGE_BPS: 
        print(json.dumps({"decision":"DENY","reason":"edge_low","edge_bps":edge_bps})); return 1
    if slip_p95 > MAX_SLIP_P95_BPS:
        print(json.dumps({"decision":"DENY","reason":"slip_p95_high","slip_p95":slip_p95})); return 1
    if max(lat_p95,jito_p95) > MAX_LAT_P95_MS and edge_bps < (MIN_EDGE_BPS*1.5):
        print(json.dumps({"decision":"DENY","reason":"latency_high","lat_ms":max(lat_p95,jito_p95)})); return 1
    # compute EV
    exp_profit_bps = edge_bps - FEE_BPS - TIP_BPS - (0.25*slip_p95)
    if exp_profit_bps <= 0:
        print(json.dumps({"decision":"DENY","reason":"ev_negative","ev_bps":exp_profit_bps})); return 1
    notional=kelly(exp_profit_bps, var=(slip_p95/10000.0 + 1e-4))
    print(json.dumps({"decision":"ALLOW","ev_bps":exp_profit_bps,"notional_usd":round(notional,2)}))
    return 0

if __name__=="__main__":
    sys.exit(main())
