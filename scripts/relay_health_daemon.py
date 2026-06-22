#!/usr/bin/env python3
import time, glob, os, re
try:
    import redis
    r=redis.Redis(host='localhost', port=6379, decode_responses=True)
except Exception:
    r=None

FAIL_RE=re.compile(r'(relay|submit).*(fail|error|timeout)', re.I)

def incr(k, ttl):
    try:
        v = int(r.incr(k))
        r.expire(k, ttl)
        return v
    except Exception:
        return 0

def loop():
    seen={}
    while True:
        files = glob.glob('logs/*.log') + glob.glob('logs/*.out') + glob.glob('logs/*')
        for p in files:
            try:
                st=os.stat(p).st_mtime
                if seen.get(p,0)>=st: 
                    continue
                seen[p]=st
                with open(p,'r',errors='ignore') as f:
                    for ln in f.readlines()[-1000:]:
                        if FAIL_RE.search(ln):
                            # crude parse relay index if present like [relay=2] or relay:2
                            idx=0
                            m=re.search(r'relay\D+(\d+)', ln, re.I)
                            if m:
                                try: idx=int(m.group(1))
                                except: idx=0
                            # dynamic TTL: 60s * min(10, fail_count)
                            cnt=incr(f"jito:relay:fail:{idx}", 900)
                            ttl=min(600, 60*max(1,cnt))
                            if idx>0:
                                r.setex(f"jito:relay:black:{idx}", ttl, "1")
            except Exception:
                pass
        time.sleep(5)

if __name__=='__main__':
    loop()
