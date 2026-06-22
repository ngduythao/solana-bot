import os, csv, time
from datetime import datetime

AN="analytics.csv"
EX="logs/executions.csv"

def accumulate(paths):
    gross=0.0; fee=0.0; net=0.0; n=0; ok=0
    for p in paths:
        if not os.path.exists(p): continue
        with open(p,"r") as f:
            for row in csv.DictReader(f):
                g=float(row.get("pnl_gross","0") or 0)
                f1=float(row.get("priority_fee","0") or 0) + float(row.get("rpc_fee","0") or 0)
                s=row.get("status","")
                gross+=g; fee+=f1; net+=g-f1; n+=1; ok+= (1 if s=="ok" else 0)
    wr = ok/max(1,n)
    return gross, fee, net, n, wr

def write_rows(rows, path, header):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_header = not os.path.exists(path)
    with open(path,"a",newline="") as f:
        w=csv.DictWriter(f, fieldnames=header)
        if write_header: w.writeheader()
        w.writerows(rows)

def main():
    ts=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    gross, fee, net, n, wr = accumulate([AN,EX])
    # hourly
    write_rows([{"ts":ts,"gross":gross,"fee":fee,"net":net,"trades":n,"winrate":round(wr,4)}],
               "reports/pnl_hourly.csv", ["ts","gross","fee","net","trades","winrate"])
    # daily
    day=datetime.utcnow().strftime("%Y-%m-%d")
    write_rows([{"day":day,"gross":gross,"fee":fee,"net":net,"trades":n,"winrate":round(wr,4)}],
               "reports/pnl_daily.csv", ["day","gross","fee","net","trades","winrate"])
    print("Wrote reports/pnl_hourly.csv & pnl_daily.csv")

if __name__=="__main__":
    main()
