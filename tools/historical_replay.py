import os, json, csv, time, argparse
from services.simulator_core import clmm_swap, dlmm_swap

"""
Replay historical slot data to validate simulator & execution gates.
Expected inputs under data/history/:
 - slots.csv: rows {slot, ts, pair, leg1_depth, leg2_depth, leg3_depth, fee_bps_leg1, ..., price_leg1, ...}
 - ticks_or_bins.jsonl: per pool snapshot w/ ticks or DLMM bins for each slot.
This script will feed snapshots to the simulator via Redis or file pipes and write a report.
"""
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", default="data/history/slots.csv")
    ap.add_argument("--snapshots", default="data/history/ticks_or_bins.jsonl")
    ap.add_argument("--out", default="reports/replay_report.json")
    args = ap.parse_args()

    os.makedirs("reports", exist_ok=True)
    # If snapshots exist, attempt more accurate sim per row
    snap_idx = {}
    if os.path.exists(args.snapshots):
        try:
            with open(args.snapshots,'r') as sf:
                for line in sf:
                    j=json.loads(line)
                    slot=j.get('slot'); snap_idx[slot]=j
        except Exception:
            pass

    total=0; ok=0; fails=0
    by_cause={"slippage":0,"stale":0,"fee":0,"unknown":0}
    if not os.path.exists(args.slots):
        print("No historical slots.csv found; place data under data/history/")
        return 0
    with open(args.slots,"r") as f:
        rd = csv.DictReader(f)
        for row in rd:
            total+=1
            try:
                slot = int(row.get("slot") or 0)
                pair = row.get("pair") or "NA"
                fee = float(row.get("fee_bps_leg1","30") or 30)
                amt = float(row.get("size_in","1000") or 1000)
                snap = snap_idx.get(slot)
                used_sim = False
                if snap:
                    if snap.get("type")=="clmm":
                        s0=float(snap["sqrt_price"]); L=float(snap["liquidity"])
                        ticks=snap.get("ticks") or []
                        out,cons,sp,cr= clmm_swap(amt, s0, L, snap.get("tick_spacing",64), ticks, fee_bps=fee)
                        used_sim=True
                        if cons<=0 or out<=0: fails+=1; by_cause["slippage"]+=1
                        else: ok+=1
                    elif snap.get("type")=="dlmm":
                        bins=snap.get("bins") or []
                        out,cons,used= dlmm_swap(amt, bins, fee_bps=fee)
                        used_sim=True
                        if cons<=0 or out<=0: fails+=1; by_cause["slippage"]+=1
                        else: ok+=1
                if not used_sim:
                    depth = float(row.get("leg1_depth","0") or 0)
                    if depth>0 and fee<100: ok+=1
                    else: fails+=1; by_cause["slippage"]+=1
            except Exception:
                fails+=1; by_cause["unknown"]+=1
    import json
    rep={"total":total,"ok":ok,"fails":fails,"by_cause":by_cause,"note":"Plug your real simulator calls here"}
    with open(args.out,"w") as f: json.dump(rep,f,indent=2)
    print(json.dumps(rep,indent=2))

if __name__=="__main__":
    main()
