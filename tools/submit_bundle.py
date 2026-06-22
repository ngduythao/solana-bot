
#!/usr/bin/env python3
import os, sys, time, json, random, math
import urllib.request, urllib.error

# Usage: tools/submit_bundle.py '<base64_tx_or_json>'
# ENV:
#  JITO_RELAYS_CANDIDATES: comma list of relay HTTP endpoints (https://...)
#  JITO_BUNDLE_AUTH: token for Authorization
#  SEND_JITTER_MS=0-3 (randomized micro-delay)
#  SEND_BACKOFF=1.6 (exponential), SEND_RETRIES=3
#  TIMEOUT_SEC=2.5

RELAYS=[s.strip() for s in os.getenv("JITO_HTTP_RELAYS","").split(",") if s.strip()]
if not RELAYS:
    # fallback: try map from WS list
    wss=[s.strip() for s in os.getenv("JITO_RELAYS_CANDIDATES","").split(",") if s.strip()]
    RELAYS=[w.replace("wss://","https://") for w in wss]
AUTH=os.getenv("JITO_BUNDLE_AUTH","")
JITTER=float(os.getenv("SEND_JITTER_MS","1.0"))
BACKOFF=float(os.getenv("SEND_BACKOFF","1.6"))
RETRIES=int(os.getenv("SEND_RETRIES","3"))
TIMEOUT=float(os.getenv("TIMEOUT_SEC","2.5"))

payload=sys.argv[1] if len(sys.argv)>1 else None
if not payload:
    print("missing payload", file=sys.stderr); sys.exit(2)

def send(url, data):
    req=urllib.request.Request(url, data=data.encode("utf-8"), headers={
        "Content-Type":"application/json",
        "Authorization":f"Bearer {AUTH}" if AUTH else ""
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8")

def main():
    # randomized micro delay per relay
    order=list(RELAYS)
    random.shuffle(order)
    errs=[]
    for i,relay in enumerate(order):
        delay=random.random()*JITTER/1000.0
        time.sleep(delay)
        attempt=0; bdelay=0.05
        while attempt<=RETRIES:
            try:
                out=send(relay, payload)
                print(out); return 0
            except Exception as e:
                errs.append((relay,str(e)))
                time.sleep(bdelay)
                bdelay*=BACKOFF
                attempt+=1
    print(json.dumps({"error":"all_relays_failed","detail":errs}), file=sys.stderr)
    return 1

if __name__=="__main__":
    sys.exit(main())
