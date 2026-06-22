#!/usr/bin/env python3
import csv, os, time, re, json, glob
OUT="logs/pnl_routes.csv"

def extract_rows():
    rows=[]
    # Scan recent logs; you can adapt pattern to your engine logs
    files = glob.glob('logs/*.log')+glob.glob('logs/*.out')+glob.glob('logs/*')
    EV = re.compile(r'route=(\S+) .* pnl=([\-\d\.]+) .* latency=(\d+)', re.I)
    for p in files:
        try:
            with open(p,'r',errors='ignore') as f:
                for ln in f.readlines()[-2000:]:
                    m=EV.search(ln)
                    if m:
                        route=m.group(1)
                        pnl=float(m.group(2))
                        lat=int(m.group(3))
                        dex = route.split(':')[0] if ':' in route else 'N/A'
                        wl  = 1 if pnl>0 else 0
                        rows.append([int(time.time()), dex, route, pnl, wl, lat])
        except Exception:
            pass
    return rows

def loop():
    os.makedirs('logs', exist_ok=True)
    # header if not exists
    if not os.path.exists(OUT):
        with open(OUT,'w',newline='') as f:
            w=csv.writer(f); w.writerow(['ts','dex','route_label','pnl_usd','win_loss','latency_ms'])
    while True:
        rows = extract_rows()
        if rows:
            with open(OUT,'a',newline='') as f:
                w=csv.writer(f); w.writerows(rows)
        time.sleep(30)

if __name__=='__main__':
    loop()
