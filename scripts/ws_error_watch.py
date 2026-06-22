#!/usr/bin/env python3
import time, os, re, glob
try:
    import redis
    r=redis.Redis(host='localhost', port=6379, decode_responses=True)
except Exception:
    r=None

ERR = re.compile(r'(ws|websocket).*(error|disconnect|timeout|closed)', re.I)
OK  = re.compile(r'(ws|websocket).*(open|connected)', re.I)

def loop():
    seen={}
    while True:
        err, ok = 0, 0
        files = glob.glob('logs/*.log') + glob.glob('logs/*.out') + glob.glob('logs/*')
        for p in files:
            try:
                st=os.stat(p).st_mtime
                if seen.get(p,0)>=st: 
                    continue
                seen[p]=st
                with open(p,'r',errors='ignore') as f:
                    for ln in f.readlines()[-1000:]:
                        if ERR.search(ln): err += 1
                        elif OK.search(ln): ok += 1
            except Exception:
                pass
        tot = max(1, err+ok)
        rate = err / tot
        try:
            r.set("ws:error_rate", round(rate,3))
            if rate > 0.25:
                os.system(f"./scripts/tg_notify.sh \"⚠️ WS error spike: {rate*100:.0f}%\" >/dev/null 2>&1")
        except Exception:
            pass
        time.sleep(5)

if __name__=='__main__':
    loop()
