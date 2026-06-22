#!/usr/bin/env python3
import time, os, re, glob
try:
    import redis
    r=redis.Redis(host='localhost', port=6379, decode_responses=True)
except Exception:
    r=None

# We treat lines containing "submit ok"/"submit success" as success; "fail|error|timeout" as failure.
OK_RE  = re.compile(r'(submit|bundle).*(ok|success)', re.I)
BAD_RE = re.compile(r'(relay|submit|bundle).*(fail|error|timeout)', re.I)

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
                        ok  = bool(OK_RE.search(ln))
                        bad = bool(BAD_RE.search(ln))
                        idx = 0
                        m=re.search(r'relay\D+(\d+)', ln, re.I)
                        if m:
                            try: idx=int(m.group(1))
                            except: idx=0
                        if ok and idx>0:
                            r.incr(f"jito:relay:succ:{idx}")
                            r.expire(f"jito:relay:succ:{idx}", 600)
                        if bad and idx>0:
                            r.incr(f"jito:relay:fail:{idx}")
                            r.expire(f"jito:relay:fail:{idx}", 600)
            except Exception:
                pass
        # compute success rate (last ~10m TTL window)
        try:
            rels = (os.environ.get("JITO_RELAYS","") or "").split(",")
            for i,_ in enumerate(rels,1):
                s = int(r.get(f"jito:relay:succ:{i}") or 0)
                f = int(r.get(f"jito:relay:fail:{i}") or 0)
                tot = max(1, s+f)
                rate = round(100.0 * s / tot, 2)
                r.set(f"jito:relay:succ_rate:{i}", rate)
                # de-prioritize: if <70%, mark as weak (used by _order_relays_env if you want)
                if rate < 70.0:
                    r.setex(f"jito:relay:weak:{i}", 180, "1")
        except Exception:
            pass
        time.sleep(5)

if __name__=='__main__':
    loop()
