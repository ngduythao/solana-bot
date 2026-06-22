
import os, csv, time, math, threading
from datetime import datetime, timezone

METRICS_PATH = os.getenv("METRICS_PATH", "metrics.csv")
_lock = threading.Lock()

def _utcnow_iso():
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

def write_metric(kind, **kw):
    row = {"ts": _utcnow_iso(), "kind": kind}
    row.update(kw)
    with _lock:
        exists = os.path.exists(METRICS_PATH)
        with open(METRICS_PATH, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sorted(row.keys()))
            if not exists:
                w.writeheader()
            w.writerow(row)

def pnl_per_second(pnl_usd, latency_ms):
    try:
        s = max(1e-3, float(latency_ms)/1000.0)
        return pnl_usd / s
    except Exception:
        return 0.0
