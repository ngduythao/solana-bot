
import os, redis
from fastapi import FastAPI, Response
from dotenv import load_dotenv

load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

app = FastAPI(title="Solana Bot Metrics Exporter")

def safe_float(x, d=0.0):
    try:
        if x is None:
            return d
        if isinstance(x, bytes):
            x = x.decode('utf-8')
        return float(x)
    except Exception:
        return d

@app.get("/metrics")
def metrics():
    lines=[]

    # Fee burn ratio
    fee = safe_float(r.get("hb:fee_burn:day"))
    pnl = safe_float(r.get("hb:pnl:day"))
    ratio = (fee / pnl) if pnl > 0 else 0.0
    lines += [
        "# HELP fee_burn_ratio Fee burn to gross PnL ratio (0-1)",
        "# TYPE fee_burn_ratio gauge",
        f"fee_burn_ratio {ratio}",
    ]

    # RPC p95
    p95 = safe_float(r.get("rpc:best_p95"))
    lines += [
        "# HELP rpc_latency_p95 RPC benchmark best p95 (ms)",
        "# TYPE rpc_latency_p95 gauge",
        f"rpc_latency_p95 {p95}",
    ]

    # Bundle acceptance rate
    acc = safe_float(r.get("bundle:accept_rate"))
    lines += [
        "# HELP bundle_accept_rate Bundle acceptance rate (0-1)",
        "# TYPE bundle_accept_rate gauge",
        f"bundle_accept_rate {acc}",
    ]

    # Sim-gate
    passed = safe_float(r.hget("sim_gate:stats","passed"))
    skipped = safe_float(r.hget("sim_gate:stats","skipped"))
    error = safe_float(r.hget("sim_gate:stats","error"))
    panic = safe_float(r.hget("sim_gate:stats","panic"))
    lines += [
        "# HELP sim_gate_passed Number of routes passed by simulator gate",
        "# TYPE sim_gate_passed counter",
        f"sim_gate_passed {passed}",
        "# HELP sim_gate_skipped Number of routes skipped by simulator gate",
        "# TYPE sim_gate_skipped counter",
        f"sim_gate_skipped {skipped}",
        "# HELP sim_gate_error Number of simulator errors",
        "# TYPE sim_gate_error counter",
        f"sim_gate_error {error}",
        "# HELP sim_gate_panic Number of unexpected exceptions in sim-gate",
        "# TYPE sim_gate_panic counter",
        f"sim_gate_panic {panic}",
    ]

    # Ops guard
    paused = safe_float(r.hget("ops_guard:state","paused"))
    size_mult = safe_float(r.hget("ops_guard:state","size_mult"), 1.0)
    lines += [
        "# HELP ops_guard_paused Pause flag (0/1)",
        "# TYPE ops_guard_paused gauge",
        f"ops_guard_paused {paused}",
        "# HELP trade_size_mult Trade sizing multiplier",
        "# TYPE trade_size_mult gauge",
        f"trade_size_mult {size_mult}",
    ]

    # PnL & inventory
    pnl_day = safe_float(r.get("hb:pnl:day"))
    skew_pct = safe_float(r.get("hb:inventory_skew_pct"))
    lines += [
        "# HELP hb_pnl_day Daily net PnL in USD",
        "# TYPE hb_pnl_day gauge",
        f"hb_pnl_day {pnl_day}",
        "# HELP inventory_skew_pct Inventory skew percent",
        "# TYPE inventory_skew_pct gauge",
        f"inventory_skew_pct {skew_pct}",
    ]

    text = "\n".join(lines) + "\n"
    return Response(content=text, media_type="text/plain")
