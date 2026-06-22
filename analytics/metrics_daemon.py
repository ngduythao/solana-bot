#!/usr/bin/env python3
import time, os, glob, re, statistics
try:
    import redis
    r=redis.Redis(host="localhost", port=6379, decode_responses=True)
except Exception:
    r=None

LAT_RE=re.compile(r'latency_ms[=\s:]+(\d+(?:\.\d+)?)', re.I)
PNL_RE=re.compile(r'pnl[_\s]*usd[=\s:]+(-?\d+(?:\.\d+)?)', re.I)
PAIR_RE=re.compile(r'pair[=\s:]+([A-Z]+/[A-Z]+)', re.I)

def push(key,val):
    if not r: return
    try: r.set(key, str(val))
    except Exception: pass

def scan():
    files=glob.glob('logs/*.log') + glob.glob('logs/*.out') + glob.glob('logs/*')
    latencies=[]; pair_lat={} ; pnl=0.0 ; trades=0 ; wr_w=0
    for p in files:
        try:
            st=os.stat(p)
            if st.st_size>5_000_000: continue  # skip huge
            with open(p,'r',errors='ignore') as f:
                for ln in f.readlines()[-2000:]:
                    m=LAT_RE.search(ln)
                    if m:
                        val=float(m.group(1)); latencies.append(val)
                        mp=PAIR_RE.search(ln); pair=mp.group(1) if mp else None
                        if pair:
                            pair_lat.setdefault(pair, []).append(val)
                    m2=PNL_RE.search(ln)
                    if m2:
                        try: pnl = float(m2.group(1))
                        except: pass
                    if "trade" in ln.lower():
                        trades+=1
                        if "win" in ln.lower(): wr_w+=1
        except Exception:
            continue
    if latencies:
        p50=statistics.median(latencies)
        p95=sorted(latencies)[int(0.95*len(latencies))-1]
        push("hsbot:lat_p50", round(p50,2))
        push("hsbot:lat_p95", round(p95,2))
    push("hsbot:pnl:daily_usd", round(pnl,2))
    try:
        import redis
        r2=redis.Redis(host='localhost', port=6379, decode_responses=True)
        r2.lpush('series:pnl', round(pnl,2)); r2.ltrim('series:pnl', 0, 119)
    except Exception:
        pass
    push("hsbot:trades_daily", trades)
    wr = (wr_w*100.0/trades) if trades>0 else 0.0
    push("hsbot:winrate_daily", round(wr,2))
    # per-pair simplified
    for pair, arr in pair_lat.items():
        if not arr: continue
        arrs=sorted(arr)
        p50=statistics.median(arrs)
        p95=arrs[int(0.95*len(arrs))-1]
        key=pair.replace("/","_")
        push(f"hsbot:lat:{key}:p50", round(p50,2))
        push(f"hsbot:lat:{key}:p95", round(p95,2))
        try:
            import redis
            r2=redis.Redis(host='localhost', port=6379, decode_responses=True)
            r2.lpush(f'series:lat:{key}', round(p50,2)); r2.ltrim(f'series:lat:{key}', 0, 119)
        except Exception:
            pass

if __name__=="__main__":
    while True:
        scan()
        time.sleep(15)
