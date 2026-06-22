
#!/usr/bin/env python3
# Lightweight parallel-quote proxy for Jupiter v6 with fallback and DEX label logging.
# Usage: tools/quote_proxy.py 'https://quote.rpc1/?...' 'https://quote.rpc2/?...' --timeout-chain 2.0,2.6,3.0 --deny-labels "SCAM,UNKNOWNDEX"
import os, sys, time, json, threading, urllib.request, urllib.error

TIMEOUT_CHAIN=[float(x) for x in (sys.argv[3] if len(sys.argv)>3 else os.getenv("QUOTE_TIMEOUT_CHAIN","2.0,2.6,3.0")).split(",")]
DENY=[s.strip().upper() for s in os.getenv("DEX_DENY_LABELS","").split(",") if s.strip()]

urls=sys.argv[1:3]
def fetch(u, timeout):
    try:
        with urllib.request.urlopen(u, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error":str(e)}

def pick_best(responses):
    # choose first success by now; caller can compare better later
    for r in responses:
        if isinstance(r, dict) and "error" not in r:
            return r
    return responses[0]

def log_denied(routes):
    deny=[]
    for rt in routes or []:
        lbl=(rt.get("dexLabel") or "").upper()
        if lbl in DENY:
            deny.append(lbl)
    if deny:
        print(json.dumps({"deny_due_to_label":list(set(deny))}))

def main():
    for t in TIMEOUT_CHAIN:
        res=[None,None]
        threads=[]
        for i,u in enumerate(urls):
            th=threading.Thread(target=lambda idx,uu: res.__setitem__(idx, fetch(uu, t)), args=(i,u))
            th.start(); threads.append(th)
        for th in threads: th.join()
        best=pick_best(res)
        # Log deny reasons if any
        if isinstance(best, dict) and "data" in best:
            log_denied(best.get("data",[]))
        print(json.dumps(best)); return 0
    print(json.dumps({"error":"all_timeouts_exhausted"})); return 1

if __name__=="__main__":
    sys.exit(main())
