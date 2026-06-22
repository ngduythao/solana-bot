
import os, time, json, redis, socket

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
TARGETS=os.getenv("COLO_RTT_TARGETS","api.mainnet-beta.solana.com:443,ny.relay.example:10001,sg.relay.example:10001").split(",")
TIMEOUT=float(os.getenv("COLO_RTT_TIMEOUT","0.35"))  # seconds
INTERVAL=float(os.getenv("COLO_RTT_INTERVAL","5"))
def probe(host, port, timeout):
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    t0=time.time()
    try:
        s.connect((host, port))
        s.close()
        return (time.time()-t0)*1000.0
    except Exception:
        return None

def main():
    print("[colo_rtt] running")
    while True:
        out=[]
        for t in TARGETS:
            try:
                h,p=t.split(":"); p=int(p)
            except Exception:
                continue
            ms=probe(h,p,TIMEOUT)
            out.append({"target": t, "ms": ms, "ts": time.time()})
        r.setex("solbot:colo:rtt", 20, json.dumps(out))
        time.sleep(INTERVAL)

if __name__=="__main__":
    main()
