
import os, csv, time, math
from collections import defaultdict, deque

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
METRICS_PATH = os.getenv("METRICS_PATH", "metrics.csv")
WINDOW_SEC = int(os.getenv("ROUTE_PENALTY_WINDOW_SEC", "1800"))   # 30m sliding
P95_SLIP_BPS = int(os.getenv("ROUTE_PENALTY_P95_SLIP_BPS", "120"))
LOSS_USD = float(os.getenv("ROUTE_PENALTY_RECENT_LOSS_USD", "50"))
TTL_SEC = int(os.getenv("ROUTE_PENALTY_TTL_SEC", "1800"))         # 30m
SLEEP_SEC = int(os.getenv("ROUTE_PENALTY_POLL_SEC", "10"))

r = redis.from_url(REDIS_URL)

def now(): return int(time.time())

def read_tail(path, limit=20000):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            rows = f.readlines()[-limit:]
        return rows
    except FileNotFoundError:
        return []

def parse_rows(lines):
    # Expected columns include: ts, route_label, slip_bps, pnl_usd
    # We make it robust to column order by header detection
    if not lines: return []
    reader = csv.DictReader(lines)
    out = []
    tnow = now()
    for row in reader:
        try:
            ts = int(float(row.get("ts", tnow)))
            if tnow - ts > WINDOW_SEC: continue
            route = row.get("route_label") or row.get("route") or "UNKNOWN"
            slip = float(row.get("slip_bps") or row.get("slippage_bps") or 0.0)
            pnl = float(row.get("pnl_usd") or row.get("pnl") or 0.0)
            out.append((ts, route.upper(), slip, pnl))
        except Exception:
            continue
    return out

def p95(nums):
    if not nums: return 0.0
    s = sorted(nums)
    k = int(math.ceil(0.95*len(s)))-1
    return float(s[max(0,min(k,len(s)-1))])

def main():
    while True:
        lines = read_tail(METRICS_PATH)
        data = parse_rows(lines)
        by_route = defaultdict(lambda: {"slips": [], "pnl": 0.0})
        for _, route, slip, pnl in data:
            by_route[route]["slips"].append(abs(slip))
            by_route[route]["pnl"] += pnl

        # clear previous mark (optional) -> not clearing; rely on TTL
        penalized = []
        for route, agg in by_route.items():
            p95_slip = p95(agg["slips"])
            recent_loss = -agg["pnl"] if agg["pnl"] < 0 else 0.0
            if p95_slip >= P95_SLIP_BPS or recent_loss >= LOSS_USD:
                key = f"hsbot:route:deny:{route}"
                r.set(key, f"p95_slip={p95_slip:.1f},recent_loss={recent_loss:.2f}", ex=TTL_SEC)
                penalized.append((route, p95_slip, recent_loss))

        # heartbeat
        r.set("hsbot:route:penalty:last_run", str(now()), ex=TTL_SEC)
        time.sleep(SLEEP_SEC)

if __name__ == "__main__":
    main()
