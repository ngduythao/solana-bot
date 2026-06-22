
"""Backtest/replay on saved slot snapshots.
Input directory structure:
snapshots/
  2025-01-01T10-00-00Z.json
  2025-01-01T10-01-00Z.json
Each JSON contains:
{ "pair":"SOL/USDC",
  "sqrt_price_x64": int,
  "liquidity": int,
  "fee_bps": int,
  "ticks": [ {"tick": int, "liquidity_net": int}, ... ],
  "dlmm": { "base_fee_bps": int, "bins": [ {"price_x64": int, "liq": int}, ... ] }
}
We simulate for a grid of sizes and tune per-hour:
- price_limit_bps
- T1_REQUOTE_BPS
- priority_fee multiplier
Output CSV: backtest_hourly.csv with columns hour, price_limit_bps, T1_REQUOTE_BPS, pf_mult, hit_rate, pnl_est
"""
import os, json, glob, math
import pandas as pd
from datetime import datetime
from simulator.clmm_exact import swap_x_to_y as clmm_swap
from simulator.dlmm_dynamic import walk_bins as dlmm_swap

def hour_key(ts_str):
    # derive hour UTC from filename
    ts = datetime.strptime(ts_str, "%Y-%m-%dT%H-%M-%SZ")
    return ts.strftime("%Y-%m-%d %H:00")

def simulate_snapshot(snap, size_list, params):
    results = []
    for size in size_list:
        # CLMM leg (proxy if ticks missing)
        out1, _, _ = clmm_swap(size, snap['sqrt_price_x64'], snap['liquidity'], snap['fee_bps'], snap.get('ticks',[]))
        # DLMM leg if present
        dl = snap.get('dlmm',{})
        out2, fill = (0,0.0)
        if dl and dl.get('bins'):
            out2, fill = dlmm_swap(out1, dl.get('bins',[]), dl.get('base_fee_bps',30))
        pnl = out2 - size  # crude pnl proxy
        hit = 1 if pnl>0 else 0
        results.append({"size":size, "pnl":pnl, "hit":hit})
    return results

def tune_hourly(snap_dir, sizes=(10_000, 25_000, 50_000), price_limit_grid=(10,20,30), requote_grid=(2,3,5), pf_mult_grid=(0.8,1.0,1.2)):
    rows=[]
    files = sorted(glob.glob(os.path.join(snap_dir, "*.json")))
    if not files: 
        print("No snapshots found."); 
        return pd.DataFrame()
    by_hour={}
    for f in files:
        base = os.path.basename(f).replace(".json","")
        hk = hour_key(base)
        by_hour.setdefault(hk, []).append(f)
    for hk, flist in by_hour.items():
        best=None
        for pl in price_limit_grid:
            for rq in requote_grid:
                for pf in pf_mult_grid:
                    pnl=0; hits=0; n=0
                    for fp in flist:
                        snap=json.load(open(fp))
                        rs = simulate_snapshot(snap, sizes, {"pl":pl,"rq":rq,"pf":pf})
                        for r in rs:
                            pnl += r["pnl"]; hits+=r["hit"]; n+=1
                    net = pnl - 0.0001*abs(pnl)  # tiny penalty
                    cand = (net, hits/max(1,n), pl, rq, pf)
                    if best is None or cand>best: best=cand
        if best:
            net, hit_rate, pl, rq, pf = best
            rows.append({"hour":hk, "price_limit_bps":pl, "T1_REQUOTE_BPS":rq, "pf_mult":pf, "hit_rate":hit_rate, "pnl_est":net})
    df = pd.DataFrame(rows).sort_values("hour")
    out = os.path.join(snap_dir, "backtest_hourly.csv")
    df.to_csv(out, index=False)
    print("Saved", out)
    return df

if __name__=="__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap_dir", required=True)
    args = ap.parse_args()
    tune_hourly(args.snap_dir)
