
import os, time, csv, json

INP="logs/executions.csv"
OUT="reports/route_pnl_top.json"
os.makedirs("reports", exist_ok=True)

def compute():
    agg={}
    if not os.path.exists(INP): return []
    with open(INP,"r") as f:
        r=csv.DictReader(f)
        for row in r:
            try:
                route = row.get("route_label") or "unknown"
                gross=float(row.get("pnl_gross","0") or 0)
                fee=float(row.get("priority_fee","0") or 0)+float(row.get("rpc_fee","0") or 0)
                tsd=float(row.get("ts_detect","0") or 0)
                tss=float(row.get("ts_submit","0") or 0)
                dur=max(0.001, tss-tsd)
                key=route
                a=agg.get(key, {"route":route,"gross":0.0,"fee":0.0,"dur":0.0,"trades":0})
                a["gross"]+=gross; a["fee"]+=fee; a["dur"]+=dur; a["trades"]+=1
                agg[key]=a
            except: pass
    rows=[]
    for k,v in agg.items():
        pnlps=(v["gross"]-v["fee"])/max(0.001,v["dur"])
        rows.append({"route":k, "pnlps":pnlps, **v})
    rows.sort(key=lambda x: x["pnlps"], reverse=True)
    return rows[:30]

def main():
    while True:
        try:
            rows=compute()
            with open(OUT,"w") as f:
                json.dump(rows, f)
        except Exception as e:
            pass
        time.sleep(5)
if __name__=="__main__":
    main()
